from __future__ import annotations

from pathlib import Path
from typing import Iterable
import re
import numpy as np
import pandas as pd


def clean_text(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text if text else None


def parse_price(value):
    if pd.isna(value):
        return np.nan
    s = str(value).lower().strip().replace("rp", "").replace("idr", "").replace(" ", "")
    if not s or s in {"nan", "none", "-"}:
        return np.nan
    mult = 1.0
    if "miliar" in s:
        s = s.replace("miliar", "")
        mult = 1e9
    elif "juta" in s:
        s = s.replace("juta", "")
        mult = 1e6
    elif "jt" in s:
        s = s.replace("jt", "")
        mult = 1e6
    s = s.split("-")[0]
    s = s.replace(".", "").replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    return float(m.group(1)) * mult if m else np.nan


def to_float(value):
    if pd.isna(value):
        return np.nan
    try:
        return float(str(value).strip().replace(",", "."))
    except Exception:
        return np.nan


def yes_no(value):
    if pd.isna(value):
        return np.nan
    s = str(value).strip().lower()
    if s in {"ya", "yes", "true", "1", "ada"}:
        return True
    if s in {"tidak", "no", "false", "0", "-1"}:
        return False
    try:
        return bool(int(float(s)))
    except Exception:
        return np.nan


def normalize_furnishing(value):
    if pd.isna(value):
        return None
    s = str(value).strip().lower()
    if s in {"full furnished", "fully furnished", "furnished"}:
        return "furnished"
    if s == "unfurnished":
        return "unfurnished"
    if s in {"semi furnished", "semi-furnished"}:
        return "semi furnished"
    return "unknown"


def split_location(value):
    if pd.isna(value):
        return None, None
    text = clean_text(value)
    if not text:
        return None, None
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) >= 2:
        return parts[0], parts[-1]
    return parts[0], None


def house_facilities(row):
    items = []
    for col in ["Ruang Makan", "Ruang Tamu", "Terjangkau Internet", "Sumber Air", "Hook", "Lebar Jalan"]:
        val = row.get(col)
        if pd.notna(val) and str(val).strip():
            items.append(f"{col}:{clean_text(val)}")
    return "; ".join(items) if items else None


def _first_valid(series):
    for value in series:
        if pd.notna(value) and value not in {"", "nan", None}:
            return value
    return np.nan


