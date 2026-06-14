// Offline "demo" mode: a real subset of the dataset plus a client-side ranking
// that mirrors the backend's strategy (hard constraint filtering -> soft scoring
// -> staged relaxation). This keeps the deployed site fully interactive on
// Vercel even when the Railway backend is unreachable.

import { rupiah, clamp01 } from '@/lib/format';

// ---- real data subset used for demo recommendations ----
export const SAMPLE = [{"source_dataset":"travelio2.csv","property_type":"apartemen","transaction_type":"sewa","title":"1 BR Apartment @ Casa Grande Residence Near Kota Kasablanka By Travelio","city":"Jakarta","district":"Menteng","price_rp":9999999,"price_label":"Rp 9.999.999","bedrooms":0,"bathrooms":1,"size_m2":55,"furnishing":"furnished","feature_summary":"0 KT | 1 KM | 55 m² | Furnished","swim_pool":true,"max_watt":1,"property_label":"Apartemen","transaction_label":"Sewa"},{"source_dataset":"travelio2.csv","property_type":"apartemen","transaction_type":"sewa","title":"1 BR City View at Sudirman Park Apartment By Travelio","city":"Jakarta","district":"Tanah Abang","price_rp":6143903,"price_label":"Rp 6.143.903","bedrooms":1,"bathrooms":1,"size_m2":42,"furnishing":"furnished","feature_summary":"1 KT | 1 KM | 42 m² | Furnished","swim_pool":true,"max_watt":3000,"property_label":"Apartemen","transaction_label":"Sewa"},{"source_dataset":"travelio2.csv","property_type":"apartemen","transaction_type":"sewa","title":"1 Bedroom Comfort Apartment The Mansion Kemayoran By Travelio","city":"Jakarta","district":"Tj. Priok","price_rp":3999999,"price_label":"Rp 3.999.999","bedrooms":1,"bathrooms":1,"size_m2":35,"furnishing":"furnished","feature_summary":"1 KT | 1 KM | 35 m² | Furnished","swim_pool":true,"max_watt":5500,"property_label":"Apartemen","transaction_label":"Sewa"},{"source_dataset":"travelio2.csv","property_type":"apartemen","transaction_type":"sewa","title":"1BR Apartment at Cosmo Mansion near Grand Indonesia By Travelio","city":"Jakarta","district":"Tanah Abang","price_rp":5750464,"price_label":"Rp 5.750.464","bedrooms":1,"bathrooms":1,"size_m2":37,"furnishing":"furnished","feature_summary":"1 KT | 1 KM | 37 m² | Furnished","swim_pool":true,"max_watt":1300,"property_label":"Apartemen","transaction_label":"Sewa"},{"source_dataset":"travelio2.csv","property_type":"apartemen","transaction_type":"sewa","title":"1BR Apartment for 3 Pax at Signature Park Grande By Travelio","city":"Jakarta","district":"Kramat Jati","price_rp":4982382,"price_label":"Rp 4.982.382","bedrooms":1,"bathrooms":1,"size_m2":37,"furnishing":"furnished","feature_summary":"1 KT | 1 KM | 37 m² | Furnished","swim_pool":true,"max_watt":2200,"property_label":"Apartemen","transaction_label":"Sewa"},{"source_dataset":"combined_datalist_v1.1","property_type":"rumah","transaction_type":"jual","title":null,"city":"Surabaya","district":"wonokromo","price_rp":600000000,"price_label":"Rp 600.000.000","bedrooms":3,"bathrooms":2,"size_m2":70,"furnishing":"unfurnished","feature_summary":"3 KT | 2 KM | 70 m² | Unfurnished","swim_pool":null,"max_watt":null,"property_label":"Rumah","transaction_label":"Jual Beli"},{"source_dataset":"combined_datalist_v1.1","property_type":"rumah","transaction_type":"jual","title":null,"city":"Surabaya","district":"semampir","price_rp":600000000,"price_label":"Rp 600.000.000","bedrooms":3,"bathrooms":3,"size_m2":85,"furnishing":"unfurnished","feature_summary":"3 KT | 3 KM | 85 m² | Unfurnished","swim_pool":null,"max_watt":null,"property_label":"Rumah","transaction_label":"Jual Beli"},{"source_dataset":"combined_datalist_v1.1","property_type":"rumah","transaction_type":"jual","title":null,"city":"Surabaya","district":"pakal","price_rp":600000000,"price_label":"Rp 600.000.000","bedrooms":2,"bathrooms":1,"size_m2":91,"furnishing":"unfurnished","feature_summary":"2 KT | 1 KM | 91 m² | Unfurnished","swim_pool":null,"max_watt":null,"property_label":"Rumah","transaction_label":"Jual Beli"},{"source_dataset":"jabodetabek_house","property_type":"rumah","transaction_type":"jual","title":null,"city":"Jakarta Barat","district":"Jelambar","price_rp":1850000000,"price_label":"Rp 1.850.000.000","bedrooms":3,"bathrooms":3,"size_m2":189,"furnishing":null,"feature_summary":"3 KT | 3 KM | 189 m²","swim_pool":null,"max_watt":null,"property_label":"Rumah","transaction_label":"Jual Beli"},{"source_dataset":"jabodetabek_house","property_type":"rumah","transaction_type":"jual","title":null,"city":"Jakarta Barat","district":"Jelambar","price_rp":6800000000,"price_label":"Rp 6.800.000.000","bedrooms":4,"bathrooms":3,"size_m2":387,"furnishing":null,"feature_summary":"4 KT | 3 KM | 387 m²","swim_pool":null,"max_watt":null,"property_label":"Rumah","transaction_label":"Jual Beli"},{"source_dataset":"jabodetabek_house","property_type":"rumah","transaction_type":"jual","title":null,"city":"Bekasi","district":"Summarecon Bekasi","price_rp":2990000000,"price_label":"Rp 2.990.000.000","bedrooms":4,"bathrooms":4,"size_m2":272,"furnishing":"unfurnished","feature_summary":"4 KT | 4 KM | 272 m² | Unfurnished","swim_pool":null,"max_watt":null,"property_label":"Rumah","transaction_label":"Jual Beli"},{"source_dataset":"jabodetabek_house","property_type":"rumah","transaction_type":"jual","title":null,"city":"Bekasi","district":"Summarecon Bekasi","price_rp":1270000000,"price_label":"Rp 1.270.000.000","bedrooms":3,"bathrooms":2,"size_m2":69,"furnishing":null,"feature_summary":"3 KT | 2 KM | 69 m²","swim_pool":null,"max_watt":null,"property_label":"Rumah","transaction_label":"Jual Beli"},{"source_dataset":"jabodetabek_house","property_type":"rumah","transaction_type":"jual","title":null,"city":"Bekasi","district":"Summarecon Bekasi","price_rp":1950000000,"price_label":"Rp 1.950.000.000","bedrooms":3,"bathrooms":3,"size_m2":131,"furnishing":"unfurnished","feature_summary":"3 KT | 3 KM | 131 m² | Unfurnished","swim_pool":null,"max_watt":null,"property_label":"Rumah","transaction_label":"Jual Beli"},{"source_dataset":"jabodetabek_house","property_type":"rumah","transaction_type":"jual","title":null,"city":"Bekasi","district":"Summarecon Bekasi","price_rp":3300000000,"price_label":"Rp 3.300.000.000","bedrooms":3,"bathrooms":3,"size_m2":174,"furnishing":"unfurnished","feature_summary":"3 KT | 3 KM | 174 m² | Unfurnished","swim_pool":null,"max_watt":null,"property_label":"Rumah","transaction_label":"Jual Beli"}];

