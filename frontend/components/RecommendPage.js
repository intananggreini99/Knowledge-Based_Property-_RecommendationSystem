'use client';

import { useRef, useState } from 'react';
import { useApiMode } from '@/components/ApiModeProvider';
import MatchRing from '@/components/MatchRing';
import { rupiah } from '@/lib/format';
import { SAMPLE, STAGE_LABEL, demoRecommend } from '@/lib/demo';
import { fetchRecommendations } from '@/lib/api';

const INITIAL_FORM = {
  property_type: '',
  transaction_type: '',
  budget_max: '',
  city: '',
  district: '',
  bedrooms_min: '',
  bathrooms_min: '',
  size_min: '',
  max_watt_min: '',
  furnishing: '',
  swim_pool: '',
  top_k: 8,
};

const DEFAULT_META = 'Isi preferensi di sebelah kiri, lalu tekan "Cari rekomendasi".';

function buildQuery(f) {
  const num = (v) => (v === '' || v == null ? null : Number(v));
  return {
    property_type: f.property_type || null,
    transaction_type: f.transaction_type || null,
    budget_max: num(f.budget_max),
    city: (f.city || '').trim() || null,
    district: (f.district || '').trim() || null,
    bedrooms_min: num(f.bedrooms_min),
    bathrooms_min: num(f.bathrooms_min),
    furnishing: f.furnishing || null,
    swim_pool: f.swim_pool === '' ? null : f.swim_pool === 'true',
    max_watt_min: num(f.max_watt_min),
    size_min: num(f.size_min),
    top_k: Number(f.top_k || 8),
    explain: true,
  };
}

function PropertyCard({ item, index }) {
  const typeLabel = item.property_label || (item.property_type === 'rumah' ? 'Rumah' : 'Apartemen');
  const txnLabel = item.transaction_label || (item.transaction_type === 'jual' ? 'Jual Beli' : 'Sewa');
  const title = item.title || `${typeLabel} ${item.district ? 'di ' + item.district : ''}`.trim();
  const loc = [item.city, item.district].filter(Boolean).join(' · ');
  const specs =
    item.feature_summary ||
    [
      item.bedrooms != null ? item.bedrooms + ' KT' : null,
      item.bathrooms != null ? item.bathrooms + ' KM' : null,
      item.size_m2 != null ? item.size_m2 + ' m²' : null,
    ]
      .filter(Boolean)
      .join(' | ');
  const reasons = item.matched_reasons || [];

  return (
    <article
      className="reveal rounded-4xl border border-line bg-surface p-5 shadow-card transition hover:shadow-lift sm:p-6"
      style={{ animationDelay: index * 0.04 + 's' }}
    >
      <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap gap-2">
            <span className="chip border-brand/20 bg-brand/5 text-brand">{typeLabel}</span>
            <span className="chip">{txnLabel}</span>
            {item.source_dataset ? <span className="chip text-muted">{item.source_dataset}</span> : null}
          </div>
          <h3 className="mt-3 truncate font-display text-xl font-600 leading-snug">{title}</h3>
          <p className="mt-1 text-sm text-muted">{loc || '-'}</p>
          <p className="mt-3 font-mono text-2xl font-700 text-brand">{item.price_label || rupiah(item.price_rp)}</p>
          <p className="mt-1 text-sm text-muted">
            {specs}
            {item.furnishing ? ' · ' + item.furnishing : ''}
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-center gap-1 rounded-2xl bg-canvas px-4 py-3">
          <MatchRing value={item.score} size={84} color="var(--gold)" caption="cocok" />
        </div>
      </div>
      {reasons.length ? (
        <div className="mt-4 flex flex-wrap gap-2 border-t border-line pt-4">
          {reasons.map((r, i) => (
            <span key={i} className="chip border-sage bg-sage/60">
              {r}
            </span>
          ))}
        </div>
      ) : null}
    </article>
  );
}

