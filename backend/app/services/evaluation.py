from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import numpy as np
import pandas as pd

from ..schemas import RecommendationRequest
from .recommender import recommend, is_relevant_row


def dcg(relevances: list[float]) -> float:
    return float(sum((rel / np.log2(idx + 2)) for idx, rel in enumerate(relevances)))


def _opt_str(value) -> str | None:
    """Return a clean string or ``None``.

    Sampled rows often have missing ``city``/``district``/``furnishing`` (stored
    as float ``NaN``). Feeding ``NaN`` into ``RecommendationRequest`` (whose
    fields are ``Optional[str]``) raised a validation error and broke
    ``/api/evaluate``.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def ndcg_at_k(pred_rels: list[float], ideal_rels: list[float]) -> float:
    ideal_dcg = dcg(sorted(ideal_rels, reverse=True))
    if ideal_dcg == 0:
        return 0.0
    return dcg(pred_rels) / ideal_dcg


def generate_query(row: pd.Series) -> RecommendationRequest:
    budget = float(row["price_rp"])
    if row["transaction_type"] == "jual":
        budget = budget * np.random.uniform(0.90, 1.10)
    else:
        budget = budget * np.random.uniform(0.95, 1.15)

    # add slight variations so ranking must infer
    return RecommendationRequest(
        property_type=row["property_type"],
        transaction_type=row["transaction_type"],
        budget_max=float(budget),
        city=_opt_str(row.get("city")),
        district=_opt_str(row.get("district")),
        bedrooms_min=int(row["bedrooms"]) if pd.notna(row.get("bedrooms")) else None,
        bathrooms_min=int(row["bathrooms"]) if pd.notna(row.get("bathrooms")) else None,
        furnishing=_opt_str(row.get("furnishing")),
        swim_pool=bool(row["swim_pool"]) if pd.notna(row.get("swim_pool")) else None,
        max_watt_min=float(row["max_watt"]) if pd.notna(row.get("max_watt")) else None,
        size_min=float(row["size_m2"]) if pd.notna(row.get("size_m2")) else None,
        top_k=10,
        explain=False,
    )


def evaluate(df: pd.DataFrame, sample_size: int = 100, top_k: int = 10, random_state: int = 42) -> dict:
    rng = np.random.default_rng(random_state)
    sample = df.sample(n=min(sample_size, len(df)), random_state=random_state)

    precision_list = []
    recall_list = []
    f1_list = []
    ndcg_list = []
    csr_list = []
    valid_rate_list = []

    for _, row in sample.iterrows():
        query = generate_query(row)
        query.top_k = top_k

        relevant_mask = df.apply(lambda r: is_relevant_row(r, query), axis=1)
        relevant_df = df[relevant_mask]
        results, _ = recommend(df, query)

        if results.empty:
            precision_list.append(0.0)
            recall_list.append(0.0)
            f1_list.append(0.0)
            ndcg_list.append(0.0)
            csr_list.append(0.0)
            valid_rate_list.append(0.0)
            continue

        hits = results.apply(lambda r: is_relevant_row(r, query), axis=1).astype(int).tolist()
        precision = sum(hits) / len(results)
        recall = sum(hits) / max(len(relevant_df), 1)

        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)

        pred_rels = hits
        ideal_rels = [1] * min(len(relevant_df), top_k)
        ndcg = ndcg_at_k(pred_rels, ideal_rels)

        csr = precision
        valid_rate = precision

        precision_list.append(precision)
        recall_list.append(recall)
        f1_list.append(f1)
        ndcg_list.append(ndcg)
        csr_list.append(csr)
        valid_rate_list.append(valid_rate)

    return {
        "sample_size": int(min(sample_size, len(df))),
        "top_k": int(top_k),
        "ndcg": float(np.mean(ndcg_list) if ndcg_list else 0.0),
        "precision": float(np.mean(precision_list) if precision_list else 0.0),
        "recall": float(np.mean(recall_list) if recall_list else 0.0),
        "f1_score": float(np.mean(f1_list) if f1_list else 0.0),
        "constraint_satisfaction_rate": float(np.mean(csr_list) if csr_list else 0.0),
        "valid_recommendation_rate": float(np.mean(valid_rate_list) if valid_rate_list else 0.0),
    }