// stage -> human label (shared with the API response shape)
export const STAGE_LABEL = {
  strict: 'Semua syarat terpenuhi',
  relaxed_budget: 'Budget dilonggarkan sedikit',
  broadened_location: 'Cakupan lokasi diperluas',
  relaxed_all: 'Beberapa syarat dilonggarkan',
  none: 'Tidak ada kandidat',
};

// ---- client-side ranking (mirror of the backend strategy) ----
export function demoRecommend(q) {
  const norm = (s) => String(s ?? '').toLowerCase().trim();
  const cityMatch = (row) =>
    !q.city ||
    norm(row.city).includes(norm(q.city)) ||
    norm(q.city).includes(norm(row.city));

  function passHard(row, level) {
    if (q.property_type && row.property_type !== q.property_type) return false;
    if (q.transaction_type && row.transaction_type !== q.transaction_type) return false;
    if (q.budget_max != null) {
      const tol = level >= 1 ? 1.15 : 1.0;
      if (row.price_rp > q.budget_max * tol) return false;
    }
    if (q.city && level < 2 && !cityMatch(row)) return false;
    const bedReq =
      q.bedrooms_min != null ? (level >= 2 ? Math.max(0, q.bedrooms_min - 1) : q.bedrooms_min) : null;
    if (bedReq != null && (row.bedrooms ?? 0) < bedReq) return false;
    const bathReq =
      q.bathrooms_min != null ? (level >= 2 ? Math.max(0, q.bathrooms_min - 1) : q.bathrooms_min) : null;
    if (bathReq != null && (row.bathrooms ?? 0) < bathReq) return false;
    if (q.size_min != null && level < 2 && (row.size_m2 ?? 0) < q.size_min) return false;
    if (q.swim_pool != null && level < 3 && Boolean(row.swim_pool) !== q.swim_pool) return false;
    return true;
  }

  function scoreRow(row) {
    let score = 0;
    const reasons = [];
    if (q.budget_max != null && row.price_rp != null) {
      const ratio = row.price_rp / q.budget_max;
      const s =
        ratio <= 1
          ? 0.6 + 0.4 * (1 - Math.min(1, Math.abs(1 - ratio)))
          : Math.max(0, 1 - (ratio - 1) * 2);
      score += s * 0.34;
      reasons.push(
        row.price_rp <= q.budget_max ? `Masuk budget (${rupiah(row.price_rp)})` : 'Sedikit di atas budget'
      );
    } else {
      score += 0.2;
    }
    if (q.city) {
      const ok = cityMatch(row);
      score += (ok ? 1 : 0.3) * 0.2;
      if (ok) reasons.push('Lokasi cocok');
    } else {
      score += 0.12;
    }
    if (q.bedrooms_min != null) {
      const ok = (row.bedrooms ?? 0) >= q.bedrooms_min;
      score += (ok ? 1 : 0.4) * 0.16;
      reasons.push(ok ? 'Jumlah kamar cocok' : 'Kamar mendekati kebutuhan');
    } else {
      score += 0.1;
    }
    if (q.bathrooms_min != null) {
      const ok = (row.bathrooms ?? 0) >= q.bathrooms_min;
      score += (ok ? 1 : 0.4) * 0.08;
      if (ok) reasons.push('Kamar mandi cocok');
    }
    if (q.furnishing) {
      const ok = norm(row.furnishing) === norm(q.furnishing);
      score += (ok ? 1 : 0.3) * 0.1;
      if (ok) reasons.push('Furnishing cocok');
    } else {
      score += 0.06;
    }
    if (q.size_min != null && row.size_m2 != null) {
      const ok = row.size_m2 >= q.size_min;
      score += (ok ? 1 : 0.5) * 0.08;
      if (ok) reasons.push('Luas cocok');
    }
    if (q.swim_pool === true && row.swim_pool) {
      score += 0.04;
      reasons.push('Ada kolam renang');
    }
    return { score: Math.min(1, score), reasons: reasons.slice(0, 4) };
  }

  const stages = ['strict', 'relaxed_budget', 'broadened_location', 'relaxed_all'];
  for (let level = 0; level < stages.length; level++) {
    const cand = SAMPLE.filter((r) => passHard(r, level));
    if (cand.length) {
      const scored = cand
        .map((r) => {
          const s = scoreRow(r);
          return { ...r, score: s.score, matched_reasons: s.reasons };
        })
        .sort((a, b) => b.score - a.score)
        .slice(0, q.top_k);
      return {
        relaxation_stage: stages[level],
        total_candidates: cand.length,
        returned: scored.length,
        results: scored,
      };
    }
  }
  return { relaxation_stage: 'none', total_candidates: 0, returned: 0, results: [] };
}

