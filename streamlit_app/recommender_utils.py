
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Iterable
import math
import re

import numpy as np
import pandas as pd


@dataclass
class RecommendationRequest:
    property_type: Optional[str] = None  # "rumah" | "apartemen"
    transaction_type: Optional[str] = None  # "jual" | "sewa"
    budget_max: Optional[float] = None
    city: Optional[str] = None
    district: Optional[str] = None
    bedrooms_min: Optional[int] = None
    bathrooms_min: Optional[int] = None
    furnishing: Optional[str] = None
    swim_pool: Optional[bool] = None
    max_watt_min: Optional[float] = None
    size_min: Optional[float] = None
    top_k: int = 8
    explain: bool = True


def normalize_text(value: str | None) -> str:
    return (str(value).strip().lower() if value is not None else "").strip()


def format_price(value: float | int | None) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "-"
    try:
        return f"Rp {float(value):,.0f}".replace(",", ".")
    except Exception:
        return "-"


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return {t for t in text.split() if len(t) > 1}


def _to_bool(value):
    if pd.isna(value):
        return np.nan
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in {"true", "1", "yes", "ya", "ada"}:
        return True
    if s in {"false", "0", "no", "tidak", "none", "nan", "-"}:
        return False
    try:
        return bool(int(float(s)))
    except Exception:
        return np.nan


def _clean_scalar(value):
    if pd.isna(value):
        return None
    if isinstance(value, (np.generic,)):
        return value.item()
    return value


