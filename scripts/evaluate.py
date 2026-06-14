from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd

# Ensure the ``app`` package is importable no matter how this script is launched.
_HERE = Path(__file__).resolve().parent
for _candidate in (_HERE.parent, _HERE.parent / "backend"):
    if (_candidate / "app").is_dir() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))

from app.services.evaluation import evaluate


def main():
    parser = argparse.ArgumentParser(description="Evaluate knowledge-based recommender")
    parser.add_argument("--data", type=Path, default=Path("./data/processed/properties_merged_cleaned.csv"))
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    metrics = evaluate(df, sample_size=args.sample_size, top_k=args.top_k)
    for k, v in metrics.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
