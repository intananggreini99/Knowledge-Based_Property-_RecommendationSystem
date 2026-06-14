from __future__ import annotations

import logging
import threading
from pathlib import Path
from time import sleep
from typing import List

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, SessionLocal
from .models import Property
from .schemas import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem,
    MetricsSummary,
)
from .services.preprocess import build_unified_dataset
from .services.recommender import recommend
from .services.evaluation import evaluate
from .services.db_loader import load_dataframe_to_db

logger = logging.getLogger("rumaku")

app = FastAPI(title=settings.app_name, version=settings.app_version)

if settings.cors_origins == "*":
    origins = ["*"]
else:
    origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

DATAFRAME_CACHE: pd.DataFrame | None = None

# ─── startup state ────────────────────────────────────────────────────────────
# Threading event so the health endpoint can return 200 immediately while the
# heavy init (DB wait + CSV load + seed) runs in the background.
_init_done = threading.Event()
_init_error: str | None = None          # set if background init crashed


def _clean_scalar(value):
    """Convert pandas/numpy missing values to None and numpy scalars to Python types."""
    if isinstance(value, (list, tuple, dict, set)):
        return value
    try:
        if value is None or pd.isna(value):
            return None
    except (TypeError, ValueError):
        return value
    if isinstance(value, np.generic):
        return value.item()
    return value


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _load_or_build_dataframe() -> pd.DataFrame:
    global DATAFRAME_CACHE
    if DATAFRAME_CACHE is not None:
        return DATAFRAME_CACHE

    path = settings.processed_data_path
    if path.exists():
        df = pd.read_csv(path)
    else:
        raw_dir = Path("/app/data/raw")
        raw_dir.mkdir(parents=True, exist_ok=True)
        df = build_unified_dataset(raw_dir, output_path=path)

    DATAFRAME_CACHE = df
    return df


def _wait_for_db(max_attempts: int = 30, delay_seconds: float = 3.0) -> None:
    """Retry until PostgreSQL is ready (up to ~90 s on first deploy)."""
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("DB ready after %d attempt(s)", attempt)
            return
        except OperationalError as exc:
            last_error = exc
            logger.info("DB not ready yet (attempt %d/%d) — retrying in %ss",
                        attempt, max_attempts, delay_seconds)
            sleep(delay_seconds)
    raise RuntimeError(
        f"Database not ready after {max_attempts} attempts"
    ) from last_error


def _background_init() -> None:
    """Heavy init that runs in a daemon thread.

    The app starts accepting HTTP immediately; this thread handles:
      1. Waiting for PostgreSQL to become available
      2. Creating tables
      3. Loading the CSV into memory
      4. Seeding 12 946 rows into the DB (first deploy only)
    """
    global _init_error
    try:
        logger.info("Background init started")
        _wait_for_db()
        Base.metadata.create_all(bind=engine)

        df = _load_or_build_dataframe()
        if not df.empty:
            with SessionLocal() as db:
                count = db.query(Property).count()
                if count == 0:
                    logger.info("Seeding %d rows into the DB…", len(df))
                    load_dataframe_to_db(db, df)
                    logger.info("Seeding complete")
                else:
                    logger.info("DB already has %d rows — skip seeding", count)
        logger.info("Background init complete")
    except Exception as exc:
        _init_error = str(exc)
        logger.exception("Background init failed: %s", exc)
    finally:
        _init_done.set()        # always signal done (even on error)


@app.on_event("startup")
def on_startup() -> None:
    """Kick off background init and return immediately."""
    t = threading.Thread(target=_background_init, daemon=True, name="rumaku-init")
    t.start()


# ─── routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/evaluation", response_class=HTMLResponse)
def evaluation_page():
    return (STATIC_DIR / "evaluation.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health():
    """Lightweight health endpoint — responds immediately, even during init.

    Returns 200 with status="starting" while seeding is in progress so Railway
    considers the deployment healthy and keeps retrying user requests normally.
    Returns 200 with status="ok" once fully ready.
    Returns 503 if background init crashed.
    """
    if _init_error:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": _init_error},
        )
    if not _init_done.is_set():
        return {"status": "starting", "ready": False}

    df = _load_or_build_dataframe()
    return {
        "status": "ok",
        "ready": True,
        "records": int(len(df)),
        "property_types": df["property_type"].value_counts(dropna=False).to_dict(),
        "transaction_types": df["transaction_type"].value_counts(dropna=False).to_dict(),
    }


@app.get("/api/stats")
def stats():
    df = _load_or_build_dataframe()
    return {
        "records": int(len(df)),
        "price_min": float(df["price_rp"].min()),
        "price_median": float(df["price_rp"].median()),
        "price_max": float(df["price_rp"].max()),
        "cities": sorted(
            [c for c in df["city"].dropna().astype(str).unique().tolist()]
        )[:25],
    }


@app.post("/api/recommend", response_model=RecommendationResponse)
def api_recommend(query: RecommendationRequest):
    df = _load_or_build_dataframe()
    results_df, stage = recommend(df, query)

    items: list[RecommendationItem] = []
    for _, row in results_df.iterrows():
        r = {key: _clean_scalar(val) for key, val in row.items()}
        items.append(
            RecommendationItem(
                id=int(row.name) if row.name is not None else 0,
                source_dataset=str(r.get("source_dataset")),
                property_type=str(r.get("property_type")),
                transaction_type=str(r.get("transaction_type")),
                title=r.get("title"),
                property_label=r.get("property_label"),
                transaction_label=r.get("transaction_label"),
                city=r.get("city"),
                district=r.get("district"),
                address=r.get("address"),
                price_rp=float(r.get("price_rp")),
                price_label=str(r.get("price_label")) if r.get("price_label") is not None else "",
                bedrooms=r.get("bedrooms"),
                bathrooms=r.get("bathrooms"),
                size_m2=r.get("size_m2"),
                feature_summary=r.get("feature_summary"),
                furnishing=r.get("furnishing"),
                condition=r.get("condition"),
                orientation=r.get("orientation"),
                facilities=r.get("facilities"),
                swim_pool=None if r.get("swim_pool") is None else bool(r.get("swim_pool")),
                score=float(r.get("score") or 0.0),
                matched_reasons=list(r.get("matched_reasons") or []),
            )
        )

    return RecommendationResponse(
        query=query,
        relaxation_stage=stage,
        total_candidates=int(len(results_df)),
        returned=len(items),
        results=items,
    )


@app.get("/api/evaluate", response_model=MetricsSummary)
def api_evaluate(sample_size: int = 100, top_k: int = 10):
    df = _load_or_build_dataframe()
    metrics = evaluate(df, sample_size=sample_size, top_k=top_k)
    return MetricsSummary(**metrics)


@app.post("/api/reload")
def reload_dataset():
    global DATAFRAME_CACHE
    DATAFRAME_CACHE = None
    df = _load_or_build_dataframe()
    with SessionLocal() as db:
        db.query(Property).delete()
        db.commit()
        load_dataframe_to_db(db, df)
    return {"status": "reloaded", "records": int(len(df))}
