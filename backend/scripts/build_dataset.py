from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the ``app`` package is importable no matter how this script is launched.
# Running ``python scripts/build_dataset.py`` puts only the scripts/ directory on
# sys.path, so ``import app`` fails. Add whichever parent actually contains the
# ``app`` package (the container's /app, or repo-root/backend for local runs).
_HERE = Path(__file__).resolve().parent
for _candidate in (_HERE.parent, _HERE.parent / "backend"):
    if (_candidate / "app").is_dir() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

from app.services.preprocess import build_unified_dataset


def main():
    parser = argparse.ArgumentParser(description="Build unified real-estate dataset")
    parser.add_argument("--raw-dir", type=Path, default=Path("./data/raw"))
    parser.add_argument("--output", type=Path, default=Path("./data/processed/properties_merged_cleaned.csv"))
    args = parser.parse_args()

    df = build_unified_dataset(args.raw_dir, args.output)
    print(f"Saved {len(df):,} rows to {args.output}")


if __name__ == "__main__":
    main()
