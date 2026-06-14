from __future__ import annotations

from pathlib import Path
from time import sleep
from typing import List

import numpy as np
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, SessionLocal
from .models import Property
from .schemas import RecommendationRequest, RecommendationResponse, RecommendationItem, MetricsSummary
from .services.preprocess import build_unified_dataset
from .services.recommender import recommend
from .services.evaluation import evaluate
from .services.db_loader import load_dataframe_to_db

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


def _clean_scalar(value):
    """Convert pandas/numpy missing values to ``None`` and numpy scalars to
    native Python types.

    CSV reads turn empty cells into float ``NaN``. Passing those straight into
    Pydantic ``Optional[str]`` fields raises a validation error (a float is not
    a string), which is why house listings — whose ``title``/``orientation``/…
    are empty — used to make ``/api/recommend`` return HTTP 500.
    """
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


def _wait_for_db(max_attempts: int = 20, delay_seconds: float = 2.0) -> None:
    last_error = None
    for _ in range(max_attempts):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError as exc:
            last_error = exc
            sleep(delay_seconds)
    raise RuntimeError(f"Database not ready after {max_attempts} attempts") from last_error


@app.on_event("startup")
def on_startup():
    _wait_for_db()
    Base.metadata.create_all(bind=engine)

    df = _load_or_build_dataframe()
    if df.empty:
        return

    with SessionLocal() as db:
        count = db.query(Property).count()
        if count == 0:
            load_dataframe_to_db(db, df)


@app.get("/", response_class=HTMLResponse)
def index():
    index_path = STATIC_DIR / "index.html"
    return index_path.read_text(encoding="utf-8")


@app.get("/evaluation", response_class=HTMLResponse)
def evaluation_page():
    eval_path = STATIC_DIR / "evaluation.html"
    return eval_path.read_text(encoding="utf-8")


@app.get("/api/health")
def health():
    df = _load_or_build_dataframe()
    return {
        "status": "ok",
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
        "cities": sorted([c for c in df["city"].dropna().astype(str).unique().tolist()])[:25],
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
