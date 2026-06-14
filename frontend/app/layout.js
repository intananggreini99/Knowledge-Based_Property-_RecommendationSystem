import './globals.css';
import { Fraunces, Plus_Jakarta_Sans, Space_Grotesk } from 'next/font/google';
import { ApiModeProvider } from '@/components/ApiModeProvider';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

// Display / body / utility faces, exposed as CSS variables that
// tailwind.config.js and globals.css reference.
const display = Fraunces({ subsets: ['latin'], variable: '--font-display', display: 'swap' });
const sans = Plus_Jakarta_Sans({ subsets: ['latin'], variable: '--font-sans', display: 'swap' });
const mono = Space_Grotesk({ subsets: ['latin'], variable: '--font-mono', display: 'swap' });

export const metadata = {
  title: 'Rumaku — Rekomendasi Properti Cerdas',
  description:
    'Temukan rumah dan apartemen yang benar-benar cocok dengan kebutuhan Anda lewat pencocokan berbasis pengetahuan.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="id" className={`${display.variable} ${sans.variable} ${mono.variable}`}>
      <body className="bg-canvas text-ink antialiased">
        <ApiModeProvider>
          <Nav />
          <main>{children}</main>
          <Footer />
        </ApiModeProvider>
      </body>
    </html>
  );
}
