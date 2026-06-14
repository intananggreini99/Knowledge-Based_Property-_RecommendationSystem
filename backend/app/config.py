from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:

    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./local.db"
    )

    processed_data_path: Path = Path(
        os.getenv(
            "PROCESSED_DATA_PATH",
            str(
                BASE_DIR
                / "data"
                / "processed"
                / "properties_merged_cleaned.csv"
            )
        )
    )

    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "*"
    )

    app_name: str = "Sistem Rekomendasi Properti"

    app_version: str = "1.0.0"


settings = Settings()