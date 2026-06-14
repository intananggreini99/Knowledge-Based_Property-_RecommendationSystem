from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://proprec:proprec123@localhost:5432/proprec")
    processed_data_path: Path = Path(os.getenv("PROCESSED_DATA_PATH", "./data/processed/properties_merged_cleaned.csv"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    app_name: str = "Sistem Rekomendasi Properti"
    app_version: str = "1.0.0"


settings = Settings()
