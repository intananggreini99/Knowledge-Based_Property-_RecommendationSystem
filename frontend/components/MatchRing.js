'use client';

import { clamp01 } from '@/lib/format';

// The "match meter" — the signature element shared by both pages.
// Renders a circular progress ring with a big value and a small caption.
export default function MatchRing({
  value,
  size = 96,
  stroke = 9,
  color = 'var(--brand)',
  caption = 'cocok',
}) {
  const v = clamp01(value);
  const r = size / 2 - stroke;
  const c = 2 * Math.PI * r;
  const dash = (v * c).toFixed(2);
  const gap = (c - dash).toFixed(2);
  const val = Math.round(v * 100);

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className="block"
      role="img"
      aria-label={`Nilai ${val} dari 100`}
    >
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--sage)" strokeWidth={stroke} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={`${dash} ${gap}`}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text
        x="50%"
        y="47%"
        textAnchor="middle"
        dominantBaseline="middle"
        style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: size * 0.24, fill: 'var(--ink)' }}
      >
        {val}
      </text>
      <text
        x="50%"
        y="65%"
        textAnchor="middle"
        dominantBaseline="middle"
        style={{ fontFamily: 'var(--font-sans)', fontWeight: 600, fontSize: size * 0.11, fill: 'var(--muted)' }}
      >
        {caption}
      </text>
    </svg>
  );
}
