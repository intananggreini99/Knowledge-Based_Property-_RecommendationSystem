from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _normalize_db_url(url: str) -> str:
    """Make a Postgres URL compatible with SQLAlchemy + psycopg2.

    Managed hosts such as Railway, Render, and Heroku hand out the URL in the
    form ``postgresql://user:pass@host:port/db`` (or the legacy ``postgres://``).
    SQLAlchemy needs the driver to be explicit, i.e.
    ``postgresql+psycopg2://...``. We rewrite the scheme here so the same code
    works locally (docker-compose) and on Railway without manual editing.
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: _normalize_db_url(
            os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg2://proprec:proprec123@localhost:5432/proprec",
            )
        )
    )
    processed_data_path: Path = field(
        default_factory=lambda: Path(
            os.getenv(
                "PROCESSED_DATA_PATH",
                "./data/processed/properties_merged_cleaned.csv",
            )
        )
    )
    cors_origins: str = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*"))
    app_name: str = "Sistem Rekomendasi Properti"
    app_version: str = "1.0.0"


settings = Settings()
