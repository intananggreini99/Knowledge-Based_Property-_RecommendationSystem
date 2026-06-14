from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from ..models import Property


def _clean(value):
    """Normalize a single DataFrame value for insertion.

    ``DataFrame.fillna(pd.NA)`` previously left float ``NaN`` in numeric columns
    and could surface ``pd.NA`` in object columns; psycopg2 cannot adapt either,
    so loading the dataset could crash at startup (or silently store the literal
    text ``"NaN"``). This turns every missing value into ``None`` and every numpy
    scalar into a native Python type the driver understands.
    """
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, np.generic):
        return value.item()
    return value


def load_dataframe_to_db(session: Session, df: pd.DataFrame) -> int:
    session.query(Property).delete()
    session.commit()

    records = df.to_dict(orient="records")
    objects = []
    for raw in records:
        row = {key: _clean(val) for key, val in raw.items()}
        obj = Property(
            source_dataset=row.get("source_dataset"),
            property_type=row.get("property_type"),
            transaction_type=row.get("transaction_type"),
            title=row.get("title"),
            city=row.get("city"),
            district=row.get("district"),
            address=row.get("address"),
            raw_location=row.get("raw_location"),
            kecamatan=row.get("kecamatan"),
            lat=row.get("lat"),
            lon=row.get("lon"),
            price_rp=row.get("price_rp"),
            bedrooms=row.get("bedrooms"),
            bathrooms=row.get("bathrooms"),
            size_m2=row.get("size_m2"),
            land_size_m2=row.get("land_size_m2"),
            building_size_m2=row.get("building_size_m2"),
            carports=row.get("carports"),
            garages=row.get("garages"),
            floors=row.get("floors"),
            certificate=row.get("certificate"),
            electricity_va=row.get("electricity_va"),
            furnishing=row.get("furnishing"),
            condition=row.get("condition"),
            orientation=row.get("orientation"),
            facilities=row.get("facilities"),
            max_capacity=row.get("max_capacity"),
            max_watt=row.get("max_watt"),
            swim_pool=None if row.get("swim_pool") is None else bool(row.get("swim_pool")),
            road_width=row.get("road_width"),
            water_source=row.get("water_source"),
            hook=None if row.get("hook") is None else bool(row.get("hook")),
            internet=None if row.get("internet") is None else bool(row.get("internet")),
            description=row.get("description"),
            url=row.get("url"),
            price_per_m2=row.get("price_per_m2"),
            search_text=row.get("search_text"),
            property_label=row.get("property_label"),
            transaction_label=row.get("transaction_label"),
            price_label=row.get("price_label"),
            feature_summary=row.get("feature_summary"),
        )
        objects.append(obj)

    session.bulk_save_objects(objects)
    session.commit()
    return len(objects)
