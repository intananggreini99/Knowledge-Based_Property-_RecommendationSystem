from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
import math
import re
import numpy as np
import pandas as pd

from ..schemas import RecommendationRequest


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return {t for t in text.split() if len(t) > 1}


def normalize_text(value: str | None) -> str:
    return (str(value).strip().lower() if value else "").strip()


def format_price(value: float) -> str:
    return f"Rp {value:,.0f}".replace(",", ".")


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
        return max(0.0, value / target)
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
    # sewa: same logic but stronger penalty when above budget
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
        reasons.append(f"Masuk budget ({format_price(row['price_rp'])} ≤ {format_price(query.budget_max)})" if row["price_rp"] <= query.budget_max else f"Sedikit di atas budget ({format_price(row['price_rp'])})")

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

    # penalize missing key info lightly
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
    # relaxation strategy
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
        else:
            cand = cand

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

    # Fallback: no candidate after all relaxations
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
