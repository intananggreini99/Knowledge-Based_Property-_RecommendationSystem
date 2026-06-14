// Centralised access to the FastAPI backend.
//
// The base URL comes from NEXT_PUBLIC_API_URL (set in Vercel / .env.local).
// When it is empty the app silently falls back to offline "demo" mode, so the
// site stays fully usable on Vercel even before the Railway backend is wired up.

export const API_BASE = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');

function withTimeout(ms) {
  // AbortSignal.timeout isn't available in every browser; degrade gracefully.
  if (typeof AbortSignal !== 'undefined' && AbortSignal.timeout) {
    return { signal: AbortSignal.timeout(ms) };
  }
  return {};
}

// Returns the stats payload if the API is reachable, otherwise null.
export async function fetchStats(timeoutMs = 2500) {
  if (!API_BASE) return null;
  try {
    const res = await fetch(`${API_BASE}/api/stats`, withTimeout(timeoutMs));
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// POST a recommendation query. Throws on any failure so the caller can fall
// back to the demo engine.
export async function fetchRecommendations(query) {
  const res = await fetch(`${API_BASE}/api/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(query),
  });
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return res.json();
}

// GET evaluation metrics. Throws on any failure.
export async function fetchEvaluation(sampleSize, topK, timeoutMs = 20000) {
  const res = await fetch(
    `${API_BASE}/api/evaluate?sample_size=${sampleSize}&top_k=${topK}`,
    withTimeout(timeoutMs)
  );
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return res.json();
}