// ---- evaluation metric definitions (display order) ----
// primary: true -> gold accent (NDCG is the headline metric)
export const METRICS = [
  { key: 'ndcg', label: 'NDCG', primary: true, blurb: 'Mutu urutan: relevan di posisi teratas dihargai lebih.' },
  { key: 'precision', label: 'Precision', blurb: 'Proporsi hasil tampil yang memang relevan.' },
  { key: 'recall', label: 'Recall', blurb: 'Proporsi properti relevan yang berhasil ditangkap.' },
  { key: 'f1_score', label: 'F1 Score', blurb: 'Penyeimbang Precision dan Recall dalam satu angka.' },
  { key: 'constraint_satisfaction_rate', label: 'Constraint Satisfaction', blurb: 'Hasil yang patuh pada syarat wajib query.' },
  { key: 'valid_recommendation_rate', label: 'Valid Recommendation', blurb: 'Query yang menghasilkan minimal satu hasil valid.' },
];

// ---- illustrative metrics for demo mode (clearly labelled, not real results) ----
export function demoMetrics(sampleSize, topK) {
  const kEff = clamp01((topK - 1) / 19); // 0..1 for top_k 1..20
  const base = {
    ndcg: 0.78 + 0.06 * kEff,
    precision: 0.81 - 0.1 * kEff,
    recall: 0.55 + 0.2 * kEff,
    constraint_satisfaction_rate: 0.93,
    valid_recommendation_rate: 0.97,
  };
  const jitter = ((sampleSize / 20) % 5) * 0.004;
  base.ndcg = clamp01(base.ndcg + jitter);
  base.precision = clamp01(base.precision + jitter * 0.5);
  base.recall = clamp01(base.recall - jitter * 0.5);
  const p = base.precision;
  const r = base.recall;
  base.f1_score = p + r ? clamp01((2 * p * r) / (p + r)) : 0;
  return {
    sample_size: sampleSize,
    top_k: topK,
    ndcg: base.ndcg,
    precision: base.precision,
    recall: base.recall,
    f1_score: base.f1_score,
    constraint_satisfaction_rate: base.constraint_satisfaction_rate,
    valid_recommendation_rate: base.valid_recommendation_rate,
  };
}