def load_dataset(csv_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    # Ensure core fields are in friendly types.
    if "swim_pool" in df.columns:
        df["swim_pool"] = df["swim_pool"].map(_to_bool)
    for col in ["hook", "internet"]:
        if col in df.columns:
            df[col] = df[col].map(_to_bool)

    num_cols = [
        "price_rp", "bedrooms", "bathrooms", "size_m2", "land_size_m2",
        "building_size_m2", "carports", "garages", "floors", "electricity_va",
        "max_capacity", "max_watt", "price_per_m2", "lat", "lon", "road_width",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fallback labels for safer rendering.
    if "location_text" not in df.columns:
        parts = []
        for col in ["city", "district", "address", "raw_location", "kecamatan"]:
            if col in df.columns:
                parts.append(df[col].fillna("").astype(str))
        if parts:
            df["location_text"] = parts[0]
            for part in parts[1:]:
                df["location_text"] = df["location_text"] + " " + part
        else:
            df["location_text"] = ""

    if "search_text" not in df.columns:
        df["search_text"] = df["location_text"].fillna("")

    for col in ["property_type", "transaction_type", "title", "city", "district", "address",
                "raw_location", "kecamatan", "furnishing", "condition", "orientation",
                "facilities", "description", "url", "property_label", "transaction_label",
                "price_label", "area_label", "feature_summary", "location_text", "search_text"]:
        if col in df.columns:
            df[col] = df[col].where(pd.notna(df[col]), None)

    return df


def location_score(row: pd.Series, query_city: str | None, query_district: str | None) -> float:
    score = 0.0
    if query_city:
        city = normalize_text(query_city)
        if city and city in normalize_text(row.get("city")):
            score += 0.7
        elif city and city in normalize_text(row.get("location_text")):
            score += 0.45

    if query_district:
        district = normalize_text(query_district)
        hay = " ".join([
            normalize_text(row.get("district")),
            normalize_text(row.get("kecamatan")),
            normalize_text(row.get("address")),
            normalize_text(row.get("raw_location")),
            normalize_text(row.get("location_text")),
        ])
        if district and district in hay:
            score += 0.7
        else:
            q_tokens = _tokens(query_district)
            r_tokens = _tokens(hay)
            if q_tokens and r_tokens:
                overlap = len(q_tokens & r_tokens) / max(len(q_tokens), 1)
                score += 0.55 * overlap
    return min(score, 1.0)


def furnishing_score(row: pd.Series, pref: str | None) -> float:
    if not pref:
        return 0.5
    pref = normalize_text(pref)
    furn = normalize_text(row.get("furnishing"))
    if pref == furn:
        return 1.0
    if pref in furn or furn in pref:
        return 0.8
    return 0.0


def bool_score(row_value, pref: bool | None) -> float:
    if pref is None:
        return 0.5
    if pd.isna(row_value):
        return 0.5
    return 1.0 if bool(row_value) == bool(pref) else 0.0


def numeric_closeness(value: float | None, target: float | None, direction: str = "min") -> float:
    if target is None or pd.isna(target):
        return 0.5
    if value is None or pd.isna(value):
        return 0.3
    value = float(value)
    target = float(target)

    if direction == "min":
        if value >= target:
            return 1.0
        return max(0.0, value / target) if target else 0.0
    if direction == "max":
        if value <= target:
            return 1.0
        return max(0.0, target / value) if value else 0.0
    if target == 0:
        return 1.0 if value == 0 else 0.0
    ratio = abs(value - target) / abs(target)
    return max(0.0, 1.0 - min(ratio, 1.0))


def price_score(row: pd.Series, budget: float | None) -> float:
    if budget is None or pd.isna(budget):
        return 0.5
    price = row.get("price_rp")
    if pd.isna(price):
        return 0.2
    price = float(price)
    budget = float(budget)
    if row.get("transaction_type") == "jual":
        if price <= budget:
            return 1.0 - max(0.0, (budget - price) / max(budget, 1.0)) * 0.2
        return max(0.0, 1.0 - (price - budget) / max(budget, 1.0))
    if price <= budget:
        return 1.0 - max(0.0, (budget - price) / max(budget, 1.0)) * 0.1
    return max(0.0, 1.0 - (price - budget) / max(budget, 1.0) * 1.5)


def size_score(row: pd.Series, size_min: float | None) -> float:
    return numeric_closeness(row.get("size_m2"), size_min, direction="min")


def score_property(row: pd.Series, query: RecommendationRequest) -> tuple[float, list[str]]:
    scores = []
    reasons = []

    s_price = price_score(row, query.budget_max)
    scores.append((s_price, 0.30))
    if query.budget_max is not None and not pd.isna(row.get("price_rp")):
        reasons.append(
            f"Masuk budget ({format_price(row['price_rp'])} ≤ {format_price(query.budget_max)})"
            if row["price_rp"] <= query.budget_max
            else f"Sedikit di atas budget ({format_price(row['price_rp'])})"
        )

    s_loc = location_score(row, query.city, query.district)
    scores.append((s_loc, 0.25))
    if query.city or query.district:
        reasons.append("Lokasi cocok" if s_loc >= 0.7 else "Lokasi cukup dekat")

    s_bed = numeric_closeness(row.get("bedrooms"), query.bedrooms_min, direction="min")
    scores.append((s_bed, 0.15))
    if query.bedrooms_min is not None:
        reasons.append("Jumlah kamar cocok" if s_bed >= 1.0 else "Kamar mendekati kebutuhan")

    s_bath = numeric_closeness(row.get("bathrooms"), query.bathrooms_min, direction="min")
    scores.append((s_bath, 0.10))
    if query.bathrooms_min is not None:
        reasons.append("Kamar mandi cocok" if s_bath >= 1.0 else "Kamar mandi mendekati kebutuhan")

    s_furn = furnishing_score(row, query.furnishing)
    scores.append((s_furn, 0.08))
    if query.furnishing:
        reasons.append("Furnishing cocok" if s_furn >= 1.0 else "Furnishing mendekati")

    s_pool = bool_score(row.get("swim_pool"), query.swim_pool)
    scores.append((s_pool, 0.05))
    if query.swim_pool is not None:
        reasons.append("Fasilitas kolam sesuai" if s_pool >= 1.0 else "Preferensi kolam dipertimbangkan")

    s_watt = numeric_closeness(row.get("max_watt"), query.max_watt_min, direction="min")
    scores.append((s_watt, 0.04))
    if query.max_watt_min is not None:
        reasons.append("Daya listrik sesuai" if s_watt >= 1.0 else "Daya listrik mendekati")

    s_size = size_score(row, query.size_min)
    scores.append((s_size, 0.03))
    if query.size_min is not None:
        reasons.append("Luas cocok" if s_size >= 1.0 else "Luas mendekati")

    total_weight = sum(w for _, w in scores)
    final_score = sum(s * w for s, w in scores) / total_weight if total_weight else 0.0
    if pd.isna(row.get("price_rp")):
        final_score *= 0.9

    uniq_reasons = []
    for reason in reasons:
        if reason not in uniq_reasons:
            uniq_reasons.append(reason)
    return round(float(final_score), 4), uniq_reasons[:4]


def apply_hard_constraints(df: pd.DataFrame, query: RecommendationRequest, relaxation_level: int = 0) -> pd.DataFrame:
    cand = df.copy()

    if query.property_type:
        cand = cand[cand["property_type"] == query.property_type]
    if query.transaction_type:
        cand = cand[cand["transaction_type"] == query.transaction_type]

    budget = query.budget_max
    if budget is not None:
        if relaxation_level == 0:
            cand = cand[cand["price_rp"] <= budget]
        elif relaxation_level == 1:
            cand = cand[cand["price_rp"] <= budget * 1.10]
        elif relaxation_level == 2:
            cand = cand[cand["price_rp"] <= budget * 1.25]
        else:
            cand = cand[cand["price_rp"] <= budget * 1.50]

    if query.city:
        q = normalize_text(query.city)
        if relaxation_level < 2:
            cand = cand[cand["location_text"].fillna("").str.contains(re.escape(q), case=False, na=False)]
        else:
            city_tokens = _tokens(q)
            cand = cand[cand["location_text"].fillna("").apply(lambda x: bool(city_tokens & _tokens(x)))]

    if query.district:
        q = normalize_text(query.district)
        if relaxation_level < 1:
            cand = cand[cand["location_text"].fillna("").str.contains(re.escape(q), case=False, na=False)]
        else:
            district_tokens = _tokens(q)
            cand = cand[cand["location_text"].fillna("").apply(lambda x: bool(district_tokens & _tokens(x)))]

    if query.bedrooms_min is not None:
        min_bed = query.bedrooms_min if relaxation_level < 2 else max(0, query.bedrooms_min - 1)
        cand = cand[(cand["bedrooms"].isna()) | (cand["bedrooms"] >= min_bed)]

    if query.bathrooms_min is not None:
        min_bath = query.bathrooms_min if relaxation_level < 2 else max(0, query.bathrooms_min - 1)
        cand = cand[(cand["bathrooms"].isna()) | (cand["bathrooms"] >= min_bath)]

    if query.furnishing:
        pref = normalize_text(query.furnishing)
        if relaxation_level < 2:
            cand = cand[cand["furnishing"].fillna("").str.contains(re.escape(pref), case=False, na=False)]

    if query.swim_pool is not None and relaxation_level < 3:
        cand = cand[(cand["swim_pool"].isna()) | (cand["swim_pool"] == query.swim_pool)]

    if query.max_watt_min is not None and relaxation_level < 3:
        cand = cand[(cand["max_watt"].isna()) | (cand["max_watt"] >= query.max_watt_min)]

    if query.size_min is not None and relaxation_level < 2:
        cand = cand[(cand["size_m2"].isna()) | (cand["size_m2"] >= query.size_min)]

    return cand


def recommend(df: pd.DataFrame, query: RecommendationRequest) -> tuple[pd.DataFrame, str]:
    stages = ["strict", "relaxed_budget", "broadened_location", "relaxed_all"]
    for level, name in enumerate(stages):
        cand = apply_hard_constraints(df, query, relaxation_level=level)
        if not cand.empty:
            ranked = cand.copy()
            scored = ranked.apply(lambda row: score_property(row, query), axis=1, result_type="expand")
            ranked["score"] = scored[0]
            ranked["matched_reasons"] = scored[1]
            ranked = ranked.sort_values(["score", "price_rp"], ascending=[False, True]).head(query.top_k)
            return ranked, name
    return df.head(0).copy(), "no_match"


def is_relevant_row(row: pd.Series, query: RecommendationRequest) -> bool:
    if query.property_type and row.get("property_type") != query.property_type:
        return False
    if query.transaction_type and row.get("transaction_type") != query.transaction_type:
        return False
    if query.budget_max is not None and pd.notna(row.get("price_rp")) and row.get("price_rp") > query.budget_max:
        return False
    if query.city and query.city.lower() not in normalize_text(row.get("location_text")):
        return False
    if query.district and query.district.lower() not in normalize_text(row.get("location_text")):
        return False
    if query.bedrooms_min is not None and pd.notna(row.get("bedrooms")) and row.get("bedrooms") < query.bedrooms_min:
        return False
    if query.bathrooms_min is not None and pd.notna(row.get("bathrooms")) and row.get("bathrooms") < query.bathrooms_min:
        return False
    if query.furnishing and query.furnishing.lower() not in normalize_text(row.get("furnishing")):
        return False
    if query.swim_pool is not None and pd.notna(row.get("swim_pool")) and bool(row.get("swim_pool")) != bool(query.swim_pool):
        return False
    return True


def generate_query(row: pd.Series) -> RecommendationRequest:
    budget = float(row["price_rp"])
    if row["transaction_type"] == "jual":
        budget = budget * np.random.uniform(0.90, 1.10)
    else:
        budget = budget * np.random.uniform(0.95, 1.15)

    def _opt_str(value):
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        text = str(value).strip()
        return text or None

    return RecommendationRequest(
        property_type=row.get("property_type"),
        transaction_type=row.get("transaction_type"),
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


def dcg(relevances: list[float]) -> float:
    return float(sum((rel / np.log2(idx + 2)) for idx, rel in enumerate(relevances)))


def ndcg_at_k(pred_rels: list[float], ideal_rels: list[float]) -> float:
    ideal_dcg = dcg(sorted(ideal_rels, reverse=True))
    if ideal_dcg == 0:
        return 0.0
    return dcg(pred_rels) / ideal_dcg


def evaluate(df: pd.DataFrame, sample_size: int = 100, top_k: int = 10, random_state: int = 42) -> dict:
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


def export_results_csv(results_df: pd.DataFrame) -> bytes:
    cols = [
        "source_dataset", "property_type", "transaction_type", "title", "city", "district",
        "address", "price_rp", "price_label", "bedrooms", "bathrooms", "size_m2",
        "furnishing", "swim_pool", "feature_summary", "score", "matched_reasons",
    ]
    present = [c for c in cols if c in results_df.columns]
    return results_df[present].copy().to_csv(index=False).encode("utf-8")
