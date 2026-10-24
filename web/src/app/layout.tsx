import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = { title: 'HTS — Comparação de conteúdo de textos', description: 'Comparação local de dois conteúdos em português, com correspondências explicáveis.' };
export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
