from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    property_type: Optional[Literal["rumah", "apartemen"]] = None
    transaction_type: Optional[Literal["jual", "sewa"]] = None
    budget_max: Optional[float] = Field(default=None, ge=0)
    city: Optional[str] = None
    district: Optional[str] = None
    bedrooms_min: Optional[int] = Field(default=None, ge=0)
    bathrooms_min: Optional[int] = Field(default=None, ge=0)
    furnishing: Optional[str] = None
    swim_pool: Optional[bool] = None
    max_watt_min: Optional[float] = Field(default=None, ge=0)
    size_min: Optional[float] = Field(default=None, ge=0)
    top_k: int = Field(default=10, ge=1, le=50)
    explain: bool = True


class RecommendationItem(BaseModel):
    id: int
    source_dataset: str
    property_type: str
    transaction_type: str
    title: Optional[str] = None
    property_label: Optional[str] = None
    transaction_label: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    price_rp: float
    price_label: str
    bedrooms: Optional[float] = None
    bathrooms: Optional[float] = None
    size_m2: Optional[float] = None
    feature_summary: Optional[str] = None
    furnishing: Optional[str] = None
    condition: Optional[str] = None
    orientation: Optional[str] = None
    facilities: Optional[str] = None
    swim_pool: Optional[bool] = None
    score: float
    matched_reasons: List[str]


class RecommendationResponse(BaseModel):
    query: RecommendationRequest
    relaxation_stage: str
    total_candidates: int
    returned: int
    results: List[RecommendationItem]


class MetricsSummary(BaseModel):
    sample_size: int
    top_k: int
    ndcg: float
    precision: float
    recall: float
    f1_score: float
    constraint_satisfaction_rate: float
    valid_recommendation_rate: float
