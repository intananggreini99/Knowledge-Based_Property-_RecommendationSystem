
from __future__ import annotations

from pathlib import Path
from io import BytesIO
import html

import pandas as pd
import streamlit as st

from recommender_utils import (
    RecommendationRequest,
    load_dataset,
    recommend,
    evaluate,
    format_price,
    export_results_csv,
    normalize_text,
)

APP_TITLE = "Rumaku — Rekomendasi Properti Cerdas"
DATA_PATH = Path(__file__).parent / "data" / "processed" / "properties_merged_cleaned.csv"


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stApp {
        background: linear-gradient(180deg, #f7f4ef 0%, #fbfaf7 100%);
      }
      header[data-testid="stHeader"] {
        background: rgba(247,244,239,0.85);
      }
      .hero {
        padding: 1.2rem 1.4rem;
        border: 1px solid rgba(20,86,76,0.12);
        border-radius: 1.5rem;
        background: linear-gradient(135deg, rgba(20,86,76,0.08), rgba(184,137,59,0.06));
        margin-bottom: 1rem;
      }
      .hero h1 {
        margin: 0;
        color: #0f4339;
      }
      .hero p {
        margin: 0.35rem 0 0;
        color: #49605a;
      }
      .metric-box {
        border: 1px solid rgba(20,86,76,0.12);
        border-radius: 1.1rem;
        background: white;
        padding: 0.9rem 1rem;
        box-shadow: 0 12px 30px -26px rgba(27,42,38,0.45);
      }
      .result-card {
        border: 1px solid rgba(20,86,76,0.10);
        border-radius: 1.25rem;
        background: white;
        padding: 1rem 1.05rem;
        box-shadow: 0 16px 40px -30px rgba(27,42,38,0.30);
        margin-bottom: 0.85rem;
      }
      .badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        border: 1px solid rgba(20,86,76,0.16);
        background: rgba(228,237,233,0.55);
        font-size: 0.76rem;
        margin-right: 0.35rem;
        margin-bottom: 0.25rem;
      }
      .score-pill {
        display: inline-block;
        padding: 0.25rem 0.55rem;
        border-radius: 999px;
        background: #14564c;
        color: white;
        font-size: 0.78rem;
        font-weight: 700;
      }
      .muted {
        color: #6b7c76;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(show_spinner=False)
def get_data():
    return load_dataset(DATA_PATH)

df = get_data()

# --- top hero ---
st.markdown(
    f"""
    <div class="hero">
      <h1>Rumaku — Rekomendasi Properti Cerdas</h1>
      <p>Pencocokan berbasis pengetahuan untuk rumah dan apartemen dengan hard filtering, soft ranking, dan relaxation bertahap.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.markdown(f'<div class="metric-box"><div class="muted">Total data</div><div style="font-size:1.6rem;font-weight:800">{len(df):,}</div></div>', unsafe_allow_html=True)
with col_b:
    st.markdown(f'<div class="metric-box"><div class="muted">Kota / area</div><div style="font-size:1.6rem;font-weight:800">{df["city"].nunique(dropna=True):,}</div></div>', unsafe_allow_html=True)
with col_c:
    st.markdown(f'<div class="metric-box"><div class="muted">Tipe properti</div><div style="font-size:1.6rem;font-weight:800">{df["property_type"].nunique(dropna=True):,}</div></div>', unsafe_allow_html=True)
with col_d:
    st.markdown(f'<div class="metric-box"><div class="muted">Sumber dataset</div><div style="font-size:1.6rem;font-weight:800">{df["source_dataset"].nunique(dropna=True):,}</div></div>', unsafe_allow_html=True)

st.write("")

tab1, tab2 = st.tabs(["Rekomendasi", "Evaluasi Model"])

with tab1:
    with st.sidebar:
        st.header("Preferensi Pencarian")
        property_type_label = st.selectbox("Tipe properti", ["Semua", "Rumah", "Apartemen"], index=0)
        transaction_label = st.selectbox("Transaksi", ["Semua", "Jual", "Sewa"], index=0)

        budget = st.number_input("Budget maksimum (Rp)", min_value=0.0, value=0.0, step=1_000_000.0, format="%.0f")
        budget_value = budget if budget > 0 else None

        city_options = ["Semua"] + sorted([c for c in df["city"].dropna().astype(str).unique().tolist()])
        city = st.selectbox("Kota", city_options, index=0)
        district = st.text_input("Kecamatan / area", placeholder="Contoh: Menteng, Setiabudi, Cibubur")

        bedrooms = st.number_input("Minimum kamar tidur", min_value=0, value=0, step=1)
        bathrooms = st.number_input("Minimum kamar mandi", min_value=0, value=0, step=1)

        furnishing = st.selectbox("Furnishing", ["Semua", "furnished", "semi furnished", "unfurnished"], index=0)
        pool = st.selectbox("Kolam renang", ["Semua", "Ya", "Tidak"], index=0)
        max_watt = st.number_input("Minimum daya listrik (VA)", min_value=0.0, value=0.0, step=100.0, format="%.0f")
        size_min = st.number_input("Minimum luas (m²)", min_value=0.0, value=0.0, step=1.0, format="%.0f")
        top_k = st.slider("Jumlah hasil", min_value=3, max_value=20, value=8, step=1)

        search = st.button("Cari rekomendasi", use_container_width=True)

    st.subheader("Pencarian properti")
    st.caption("Gunakan filter di sidebar, lalu jalankan pencarian untuk melihat hasil dengan skor kecocokan.")

    if search:
        query = RecommendationRequest(
            property_type={"Rumah": "rumah", "Apartemen": "apartemen"}.get(property_type_label),
            transaction_type={"Jual": "jual", "Sewa": "sewa"}.get(transaction_label),
            budget_max=budget_value,
            city=None if city == "Semua" else city,
            district=district.strip() or None,
            bedrooms_min=int(bedrooms) if bedrooms > 0 else None,
            bathrooms_min=int(bathrooms) if bathrooms > 0 else None,
            furnishing=None if furnishing == "Semua" else furnishing,
            swim_pool=None if pool == "Semua" else (pool == "Ya"),
            max_watt_min=max_watt if max_watt > 0 else None,
            size_min=size_min if size_min > 0 else None,
            top_k=int(top_k),
            explain=True,
        )

        with st.spinner("Menjalankan filtering dan ranking..."):
            results_df, stage = recommend(df, query)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-box"><div class="muted">Relaxation stage</div><div style="font-size:1.25rem;font-weight:800">{stage}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-box"><div class="muted">Kandidat tampil</div><div style="font-size:1.25rem;font-weight:800">{len(results_df):,}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-box"><div class="muted">Budget</div><div style="font-size:1.25rem;font-weight:800">{format_price(budget_value) if budget_value else "Tidak dibatasi"}</div></div>', unsafe_allow_html=True)

        if results_df.empty:
            st.warning("Tidak ada hasil yang cocok dengan filter saat ini.")
        else:
            st.download_button(
                "Unduh hasil sebagai CSV",
                data=export_results_csv(results_df),
                file_name="hasil_rekomendasi_properti.csv",
                mime="text/csv",
                use_container_width=True,
            )

            for _, row in results_df.iterrows():
                title_raw = row.get("title") or f"{row.get('property_label') or row.get('property_type')} — {row.get('transaction_label') or row.get('transaction_type')}"
                title = html.escape(str(title_raw))
                loc_raw = " • ".join([x for x in [row.get("city"), row.get("district"), row.get("address")] if x and str(x).strip()])
                loc = html.escape(str(loc_raw))
                cols = st.columns([0.8, 0.2])
                with cols[0]:
                    st.markdown(
                        f"""
                        <div class="result-card">
                          <div style="display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;">
                            <div>
                              <div class="badge">{html.escape(str(row.get('property_label') or row.get('property_type') or '-'))}</div>
                              <div class="badge">{html.escape(str(row.get('transaction_label') or row.get('transaction_type') or '-'))}</div>
                              <h3 style="margin:0.4rem 0 0.25rem;font-size:1.15rem;">{title}</h3>
                              <div class="muted" style="font-size:0.92rem;">{loc or '-'}</div>
                            </div>
                            <div class="score-pill">{float(row.get('score') or 0):.2f}</div>
                          </div>

                          <div style="margin-top:0.8rem;font-size:1.1rem;font-weight:800;color:#14564c;">
                            {row.get('price_label') or format_price(row.get('price_rp'))}
                          </div>
                          <div class="muted" style="margin-top:0.15rem;">
                            {row.get('feature_summary') or '-'}
                          </div>
                          <div style="margin-top:0.7rem;">
                            <span class="badge">Sumber: {html.escape(str(row.get('source_dataset') or '-'))}</span>
                            <span class="badge">Furnishing: {html.escape(str(row.get('furnishing') or '-'))}</span>
                            <span class="badge">KT: {row.get('bedrooms') if pd.notna(row.get('bedrooms')) else '-'}</span>
                            <span class="badge">KM: {row.get('bathrooms') if pd.notna(row.get('bathrooms')) else '-'}</span>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    reasons = row.get("matched_reasons") or []
                    if reasons:
                        st.caption("Alasan cocok: " + " | ".join(reasons))
                with cols[1]:
                    st.write("")
    else:
        st.info("Atur preferensi di sidebar, lalu klik **Cari rekomendasi**.")

with tab2:
    st.subheader("Evaluasi model")
    st.caption("Tab ini menjalankan evaluasi sampel dari dataset untuk melihat kualitas ranking secara ringkas.")
    sample_size = st.slider("Ukuran sampel evaluasi", min_value=10, max_value=min(300, len(df)), value=50, step=10)
    top_k_eval = st.slider("Top-k evaluasi", min_value=3, max_value=20, value=10, step=1)
    run_eval = st.button("Jalankan evaluasi", use_container_width=True)

    if run_eval:
        with st.spinner("Menghitung metrik..."):
            metrics = evaluate(df, sample_size=sample_size, top_k=top_k_eval)
        m1, m2, m3 = st.columns(3)
        m1.metric("NDCG", f"{metrics['ndcg']:.3f}")
        m2.metric("Precision", f"{metrics['precision']:.3f}")
        m3.metric("Recall", f"{metrics['recall']:.3f}")
        m4, m5, m6 = st.columns(3)
        m4.metric("F1-score", f"{metrics['f1_score']:.3f}")
        m5.metric("CSR", f"{metrics['constraint_satisfaction_rate']:.3f}")
        m6.metric("Valid recommendation rate", f"{metrics['valid_recommendation_rate']:.3f}")

        st.json(metrics)
    else:
        st.write("Klik tombol evaluasi untuk melihat metrik model.")
