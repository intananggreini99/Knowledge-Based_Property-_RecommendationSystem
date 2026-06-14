'use client';

import { useEffect, useState } from 'react';
import { useApiMode } from '@/components/ApiModeProvider';
import MatchRing from '@/components/MatchRing';
import { useAnimatedNumber } from '@/components/useAnimatedNumber';
import { clamp01 } from '@/lib/format';
import { METRICS, demoMetrics } from '@/lib/demo';
import { fetchEvaluation } from '@/lib/api';

function prefersReducedMotion() {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  );
}

// Ring whose value eases up from 0 on (re)mount.
function CountUpRing({ value, ...props }) {
  const v = useAnimatedNumber(value);
  return <MatchRing value={v} {...props} />;
}

function MetricCard({ m, value, illustrative }) {
  const v = useAnimatedNumber(clamp01(value));
  const color = m.primary ? 'var(--gold)' : 'var(--brand)';
  return (
    <article
      className={`reveal rounded-4xl border ${m.primary ? 'border-gold/40' : 'border-line'} bg-surface p-5 shadow-card sm:p-6`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-lg font-600 leading-tight">{m.label}</h3>
          <p className="mt-1 max-w-[16rem] text-xs leading-relaxed text-muted">{m.blurb}</p>
        </div>
        {m.primary ? (
          <span className="chip">
            <span className="h-1.5 w-1.5 rounded-full bg-gold" /> Metrik utama
          </span>
        ) : null}
      </div>
      <div className="mt-4 flex items-center gap-4">
        <div className="shrink-0">
          <MatchRing value={v} size={80} color={color} caption="/ 100" />
        </div>
        <div>
          <p className={`font-mono text-3xl font-700 leading-none ${m.primary ? 'text-gold' : 'text-ink'}`}>
            {v.toFixed(3)}
          </p>
          <p className="mt-1 text-[0.7rem] font-600 uppercase tracking-wider text-muted">dari 1.000</p>
          {illustrative ? <p className="mt-2 text-[0.66rem] font-600 text-gold">contoh ilustratif</p> : null}
        </div>
      </div>
    </article>
  );
}

function MetricBars({ data }) {
  const t = useAnimatedNumber(1, { duration: 700 });
  const rows = METRICS.map((m) => ({ label: m.label, v: clamp01(data[m.key]), primary: m.primary }));
  const W = 720;
  const rowH = 46;
  const padL = 188;
  const padR = 56;
  const top = 8;
  const H = top * 2 + rows.length * rowH;
  const barMax = W - padL - padR;
  const grid = [0, 0.25, 0.5, 0.75, 1];

  return (
    <svg
      viewBox={`0 0 ${W} ${H + 16}`}
      className="w-full"
      role="img"
      aria-label="Perbandingan seluruh metrik dalam skala 0 sampai 1"
    >
      {grid.map((g, i) => {
        const x = padL + g * barMax;
        return (
          <g key={`g${i}`}>
            <line x1={x} y1={top - 2} x2={x} y2={H - top} stroke="var(--line)" strokeWidth="1" />
            <text
              x={x}
              y={H - 2}
              textAnchor="middle"
              style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#9AA8A2' }}
            >
              {g.toFixed(2)}
            </text>
          </g>
        );
      })}
      {rows.map((r, i) => {
        const y = top + i * rowH + 8;
        const fullW = Math.max(2, r.v * barMax);
        const w = fullW * t;
        const col = r.primary ? 'var(--gold)' : 'var(--brand)';
        const pct = (r.v * 100).toFixed(1);
        return (
          <g key={`b${i}`}>
            <text
              x={padL - 14}
              y={y + 15}
              textAnchor="end"
              style={{ fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 600, fill: 'var(--ink)' }}
            >
              {r.label}
            </text>
            <rect x={padL} y={y} width={barMax} height="22" rx="11" fill="var(--sage)" />
            <rect x={padL} y={y} width={w} height="22" rx="11" fill={col} />
            <text
              x={padL + fullW + 10}
              y={y + 15}
              style={{ fontFamily: 'var(--font-mono)', fontSize: 12.5, fontWeight: 700, fill: 'var(--muted)' }}
            >
              {pct}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function EvaluationPage() {
  const { ready, live } = useApiMode();
  const [sampleSize, setSampleSize] = useState(100);
  const [topK, setTopK] = useState(10);
  const [data, setData] = useState(() => demoMetrics(100, 10));
  const [illustrative, setIllustrative] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorShown, setErrorShown] = useState(false);
  const [evalMeta, setEvalMeta] = useState('Pratinjau angka contoh — tekan "Jalankan evaluasi".');
  const [runId, setRunId] = useState(0);

  // Once the API probe settles, update the hint line (without replaying anims).
  useEffect(() => {
    if (!ready) return;
    setEvalMeta(
      live
        ? 'API terdeteksi — tekan "Jalankan evaluasi" untuk hasil asli.'
        : 'Pratinjau angka contoh — tekan "Jalankan evaluasi".'
    );
  }, [ready, live]);

  async function runEval(e) {
    if (e) e.preventDefault();
    const sample_size = Number(sampleSize);
    const top_k = Number(topK);

    setErrorShown(false);
    setLoading(true);
    setEvalMeta('Menghitung…');

    let d = null;
    let illus = !live;
    let failed = false;

    if (live) {
      try {
        d = await fetchEvaluation(sample_size, top_k);
        illus = false;
      } catch (err) {
        failed = true;
        illus = true;
        d = demoMetrics(sample_size, top_k);
      }
    } else {
      d = demoMetrics(sample_size, top_k);
    }

    await new Promise((r) => setTimeout(r, prefersReducedMotion() ? 0 : 350));

    setLoading(false);
    setErrorShown(failed);
    setData(d);
    setIllustrative(illus);
    setRunId((id) => id + 1);
    setEvalMeta(
      illus ? 'Menampilkan angka contoh (ilustratif).' : `Selesai · ${d.sample_size} query dievaluasi.`
    );
  }

  return (
    <>
      {/* ============ HERO ============ */}
      <section className="relative overflow-hidden border-b border-line">
        <div className="blueprint pointer-events-none absolute inset-0" />
        <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:py-16">
          <div className="reveal">
            <p className="eyebrow">Evaluasi offline berbasis query</p>
            <h1 className="mt-3 font-display text-[2.5rem] font-600 leading-[1.05] tracking-tight sm:text-6xl">
              Seberapa <span className="italic text-brand">baik</span> rekomendasi kami sebenarnya?
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-muted sm:text-lg">
              Kami menguji mesin terhadap ratusan query sintetis, lalu mengukur mutu urutan hasil dan kepatuhannya
              pada syarat wajib. Semua metrik bernilai 0 sampai 1 — makin tinggi makin baik.
            </p>

            <ol className="mt-8 grid gap-3 sm:grid-cols-3">
              <li className="rounded-2xl border border-line bg-surface/70 p-4">
                <span className="font-mono text-sm font-700 text-gold">01</span>
                <p className="mt-1.5 text-sm font-700">Susun query uji</p>
                <p className="mt-1 text-xs leading-relaxed text-muted">Sampel preferensi dari data nyata.</p>
              </li>
              <li className="rounded-2xl border border-line bg-surface/70 p-4">
                <span className="font-mono text-sm font-700 text-gold">02</span>
                <p className="mt-1.5 text-sm font-700">Jalankan rekomendasi</p>
                <p className="mt-1 text-xs leading-relaxed text-muted">Ambil top-K untuk tiap query.</p>
              </li>
              <li className="rounded-2xl border border-line bg-surface/70 p-4">
                <span className="font-mono text-sm font-700 text-gold">03</span>
                <p className="mt-1.5 text-sm font-700">Hitung metrik</p>
                <p className="mt-1 text-xs leading-relaxed text-muted">Rata-rata seluruh query.</p>
              </li>
            </ol>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a
                href="#ukur"
                className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3 text-sm font-700 text-canvas shadow-lift transition hover:bg-brand-700 focus-ring"
              >
                Jalankan evaluasi
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14" />
                  <path d="m13 6 6 6-6 6" />
                </svg>
              </a>
              <a
                href="#metodologi"
                className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-6 py-3 text-sm font-700 text-ink transition hover:border-brand/40 focus-ring"
              >
                Lihat metodologi
              </a>
            </div>
          </div>

          {/* preview card: NDCG ring as a factual "match meter" */}
          <div className="reveal" style={{ animationDelay: '.08s' }}>
            <div className="relative mx-auto max-w-md rounded-4xl border border-line bg-surface p-6 shadow-card sm:p-8">
              <div className="flex items-center justify-between">
                <div>
                  <p className="eyebrow">Skor keseluruhan</p>
                  <p className="mt-1 font-display text-xl font-600">Kualitas peringkat</p>
                </div>
                <span className="chip">
                  <span className="h-1.5 w-1.5 rounded-full bg-gold" /> NDCG
                </span>
              </div>
              <div className="mt-6 flex items-center gap-5">
                <div className="shrink-0">
                  <CountUpRing key={runId} value={clamp01(data.ndcg)} size={104} stroke={10} color="var(--gold)" caption="/ 100" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm leading-relaxed text-muted">
                    NDCG menilai apakah properti paling relevan muncul di urutan teratas — bukan sekadar ada di
                    daftar.
                  </p>
                  <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-sage px-3 py-1 text-xs font-600 text-brand-700">
                    {illustrative ? (
                      <>
                        <span className="h-1.5 w-1.5 rounded-full bg-gold" /> Angka contoh — jalankan API untuk hasil asli
                      </>
                    ) : (
                      <>
                        <span className="h-1.5 w-1.5 rounded-full bg-brand" /> {data.sample_size} query · top-{data.top_k}
                      </>
                    )}
                  </div>
                </div>
              </div>
              <div className="mt-6 grid grid-cols-3 gap-2 border-t border-line pt-5 text-center">
                <div>
                  <p className="font-mono text-lg font-700 text-ink">{clamp01(data.precision).toFixed(3)}</p>
                  <p className="text-[0.68rem] font-600 uppercase tracking-wider text-muted">Precision</p>
                </div>
                <div>
                  <p className="font-mono text-lg font-700 text-ink">{clamp01(data.recall).toFixed(3)}</p>
                  <p className="text-[0.68rem] font-600 uppercase tracking-wider text-muted">Recall</p>
                </div>
                <div>
                  <p className="font-mono text-lg font-700 text-ink">{clamp01(data.f1_score).toFixed(3)}</p>
                  <p className="text-[0.68rem] font-600 uppercase tracking-wider text-muted">F1</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============ CONTROL + METRICS ============ */}
      <section id="ukur" className="mx-auto max-w-7xl scroll-mt-20 px-4 py-12 sm:px-6 lg:py-16">
        <div className="grid gap-8 lg:grid-cols-[320px_1fr]">
          {/* control panel (sticky) */}
          <aside className="lg:sticky lg:top-24 lg:self-start">
            <form onSubmit={runEval} className="rounded-4xl border border-line bg-surface p-5 shadow-card sm:p-6">
              <div className="flex items-center justify-between">
                <h2 className="font-display text-xl font-600">Parameter uji</h2>
                <span className="chip">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 3v18h18" />
                    <path d="m19 9-5 5-4-4-3 3" />
                  </svg>{' '}
                  Offline
                </span>
              </div>
              <p className="mt-1.5 text-sm leading-relaxed text-muted">
                Atur seberapa banyak query uji dan berapa hasil teratas yang dinilai.
              </p>

              <div className="mt-6 space-y-6">
                <div>
                  <div className="flex items-baseline justify-between">
                    <label htmlFor="sample_size" className="text-sm font-700">
                      Jumlah query uji
                    </label>
                    <span className="font-mono text-sm font-700 text-brand">{sampleSize}</span>
                  </div>
                  <input
                    id="sample_size"
                    type="range"
                    min="20"
                    max="300"
                    step="20"
                    value={sampleSize}
                    onChange={(e) => setSampleSize(Number(e.target.value))}
                    className="mt-3 w-full"
                  />
                  <div className="mt-1.5 flex justify-between text-[0.68rem] font-600 text-muted">
                    <span>20</span>
                    <span>lebih cepat ↔ lebih stabil</span>
                    <span>300</span>
                  </div>
                </div>

                <div>
                  <div className="flex items-baseline justify-between">
                    <label htmlFor="top_k" className="text-sm font-700">
                      Top-K dinilai
                    </label>
                    <span className="font-mono text-sm font-700 text-brand">{topK}</span>
                  </div>
                  <input
                    id="top_k"
                    type="range"
                    min="1"
                    max="20"
                    step="1"
                    value={topK}
                    onChange={(e) => setTopK(Number(e.target.value))}
                    className="mt-3 w-full"
                  />
                  <p className="mt-1.5 text-[0.68rem] font-600 text-muted">
                    Banyak hasil teratas yang diperhitungkan per query.
                  </p>
                </div>
              </div>

              <div className="mt-7 flex gap-2.5">
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex flex-1 items-center justify-center gap-2 rounded-full bg-brand px-5 py-3 text-sm font-700 text-canvas shadow-lift transition hover:bg-brand-700 focus-ring disabled:opacity-60"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                  Jalankan evaluasi
                </button>
              </div>

              <div className="mt-5 rounded-2xl border border-line bg-canvas/60 p-4">
                <p className="text-[0.7rem] font-700 uppercase tracking-wider text-muted">Cara membaca</p>
                <p className="mt-1.5 text-xs leading-relaxed text-muted">
                  Cincin <span className="font-700 text-gold">emas</span> = metrik mutu peringkat (NDCG). Cincin{' '}
                  <span className="font-700 text-brand">hijau</span> = metrik kepatuhan &amp; relevansi. Skala 0–1,
                  makin tinggi makin baik.
                </p>
              </div>
            </form>
          </aside>

          {/* metric results area */}
          <div>
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="eyebrow">Ringkasan metrik</p>
                <h2 className="mt-1 font-display text-2xl font-600 sm:text-3xl">Hasil evaluasi</h2>
              </div>
              <p className="text-sm text-muted">{evalMeta}</p>
            </div>

            {/* context bar */}
            {!loading ? (
              <div className="mt-4 flex flex-wrap items-center gap-2 rounded-2xl border border-line bg-surface px-4 py-3 text-xs font-600 text-muted">
                <span className="inline-flex items-center gap-1.5">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="9" />
                    <path d="M12 7v5l3 2" />
                  </svg>{' '}
                  {data.sample_size} query uji
                </span>
                <span className="text-line">·</span>
                <span>
                  Top-K dinilai: <span className="font-700 text-ink">{data.top_k}</span>
                </span>
                <span className="text-line">·</span>
                <span>
                  Sumber:{' '}
                  {illustrative ? (
                    <span className="font-700 text-gold">data contoh</span>
                  ) : (
                    <span className="font-700 text-brand">API langsung</span>
                  )}
                </span>
              </div>
            ) : null}

            {/* error state */}
            {errorShown ? (
              <div className="mt-5 rounded-4xl border border-gold/40 bg-gold-soft/50 p-6 text-center">
                <p className="font-700 text-ink">Tidak bisa memuat evaluasi dari API.</p>
                <p className="mt-1 text-sm text-muted">
                  Menampilkan angka contoh berlabel ilustratif. Jalankan backend untuk hasil sesungguhnya.
                </p>
              </div>
            ) : null}

            {/* loading skeleton */}
            {loading ? (
              <div className="mt-5">
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  {[0, 1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="skeleton h-44 rounded-4xl" />
                  ))}
                </div>
              </div>
            ) : null}

            {/* metric grid */}
            {!loading ? (
              <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {METRICS.map((m) => (
                  <MetricCard key={`${runId}-${m.key}`} m={m} value={data[m.key]} illustrative={illustrative} />
                ))}
              </div>
            ) : null}

            {/* comparison bar chart */}
            {!loading ? (
              <div className="mt-6 rounded-4xl border border-line bg-surface p-6 shadow-card sm:p-7">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="eyebrow">Perbandingan</p>
                    <h3 className="mt-1 font-display text-xl font-600">Semua metrik berdampingan</h3>
                  </div>
                  <span className="chip">Skala 0–1</span>
                </div>
                <div className="mt-6">
                  <MetricBars key={runId} data={data} />
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </section>

      {/* ============ METHODOLOGY ============ */}
      <section id="metodologi" className="border-t border-line bg-surface/50">
        <div className="mx-auto max-w-7xl scroll-mt-20 px-4 py-12 sm:px-6 lg:py-16">
          <div className="max-w-2xl">
            <p className="eyebrow">Metodologi</p>
            <h2 className="mt-1 font-display text-2xl font-600 sm:text-3xl">Bagaimana angka ini dihitung</h2>
            <p className="mt-4 text-base leading-relaxed text-muted">
              Evaluasi bersifat <span className="font-700 text-ink">offline &amp; berbasis query</span>. Dari
              dataset, sistem mengambil sejumlah sampel sebagai “query pengguna” sintetis. Untuk tiap query, mesin
              mengembalikan top-K rekomendasi, lalu hasilnya dinilai terhadap properti yang dianggap relevan menurut
              syarat query. Skor akhir adalah rata-rata seluruh query.
            </p>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2">
            <div className="rounded-4xl border border-line bg-surface p-6">
              <h3 className="font-display text-lg font-600">Metrik mutu peringkat</h3>
              <dl className="mt-4 space-y-4 text-sm">
                <div>
                  <dt className="font-700 text-ink">NDCG</dt>
                  <dd className="mt-1 leading-relaxed text-muted">
                    Menghargai sistem yang menaruh properti paling relevan di posisi teratas. Posisi penting — relevan
                    di urutan 1 bernilai lebih dari relevan di urutan 10.
                  </dd>
                </div>
                <div>
                  <dt className="font-700 text-ink">Precision</dt>
                  <dd className="mt-1 leading-relaxed text-muted">
                    Dari hasil yang ditampilkan, berapa proporsi yang benar-benar relevan. Mengukur seberapa “bersih”
                    daftar dari hasil meleset.
                  </dd>
                </div>
                <div>
                  <dt className="font-700 text-ink">Recall</dt>
                  <dd className="mt-1 leading-relaxed text-muted">
                    Dari semua properti relevan yang ada, berapa proporsi yang berhasil ditangkap di top-K. Mengukur
                    seberapa lengkap cakupannya.
                  </dd>
                </div>
                <div>
                  <dt className="font-700 text-ink">F1</dt>
                  <dd className="mt-1 leading-relaxed text-muted">
                    Rata-rata harmonik Precision dan Recall — satu angka yang menyeimbangkan ketepatan dan kelengkapan.
                  </dd>
                </div>
              </dl>
            </div>

            <div className="rounded-4xl border border-line bg-surface p-6">
              <h3 className="font-display text-lg font-600">Metrik kepatuhan &amp; relevansi</h3>
              <dl className="mt-4 space-y-4 text-sm">
                <div>
                  <dt className="font-700 text-ink">Constraint Satisfaction Rate (CSR)</dt>
                  <dd className="mt-1 leading-relaxed text-muted">
                    Proporsi hasil yang mematuhi syarat wajib query — misalnya tipe properti, lokasi, dan tidak
                    melebihi budget. Idealnya mendekati 1.
                  </dd>
                </div>
                <div>
                  <dt className="font-700 text-ink">Valid Recommendation Rate (VRR)</dt>
                  <dd className="mt-1 leading-relaxed text-muted">
                    Proporsi query yang menghasilkan setidaknya satu rekomendasi valid. Menjaga agar pengguna jarang
                    melihat hasil kosong.
                  </dd>
                </div>
                <div className="rounded-2xl bg-canvas/70 p-4">
                  <dt className="font-700 text-ink">Tentang pelonggaran</dt>
                  <dd className="mt-1 leading-relaxed text-muted">
                    Bila syarat ketat menghasilkan terlalu sedikit kandidat, mesin melonggarkan batas secara bertahap
                    (budget → lokasi → semua). CSR &amp; VRR membantu memantau dampak pelonggaran terhadap mutu.
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