export default function RecommendPage() {
  const { ready, live, stats } = useApiMode();
  const [form, setForm] = useState(INITIAL_FORM);
  const [results, setResults] = useState(null); // null = belum mencari
  const [stageLabel, setStageLabel] = useState(null);
  const [resultMeta, setResultMeta] = useState(DEFAULT_META);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const resultsRef = useRef(null);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const cities =
    live && stats?.cities ? stats.cities : [...new Set(SAMPLE.map((s) => s.city))];

  const budgetHint = form.budget_max ? '≈ ' + rupiah(Number(form.budget_max)) : '';

  // hero stat chip
  let heroDot = 'bg-brand';
  let heroText = 'Memuat data…';
  if (ready) {
    if (live && stats) {
      heroText = `${Number(stats.records).toLocaleString('id-ID')} properti siap dicocokkan`;
      heroDot = 'bg-brand';
    } else {
      heroText = '12.946 properti pada dataset penuh';
      heroDot = 'bg-gold';
    }
  }

  async function runSearch(query) {
    setHasSearched(true);
    setError(null);
    setStageLabel(null);
    setResults(null);
    setLoading(true);
    setResultMeta('Menjalankan hard constraint filtering → soft ranking → constraint relaxation.');

    let data;
    try {
      if (live) {
        data = await fetchRecommendations(query);
      } else {
        await new Promise((r) => setTimeout(r, 350));
        data = demoRecommend(query);
      }
    } catch (e) {
      setLoading(false);
      setError(
        'Tidak dapat menghubungi server rekomendasi. Periksa apakah backend FastAPI sedang berjalan, lalu coba lagi.'
      );
      return;
    }

    setLoading(false);
    if (data.results && data.results.length) {
      setStageLabel(STAGE_LABEL[data.relaxation_stage] || data.relaxation_stage);
      setResultMeta(
        `Menampilkan ${data.returned} dari ${data.total_candidates} kandidat, diurutkan dari kecocokan tertinggi.`
      );
      setResults(data.results);
    } else {
      setStageLabel(null);
      setResultMeta('Tidak ada properti yang memenuhi kriteria.');
      setResults([]);
    }
    requestAnimationFrame(() =>
      resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    );
  }

  function onSubmit(e) {
    e.preventDefault();
    runSearch(buildQuery(form));
  }

  function fillExample() {
    const next = {
      ...form,
      property_type: 'rumah',
      transaction_type: 'jual',
      budget_max: '2000000000',
      city: 'Bekasi',
      bedrooms_min: '3',
      bathrooms_min: '2',
      furnishing: '',
    };
    setForm(next);
    runSearch(buildQuery(next));
  }

  function reset() {
    setForm(INITIAL_FORM);
    setResults(null);
    setHasSearched(false);
    setError(null);
    setStageLabel(null);
    setResultMeta(DEFAULT_META);
  }

  return (
    <>
      {/* ============ HERO ============ */}
      <section className="relative overflow-hidden border-b border-line">
        <div className="blueprint pointer-events-none absolute inset-0" />
        <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:py-16">
          <div className="reveal">
            <p className="eyebrow">Pencocokan berbasis pengetahuan</p>
            <h1 className="mt-3 font-display text-[2.5rem] font-600 leading-[1.05] tracking-tight sm:text-6xl">
              Properti yang benar-benar <span className="italic text-brand">cocok</span>, bukan sekadar tersedia.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-muted sm:text-lg">
              Atur budget, lokasi, dan kebutuhan ruang Anda. Mesin kami menyaring syarat wajib, memeringkat sisanya
              menurut kedekatan preferensi, lalu melonggarkan batas secukupnya agar Anda tetap mendapat pilihan
              terbaik.
            </p>

            <ol className="mt-8 grid gap-3 sm:grid-cols-3">
              <li className="rounded-2xl border border-line bg-surface/70 p-4">
                <span className="font-mono text-sm font-700 text-gold">01</span>
                <p className="mt-1.5 text-sm font-700">Saring syarat wajib</p>
                <p className="mt-1 text-xs leading-relaxed text-muted">Budget, tipe, lokasi, jumlah kamar.</p>
              </li>
              <li className="rounded-2xl border border-line bg-surface/70 p-4">
                <span className="font-mono text-sm font-700 text-gold">02</span>
                <p className="mt-1.5 text-sm font-700">Peringkat preferensi</p>
                <p className="mt-1 text-xs leading-relaxed text-muted">Harga, furnishing, fasilitas, luas.</p>
              </li>
              <li className="rounded-2xl border border-line bg-surface/70 p-4">
                <span className="font-mono text-sm font-700 text-gold">03</span>
                <p className="mt-1.5 text-sm font-700">Longgarkan bertahap</p>
                <p className="mt-1 text-xs leading-relaxed text-muted">Bila hasil terlalu sedikit.</p>
              </li>
            </ol>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a
                href="#cari"
                className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3 text-sm font-700 text-canvas shadow-lift transition hover:bg-brand-700 focus-ring"
              >
                Mulai cari rekomendasi
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14" />
                  <path d="m13 6 6 6-6 6" />
                </svg>
              </a>
              <span className="chip">
                <span className={`h-1.5 w-1.5 rounded-full ${heroDot}`} /> {heroText}
              </span>
            </div>
          </div>

          {/* signature: a "match meter" preview card */}
          <div className="reveal relative" style={{ animationDelay: '.08s' }}>
            <div className="absolute -inset-3 -z-10 rounded-[2.4rem] bg-gradient-to-br from-sage to-gold-soft/60" />
            <article className="rounded-4xl border border-line bg-surface p-6 shadow-card">
              <div className="flex items-center justify-between">
                <div className="flex gap-2">
                  <span className="chip">Rumah</span>
                  <span className="chip">Jual Beli</span>
                </div>
                <span className="text-xs font-600 text-muted">Contoh kecocokan</span>
              </div>

              <div className="mt-5 flex items-center gap-5">
                <div className="shrink-0">
                  <MatchRing value={0.92} size={104} stroke={10} color="var(--gold)" caption="cocok" />
                </div>
                <div>
                  <h3 className="font-display text-xl font-600 leading-snug">Rumah 3 KT di Summarecon Bekasi</h3>
                  <p className="mt-1 text-sm text-muted">Bekasi · 131 m² · Unfurnished</p>
                  <p className="mt-2 font-mono text-lg font-700 text-brand">Rp 1.950.000.000</p>
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-2 border-t border-line pt-4">
                <span className="chip border-sage bg-sage/60">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4">
                    <path d="M20 6 9 17l-5-5" />
                  </svg>{' '}
                  Masuk budget
                </span>
                <span className="chip border-sage bg-sage/60">Lokasi cocok</span>
                <span className="chip border-sage bg-sage/60">Jumlah kamar cocok</span>
              </div>
            </article>
          </div>
        </div>
      </section>

      {/* ============ TOOL: filter + results ============ */}
      <section id="cari" className="mx-auto max-w-7xl scroll-mt-20 px-4 py-12 sm:px-6 lg:py-16">
        <div className="grid gap-8 lg:grid-cols-[370px_1fr]">
          {/* FILTER PANEL */}
          <aside className="lg:sticky lg:top-24 lg:h-fit">
            <form onSubmit={onSubmit} className="rounded-4xl border border-line bg-surface p-6 shadow-card">
              <div className="flex items-center justify-between">
                <h2 className="font-display text-2xl font-600">Preferensi Anda</h2>
                <button
                  type="button"
                  onClick={reset}
                  className="text-xs font-600 text-muted underline-offset-4 hover:text-brand hover:underline focus-ring"
                >
                  Reset
                </button>
              </div>
              <p className="mt-1.5 text-sm text-muted">
                Kosongkan kolom yang tidak relevan — semakin spesifik, semakin tepat.
              </p>

              {/* jenis */}
              <div className="mt-6 space-y-1.5">
                <p className="eyebrow !tracking-[0.2em]">Jenis</p>
                <div className="grid grid-cols-2 gap-3">
                  <label className="block">
                    <span className="mb-1 block text-xs font-600 text-muted">Tipe properti</span>
                    <select value={form.property_type} onChange={set('property_type')} className="field">
                      <option value="">Semua</option>
                      <option value="rumah">Rumah</option>
                      <option value="apartemen">Apartemen</option>
                    </select>
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-xs font-600 text-muted">Transaksi</span>
                    <select value={form.transaction_type} onChange={set('transaction_type')} className="field">
                      <option value="">Semua</option>
                      <option value="jual">Jual Beli</option>
                      <option value="sewa">Sewa</option>
                    </select>
                  </label>
                </div>
              </div>

              {/* anggaran */}
              <div className="mt-5 space-y-1.5">
                <p className="eyebrow !tracking-[0.2em]">Anggaran</p>
                <label className="block">
                  <span className="mb-1 block text-xs font-600 text-muted">Budget maksimum (Rp)</span>
                  <input
                    type="number"
                    min="0"
                    step="1000000"
                    value={form.budget_max}
                    onChange={set('budget_max')}
                    className="field"
                    placeholder="contoh: 2000000000"
                  />
                  <span className="mt-1 block text-xs text-muted">{budgetHint}</span>
                </label>
              </div>

              {/* lokasi */}
              <div className="mt-5 space-y-1.5">
                <p className="eyebrow !tracking-[0.2em]">Lokasi</p>
                <div className="grid grid-cols-2 gap-3">
                  <label className="block">
                    <span className="mb-1 block text-xs font-600 text-muted">Kota</span>
                    <input
                      type="text"
                      list="cityList"
                      value={form.city}
                      onChange={set('city')}
                      className="field"
                      placeholder="Surabaya"
                    />
                    <datalist id="cityList">
                      {cities.map((c) => (
                        <option key={c} value={c} />
                      ))}
                    </datalist>
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-xs font-600 text-muted">Kecamatan / area</span>
                    <input
                      type="text"
                      value={form.district}
                      onChange={set('district')}
                      className="field"
                      placeholder="opsional"
                    />
                  </label>
                </div>
              </div>

              {/* ruang */}
              <div className="mt-5 space-y-1.5">
                <p className="eyebrow !tracking-[0.2em]">Ruang</p>
                <div className="grid grid-cols-2 gap-3">
                  <label className="block">
                    <span className="mb-1 block text-xs font-600 text-muted">Kamar tidur min.</span>
                    <input type="number" min="0" step="1" value={form.bedrooms_min} onChange={set('bedrooms_min')} className="field" placeholder="2" />
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-xs font-600 text-muted">Kamar mandi min.</span>
                    <input type="number" min="0" step="1" value={form.bathrooms_min} onChange={set('bathrooms_min')} className="field" placeholder="1" />
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-xs font-600 text-muted">Luas min. (m²)</span>
                    <input type="number" min="0" step="1" value={form.size_min} onChange={set('size_min')} className="field" placeholder="60" />
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-xs font-600 text-muted">Daya listrik min. (VA)</span>
                    <input type="number" min="0" step="100" value={form.max_watt_min} onChange={set('max_watt_min')} className="field" placeholder="1300" />
                  </label>
                </div>
              </div>

              {/* preferensi */}
              <div className="mt-5 space-y-1.5">
                <p className="eyebrow !tracking-[0.2em]">Preferensi</p>
                <div className="grid grid-cols-2 gap-3">
                  <label className="block">
                    <span className="mb-1 block text-xs font-600 text-muted">Furnishing</span>
                    <select value={form.furnishing} onChange={set('furnishing')} className="field">
                      <option value="">Semua</option>
                      <option value="furnished">Furnished</option>
                      <option value="semi furnished">Semi furnished</option>
                      <option value="unfurnished">Unfurnished</option>
                    </select>
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-xs font-600 text-muted">Kolam renang</span>
                    <select value={form.swim_pool} onChange={set('swim_pool')} className="field">
                      <option value="">Tidak masalah</option>
                      <option value="true">Harus ada</option>
                      <option value="false">Tidak perlu</option>
                    </select>
                  </label>
                </div>
              </div>

              {/* top_k */}
              <label className="mt-6 block">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-600 text-muted">Jumlah rekomendasi</span>
                  <span className="font-mono text-sm font-700 text-brand">{form.top_k}</span>
                </div>
                <input
                  type="range"
                  min="3"
                  max="20"
                  value={form.top_k}
                  onChange={set('top_k')}
                  className="mt-2 w-full"
                />
              </label>

              <button
                type="submit"
                disabled={loading}
                className="mt-6 flex w-full items-center justify-center gap-2 rounded-full bg-brand px-6 py-3.5 text-sm font-700 text-canvas shadow-lift transition hover:bg-brand-700 focus-ring disabled:opacity-60"
              >
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="7" />
                  <path d="m21 21-4.3-4.3" />
                </svg>
                Cari rekomendasi
              </button>
            </form>
          </aside>

          {/* RESULTS */}
          <div ref={resultsRef}>
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="font-display text-2xl font-600">Hasil rekomendasi</h2>
                <p className="mt-1 text-sm text-muted">{resultMeta}</p>
              </div>
              {stageLabel ? (
                <span className="inline-flex items-center gap-2 rounded-full border border-gold/40 bg-gold-soft/60 px-3.5 py-1.5 text-xs font-700 text-gold">
                  {stageLabel}
                </span>
              ) : null}
            </div>

            {/* empty state */}
            {!hasSearched && !loading ? (
              <div className="mt-6 rounded-4xl border border-dashed border-line bg-surface/60 p-10 text-center">
                <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-sage text-brand">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 11.5 12 4l9 7.5" />
                    <path d="M5 10v9h14v-9" />
                  </svg>
                </div>
                <h3 className="mt-4 font-display text-xl font-600">Belum ada pencarian</h3>
                <p className="mx-auto mt-1.5 max-w-sm text-sm text-muted">
                  Coba mulai dengan budget dan kota Anda. Tidak yakin? Tekan tombol di bawah untuk melihat contoh
                  pencocokan.
                </p>
                <button
                  type="button"
                  onClick={fillExample}
                  className="mt-5 inline-flex items-center gap-2 rounded-full border border-brand px-5 py-2.5 text-sm font-700 text-brand transition hover:bg-brand hover:text-canvas focus-ring"
                >
                  Lihat contoh hasil
                </button>
              </div>
            ) : null}

            {/* error state */}
            {error ? (
              <div className="mt-6 rounded-4xl border border-gold/50 bg-gold-soft/50 p-6">
                <p className="font-700 text-ink">Pencarian belum bisa dijalankan</p>
                <p className="mt-1 text-sm text-muted">{error}</p>
              </div>
            ) : null}

            {/* loading skeletons */}
            {loading ? (
              <div className="mt-6 space-y-4">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="rounded-4xl border border-line bg-surface p-6">
                    <div className="skeleton h-5 w-1/3 rounded" />
                    <div className="skeleton mt-3 h-7 w-2/3 rounded" />
                    <div className="skeleton mt-4 h-8 w-40 rounded" />
                  </div>
                ))}
              </div>
            ) : null}

            {/* results */}
            {!loading && results && results.length ? (
              <div className="mt-6 space-y-4">
                {results.map((item, i) => (
                  <PropertyCard key={i} item={item} index={i} />
                ))}
              </div>
            ) : null}

            {/* no results */}
            {!loading && results && results.length === 0 ? (
              <div className="mt-6 rounded-4xl border border-dashed border-line bg-surface/60 p-10 text-center">
                <h3 className="font-display text-xl font-600">Tidak ada hasil yang cocok</h3>
                <p className="mx-auto mt-1.5 max-w-sm text-sm text-muted">
                  Coba naikkan budget, hapus filter kota, atau kurangi jumlah kamar minimum.
                </p>
              </div>
            ) : null}
          </div>
        </div>
      </section>
    </>
  );
}
