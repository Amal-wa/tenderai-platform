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
