'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useApiMode } from '@/components/ApiModeProvider';

function NavLink({ href, active, children }) {
  return (
    <Link
      href={href}
      className={
        active
          ? 'rounded-full bg-brand px-4 py-1.5 text-sm font-600 text-canvas'
          : 'rounded-full px-4 py-1.5 text-sm font-600 text-muted transition hover:text-ink focus-ring'
      }
    >
      {children}
    </Link>
  );
}

export default function Nav() {
  const pathname = usePathname();
  const onEval = pathname.startsWith('/evaluation');
  const { ready, live } = useApiMode();

  let dotClass = 'bg-muted';
  let modeText = 'Memeriksa…';
  if (ready) {
    dotClass = live ? 'bg-brand' : 'bg-gold';
    modeText = live ? 'Terhubung API' : 'Mode demo (contoh data)';
  }

  return (
    <header className="sticky top-0 z-30 border-b border-line/80 bg-canvas/85 backdrop-blur">
      <nav className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3.5 sm:px-6">
        <Link href="/" className="group flex items-center gap-2.5 focus-ring">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand text-canvas shadow-sm">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 11.5 12 4l9 7.5" />
              <path d="M5 10v9h14v-9" />
              <path d="M10 19v-5h4v5" />
            </svg>
          </span>
          <span className="leading-tight">
            <span className="block font-display text-lg font-600 tracking-tight">Rumaku</span>
            <span className="block text-[0.62rem] font-600 uppercase tracking-[0.22em] text-muted">
              Property Recommender
            </span>
          </span>
        </Link>

        <div className="flex items-center gap-1.5 rounded-full border border-line bg-surface p-1 shadow-sm">
          <NavLink href="/" active={!onEval}>
            Rekomendasi
          </NavLink>
          <NavLink href="/evaluation" active={onEval}>
            Evaluasi Model
          </NavLink>
        </div>

        <div className="hidden items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 text-xs font-600 text-muted sm:flex">
          <span className={`h-2 w-2 rounded-full ${dotClass}`} />
          <span>{modeText}</span>
        </div>
      </nav>
    </header>
  );
}
