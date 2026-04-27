export interface AnalyseStats {
  total_analysed: number
  avg_conformite: number
  hours_saved: number
  success_rate: number
  delta_analysed: number
  delta_conformite: number
  delta_success_rate?: number
}

export interface AnalyseRequest {
  tender_id?: string
  document_url?: string
  type: 'conformite' | 'technique' | 'financier' | 'complet'
  lang: 'FR' | 'AR' | 'EN'
  scope: Array<'criteres' | 'risques' | 'reponse' | 'score'>
  detail: 'synthese' | 'approfondi'
}

export interface AnalyseResult {
  id: string
  score_conformite: number
  score_technique: number
  score_risque: number
  resume: string
  criteres_manquants: string[]
  risques: string[]
  reponse_generee: string
  recommandations: string[]
  created_at: string
}

export interface AnalyseHistoryItem {
  id: string
  file_name: string
  created_at: string
  type: string
  score_conformite: number
  lang: string
}
