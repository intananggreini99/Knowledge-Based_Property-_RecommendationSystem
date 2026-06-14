export default function Footer() {
  return (
    <footer className="border-t border-line bg-surface/60">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-4 px-4 py-8 sm:flex-row sm:items-center sm:px-6">
        <div className="flex items-center gap-2.5">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand text-canvas">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 11.5 12 4l9 7.5" />
              <path d="M5 10v9h14v-9" />
            </svg>
          </span>
          <p className="text-sm text-muted">
            <span className="font-700 text-ink">Rumaku</span> — sistem rekomendasi sewa &amp; jual beli properti.
          </p>
        </div>
        <p className="text-xs text-muted">Knowledge-Based Filtering · FastAPI · PostgreSQL · Next.js</p>
      </div>
    </footer>
  );
}
