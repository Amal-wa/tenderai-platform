export type DeltaType = 'up' | 'down' | 'neutral' | 'amber'
export type BarColor = 'success' | 'danger' | 'info' | 'amber' | 'purple'
export type ChipType = 'danger' | 'warning' | 'success'

export interface KpiMetric {
  title: string
  value: string
  delta: string
  deltaType: DeltaType
  sub: string
  barColor: BarColor
  barWidth: number
  alertVariant?: boolean
  darkVariant?: boolean
}

export interface SectorStat {
  name: string
  value: number
  delta: string
  deltaType: 'up' | 'down' | 'neutral'
  color: string
}

export interface AlertItem {
  name: string
  meta: string
  chip: string
  chipType: ChipType
  score: number
}

export interface HeroData {
  aos: number
  winRate: number
  conformite: number
  tenant: string
}

export interface NpsData {
  score: number
  label: string
  vsMarket: string
}

export interface AnalyticsData {
  hero: HeroData
  couche1: KpiMetric[]
  couche2: KpiMetric[]
  couche3row1: KpiMetric[]
  couche3row2: KpiMetric[]
  couche4: KpiMetric[]
  sectors: SectorStat[]
  alerts: AlertItem[]
  nps: NpsData
}

export function getAnalyticsData(): AnalyticsData {
  return {
    hero: { aos: 247, winRate: 68, conformite: 94, tenant: 'Fondements' },

    couche1: [
      { title: 'Win rate global',        value: '68%',       delta: '+27 pts',  deltaType: 'up',      sub: 'vs marché (41%)',           barColor: 'success', barWidth: 68 },
      { title: 'AOs soumis / analysés',  value: '34 / 247',  delta: '14%',      deltaType: 'neutral', sub: 'Taux de conversion',         barColor: 'info',    barWidth: 14 },
      { title: 'Valeur totale soumise',  value: '4,2 M TND', delta: '+18%',     deltaType: 'up',      sub: 'vs trimestre précédent',     barColor: 'amber',   barWidth: 72 },
      { title: 'Valeur contrats gagnés', value: '2,8 M TND', delta: '67%',      deltaType: 'neutral', sub: 'Win value rate',             barColor: 'success', barWidth: 67 },
    ],

    couche2: [
      { title: 'Conformité moyenne',             value: '94%',     delta: '+3 pts',        deltaType: 'up',      sub: 'Ce trimestre',          barColor: 'success', barWidth: 94 },
      { title: 'Critères manquants détectés',    value: '1 247',   delta: '312 critiques', deltaType: 'down',    sub: 'Dont 312 critiques',    barColor: 'danger',  barWidth: 55, alertVariant: true },
      { title: 'Précision NER extraction',       value: '91%',     delta: 'FR/AR/EN',      deltaType: 'neutral', sub: 'Sur corpus multilingue', barColor: 'info',    barWidth: 91 },
      { title: 'Satisfaction réponses IA',       value: '4,3 / 5', delta: '890 feedbacks', deltaType: 'neutral', sub: 'Score utilisateurs',     barColor: 'amber',   barWidth: 86 },
    ],

    couche3row1: [
      { title: 'Heures économisées',        value: '1 840 h', delta: 'Ce trimestre', deltaType: 'up',      sub: '≈ 230 jours·homme',      barColor: 'success', barWidth: 88 },
      { title: 'Temps moyen / AO',          value: '2,4 h',   delta: '−87%',         deltaType: 'up',      sub: 'vs 18h sans TenderAI',   barColor: 'info',    barWidth: 87 },
      { title: 'Taux réutilisation contenu',value: '61%',     delta: 'Bibliothèque', deltaType: 'neutral', sub: 'Templates sectoriels',   barColor: 'purple',  barWidth: 61 },
    ],

    couche3row2: [
      { title: 'Délais manqués',                    value: '2',        delta: '+2 vs précédent', deltaType: 'down',    sub: 'Action requise',           barColor: 'danger',  barWidth: 20, alertVariant: true },
      { title: 'Collaborateurs actifs / tenant',    value: '4,1 moy.', delta: 'Engagement',      deltaType: 'neutral', sub: 'Équipe active',            barColor: 'purple',  barWidth: 82 },
      { title: 'Documents OCR traités',             value: '3 120',    delta: '38% en arabe',    deltaType: 'neutral', sub: 'FR · AR · EN multilingue', barColor: 'success', barWidth: 78 },
    ],

    couche4: [
      { title: 'ROI estimé client', value: '× 8,4', delta: '×8,4 gains/coût',        deltaType: 'amber', sub: 'Gains / coût abonnement',        barColor: 'amber',   barWidth: 84, darkVariant: true },
      { title: 'Churn mensuel',     value: '1,2%',  delta: '−0,4 pts MoM',           deltaType: 'up',    sub: 'En amélioration',                barColor: 'success', barWidth: 12, darkVariant: true },
      { title: 'NPS',               value: '+62',   delta: 'Benchmark SaaS B2B : +34',deltaType: 'amber', sub: '+28 pts au-dessus du marché',    barColor: 'amber',   barWidth: 62, darkVariant: true },
    ],

    sectors: [
      { name: 'Informatique & SI',      value: 74, delta: '+8pts', deltaType: 'up',      color: 'var(--amber)' },
      { name: 'BTP & Travaux publics',  value: 61, delta: '+5pts', deltaType: 'up',      color: 'var(--success)' },
      { name: 'Énergie & Utilities',    value: 58, delta: '=',     deltaType: 'neutral', color: 'var(--info)' },
      { name: 'Santé & Équipement',     value: 49, delta: '−2pts', deltaType: 'down',    color: '#7F77DD' },
      { name: 'Transport & Logistique', value: 44, delta: '+3pts', deltaType: 'up',      color: 'var(--danger)' },
    ],

    alerts: [
      { name: 'Min. Éducation — Fournitures info.', meta: 'Échéance J−4 · Conformité 87%',   chip: 'Critique',   chipType: 'danger',  score: 87 },
      { name: 'STEG — Maintenance réseau',          meta: '3 annexes expirées · Conf. 72%',  chip: 'À corriger', chipType: 'warning', score: 72 },
      { name: 'Municipalité Tunis — Voirie',        meta: 'Soumis · Score 96%',              chip: 'Suivi',      chipType: 'success', score: 96 },
    ],

    nps: { score: 62, label: 'Excellent', vsMarket: '+28pts vs benchmark SaaS B2B' },
  }
}
