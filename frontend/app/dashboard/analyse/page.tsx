import type { Metadata } from 'next'
import AnalyseClient from './AnalyseClient'

export const metadata: Metadata = {
  title: 'Analyse IA — TenderAI',
  description: 'Analysez vos appels d\'offres avec l\'intelligence artificielle',
}

export default function AnalysePage() {
  return <AnalyseClient />
}
