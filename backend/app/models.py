from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from .database import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    source_dataset = Column(String(100), index=True, nullable=False)
    property_type = Column(String(20), index=True, nullable=False)
    transaction_type = Column(String(20), index=True, nullable=False)

    title = Column(Text, nullable=True)
    city = Column(String(120), index=True, nullable=True)
    district = Column(String(120), index=True, nullable=True)
    address = Column(Text, nullable=True)
    raw_location = Column(Text, nullable=True)
    kecamatan = Column(String(120), nullable=True)

    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)

    price_rp = Column(Float, index=True, nullable=False)
    bedrooms = Column(Float, nullable=True)
    bathrooms = Column(Float, nullable=True)
    size_m2 = Column(Float, nullable=True)
    land_size_m2 = Column(Float, nullable=True)
    building_size_m2 = Column(Float, nullable=True)

    carports = Column(Float, nullable=True)
    garages = Column(Float, nullable=True)
    floors = Column(Float, nullable=True)
    certificate = Column(Text, nullable=True)
    electricity_va = Column(Float, nullable=True)
    furnishing = Column(String(40), nullable=True)
    condition = Column(String(40), nullable=True)
    orientation = Column(String(40), nullable=True)
    facilities = Column(Text, nullable=True)

    max_capacity = Column(Float, nullable=True)
    max_watt = Column(Float, nullable=True)
    swim_pool = Column(Boolean, nullable=True)
    road_width = Column(Text, nullable=True)
    water_source = Column(Text, nullable=True)
    hook = Column(Boolean, nullable=True)
    internet = Column(Boolean, nullable=True)

    description = Column(Text, nullable=True)
    url = Column(Text, nullable=True)

    price_per_m2 = Column(Float, nullable=True)
    search_text = Column(Text, nullable=True)
    property_label = Column(String(50), nullable=True)
    transaction_label = Column(String(50), nullable=True)
    price_label = Column(String(50), nullable=True)
    feature_summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
