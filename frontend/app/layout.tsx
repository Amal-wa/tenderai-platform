import type { Metadata } from 'next'
import { IBM_Plex_Sans, Sora, Noto_Sans_Arabic } from 'next/font/google'
import { Providers } from '@/components/providers'
import './globals.css'

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-ibm',
  display: 'swap',
})

const sora = Sora({
  subsets: ['latin'],
  weight: ['300', '400', '600', '700'],
  variable: '--font-sora',
  display: 'swap',
})

const notoArabic = Noto_Sans_Arabic({
  subsets: ['arabic'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-arabic',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'TenderAI — Appels d\'offres avec intelligence',
  description:
    'Automatisez l\'analyse, la conformité et le suivi de vos marchés publics.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="fr"
      dir="ltr"
      className={`${ibmPlexSans.variable} ${sora.variable} ${notoArabic.variable}`}
    >
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
