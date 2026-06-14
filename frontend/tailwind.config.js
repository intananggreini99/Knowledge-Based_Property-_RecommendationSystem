/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#F7F4EF',
        surface: '#FFFFFF',
        ink: '#1B2A26',
        brand: { DEFAULT: '#14564C', 700: '#0F4339', 900: '#0A2F28' },
        sage: '#E4EDE9',
        gold: { DEFAULT: '#B8893B', soft: '#F0E6D2' },
        line: '#E6DFD3',
        muted: '#6B7C76',
      },
      fontFamily: {
        // Wired to the next/font CSS variables defined in app/layout.js
        display: ['var(--font-display)', 'ui-serif', 'Georgia', 'serif'],
        sans: ['var(--font-sans)', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
      },
      // The original markup uses font-600 / font-700 utilities.
      fontWeight: {
        600: '600',
        700: '700',
      },
      boxShadow: {
        card: '0 1px 2px rgba(27,42,38,0.05), 0 18px 40px -28px rgba(27,42,38,0.35)',
        lift: '0 26px 60px -30px rgba(20,86,76,0.50)',
      },
      borderRadius: { '4xl': '2rem' },
    },
  },
  plugins: [],
};