def _load_apartment_files(paths: Iterable[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            frames.append({
                "source_dataset": path.name,
                "property_type": "apartemen",
                "transaction_type": "sewa",
                "title": clean_text(row.get("Name")),
                "city": "Jakarta",
                "district": clean_text(row.get("kecamatan")) if "kecamatan" in df.columns else None,
                "address": clean_text(row.get("Address")),
                "raw_location": clean_text(row.get("location")) if "location" in df.columns else clean_text(row.get("Address")),
                "kecamatan": clean_text(row.get("kecamatan")) if "kecamatan" in df.columns else None,
                "lat": row.get("lat") if "lat" in df.columns else np.nan,
                "lon": row.get("lon") if "lon" in df.columns else np.nan,
                "price_rp": row.get("Price"),
                "bedrooms": row.get("Total Bedroom"),
                "bathrooms": row.get("Total Bathroom") if "Total Bathroom" in df.columns else np.nan,
                "size_m2": row.get("Apart Size"),
                "land_size_m2": np.nan,
                "building_size_m2": row.get("Apart Size"),
                "carports": np.nan,
                "garages": np.nan,
                "floors": np.nan,
                "certificate": None,
                "electricity_va": row.get("Max Watt"),
                "furnishing": normalize_furnishing(row.get("Furnish Type")),
                "condition": None,
                "orientation": None,
                "facilities": "swim_pool" if yes_no(row.get("Swim Pool")) else None,
                "max_capacity": row.get("Max Capacity") if "Max Capacity" in df.columns else np.nan,
                "max_watt": row.get("Max Watt"),
                "swim_pool": yes_no(row.get("Swim Pool")),
                "road_width": np.nan,
                "water_source": np.nan,
                "hook": np.nan,
                "internet": np.nan,
                "description": None,
                "url": None,
            })
    ap = pd.DataFrame(frames)
    if ap.empty:
        return ap

    ap = ap.groupby(["title", "address"], dropna=False).agg(_first_valid).reset_index()
    return ap


def build_unified_dataset(raw_dir: Path, output_path: Path | None = None) -> pd.DataFrame:
    raw_dir = Path(raw_dir)
    sources = {
        "jabodetabek_house.csv": "rumah",
        "Combined_Datalist_v1.1.csv": "rumah",
        "yogyakarta_house.csv": "rumah",
        "travelio2.csv": "apartemen",
        "travelio3.csv": "apartemen",
        "travelio4.csv": "apartemen",
        "travelio5.csv": "apartemen",
    }

    frames = []

    # houses: jabodetabek
    jabo_path = raw_dir / "jabodetabek_house.csv"
    if jabo_path.exists():
        df = pd.read_csv(jabo_path)
        for _, row in df.iterrows():
            frames.append({
                "source_dataset": "jabodetabek_house",
                "property_type": "rumah",
                "transaction_type": "jual",
                "title": None,
                "city": clean_text(row.get("city")) or "Jabodetabek",
                "district": clean_text(row.get("district")),
                "address": clean_text(row.get("district")),
                "raw_location": clean_text(row.get("city")) or "Jabodetabek",
                "kecamatan": clean_text(row.get("district")),
                "lat": row.get("lat"),
                "lon": row.get("long"),
                "price_rp": row.get("price_in_rp"),
                "bedrooms": row.get("bedrooms"),
                "bathrooms": row.get("bathrooms"),
                "size_m2": row.get("building_size_m2"),
                "land_size_m2": row.get("land_size_m2"),
                "building_size_m2": row.get("building_size_m2"),
                "carports": row.get("carports"),
                "garages": row.get("garages"),
                "floors": row.get("floors"),
                "certificate": clean_text(row.get("certificate")),
                "electricity_va": row.get("electricity"),
                "furnishing": normalize_furnishing(row.get("furnishing")),
                "condition": clean_text(row.get("property_condition")),
                "orientation": clean_text(row.get("building_orientation")),
                "facilities": clean_text(row.get("facilities")),
                "max_capacity": np.nan,
                "max_watt": np.nan,
                "swim_pool": np.nan,
                "road_width": np.nan,
                "water_source": np.nan,
                "hook": np.nan,
                "internet": np.nan,
                "description": None,
                "url": None,
            })

    # houses: combined semicolon file
    combined_path = raw_dir / "Combined_Datalist_v1.1.csv"
    if combined_path.exists():
        df = pd.read_csv(combined_path, sep=";", encoding="utf-8-sig")
        for _, row in df.iterrows():
            frames.append({
                "source_dataset": "combined_datalist_v1.1",
                "property_type": "rumah",
                "transaction_type": "jual",
                "title": None,
                "city": "Surabaya",
                "district": clean_text(row.get("Kecamatan")),
                "address": clean_text(row.get("Kecamatan")),
                "raw_location": clean_text(row.get("Kecamatan")),
                "kecamatan": clean_text(row.get("Kecamatan")),
                "lat": np.nan,
                "lon": np.nan,
                "price_rp": parse_price(row.get(" Price ")),
                "bedrooms": to_float(row.get("Kamar Tidur")),
                "bathrooms": to_float(row.get("Kamar Mandi")),
                "size_m2": to_float(row.get("Luas Bangunan")),
                "land_size_m2": to_float(row.get("Luas Tanah")),
                "building_size_m2": to_float(row.get("Luas Bangunan")),
                "carports": np.nan,
                "garages": np.nan,
                "floors": to_float(row.get("Jumlah Lantai")),
                "certificate": clean_text(row.get("Sertifikat")),
                "electricity_va": to_float(row.get("Daya Listrik")),
                "furnishing": normalize_furnishing(row.get("Kondisi Perabotan")),
                "condition": clean_text(row.get("Kondisi Properti")),
                "orientation": clean_text(row.get("Hadap")),
                "facilities": house_facilities(row),
                "max_capacity": np.nan,
                "max_watt": np.nan,
                "swim_pool": np.nan,
                "road_width": clean_text(row.get("Lebar Jalan")),
                "water_source": clean_text(row.get("Sumber Air")),
                "hook": yes_no(row.get("Hook")),
                "internet": yes_no(row.get("Terjangkau Internet")),
                "description": None,
                "url": None,
            })

    # houses: yogyakarta
    jogja_path = raw_dir / "yogyakarta_house.csv"
    if jogja_path.exists():
        df = pd.read_csv(jogja_path)
        for _, row in df.iterrows():
            district, city = split_location(row.get("listing-location"))
            frames.append({
                "source_dataset": "yogyakarta_house",
                "property_type": "rumah",
                "transaction_type": "jual",
                "title": clean_text(row.get("description")),
                "city": city or "Yogyakarta",
                "district": district,
                "address": clean_text(row.get("listing-location")),
                "raw_location": clean_text(row.get("listing-location")),
                "kecamatan": district,
                "lat": np.nan,
                "lon": np.nan,
                "price_rp": parse_price(row.get("price")),
                "bedrooms": row.get("bed"),
                "bathrooms": row.get("bath"),
                "size_m2": to_float(row.get("building_area")),
                "land_size_m2": to_float(row.get("surface_area")),
                "building_size_m2": to_float(row.get("building_area")),
                "carports": row.get("carport"),
                "garages": np.nan,
                "floors": np.nan,
                "certificate": None,
                "electricity_va": np.nan,
                "furnishing": None,
                "condition": None,
                "orientation": None,
                "facilities": None,
                "max_capacity": np.nan,
                "max_watt": np.nan,
                "swim_pool": np.nan,
                "road_width": np.nan,
                "water_source": np.nan,
                "hook": np.nan,
                "internet": np.nan,
                "description": clean_text(row.get("description")),
                "url": clean_text(row.get("nav-link")),
            })

    # apartments
    apt_paths = [raw_dir / n for n in ["travelio2.csv", "travelio3.csv", "travelio4.csv", "travelio5.csv"] if (raw_dir / n).exists()]
    if apt_paths:
        ap = _load_apartment_files(apt_paths)
        # align missing columns if groupby reduced
        for col in [
            "source_dataset","property_type","transaction_type","title","city","district","address","raw_location","kecamatan",
            "lat","lon","price_rp","bedrooms","bathrooms","size_m2","land_size_m2","building_size_m2","carports","garages",
            "floors","certificate","electricity_va","furnishing","condition","orientation","facilities","max_capacity",
            "max_watt","swim_pool","road_width","water_source","hook","internet","description","url"
        ]:
            if col not in ap.columns:
                ap[col] = np.nan
        frames.extend(ap.to_dict("records"))

    df = pd.DataFrame(frames)
    if df.empty:
        return df

    # Numeric cleanup
    for col in ["price_rp", "bedrooms", "bathrooms", "size_m2", "land_size_m2", "building_size_m2", "carports", "garages", "floors", "electricity_va", "max_capacity", "max_watt", "lat", "lon"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # remove impossible values
    df = df[df["price_rp"].notna() & (df["price_rp"] > 0)]
    df = df[(df["bedrooms"].fillna(0) >= 0) & (df["bedrooms"].fillna(0) <= 20)]
    df = df[(df["bathrooms"].fillna(0) >= 0) & (df["bathrooms"].fillna(0) <= 20)]
    df = df[(df["size_m2"].fillna(0) >= 5) & (df["size_m2"].fillna(0) <= 5000)]

    # percentile outlier removal per transaction type
    cleaned = []
    for (_, _), g in df.groupby(["property_type", "transaction_type"], dropna=False):
        if len(g) < 50:
            cleaned.append(g)
            continue
        p_lo, p_hi = g["price_rp"].quantile([0.01, 0.99])
        s_lo, s_hi = g["size_m2"].quantile([0.01, 0.99])
        g = g[g["price_rp"].between(p_lo, p_hi)]
        g = g[g["size_m2"].between(s_lo, s_hi)]
        cleaned.append(g)
    df = pd.concat(cleaned, ignore_index=True)

    df["property_label"] = df["property_type"].map({"rumah": "Rumah", "apartemen": "Apartemen"})
    df["transaction_label"] = df["transaction_type"].map({"jual": "Jual Beli", "sewa": "Sewa"})
    df["price_label"] = df["price_rp"].map(lambda x: f"Rp {x:,.0f}".replace(",", "."))
    df["area_label"] = df["size_m2"].map(lambda x: None if pd.isna(x) else f"{int(round(x))} m²")
    df["feature_summary"] = df.apply(
        lambda r: " | ".join([x for x in [
            f"{int(r['bedrooms']) if pd.notna(r['bedrooms']) else '?'} KT",
            f"{int(r['bathrooms']) if pd.notna(r['bathrooms']) else '?'} KM",
            f"{int(r['size_m2']) if pd.notna(r['size_m2']) else '?'} m²",
            clean_text(r["furnishing"]).title() if pd.notna(r["furnishing"]) and clean_text(r["furnishing"]) else None,
        ] if x]),
        axis=1,
    )
    df["location_text"] = df[["city", "district", "address", "raw_location"]].fillna("").agg(" ".join, axis=1).str.replace(r"\s+", " ", regex=True).str.strip().str.lower()
    df["search_text"] = df[["title", "city", "district", "address", "facilities", "certificate", "condition", "orientation", "furnishing"]].fillna("").agg(" ".join, axis=1).str.replace(r"\s+", " ", regex=True).str.strip().str.lower()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

    return df
