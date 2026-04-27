'use client'

import { BarChart3, TrendingUp, Clock, Zap } from 'lucide-react'
import type { AnalyseStats } from '@/types/analyse'

interface KpiStripProps {
  stats: AnalyseStats | null
}

export default function KpiStrip({ stats }: KpiStripProps) {
  const kpis = [
    {
      icon: BarChart3,
      bgColor: 'bg-[rgba(30,95,168,0.1)]',
      iconColor: 'text-[#1E5FA8]',
      value: stats?.total_analysed ?? 0,
      label: 'AOs analysés',
      delta: `+${stats?.delta_analysed ?? 0} ce mois`,
      deltaType: 'up' as const,
    },
    {
      icon: TrendingUp,
      bgColor: 'bg-[rgba(31,122,77,0.1)]',
      iconColor: 'text-[#1F7A4D]',
      value: `${stats?.avg_conformite ?? 0}%`,
      label: 'Conformité moyenne',
      delta: `+${stats?.delta_conformite ?? 0}pts`,
      deltaType: 'up' as const,
    },
    {
      icon: Clock,
      bgColor: 'bg-[rgba(196,150,42,0.1)]',
      iconColor: 'text-[var(--amber)]',
      value: `${stats?.hours_saved ?? 0}h`,
      label: 'Heures économisées',
      delta: 'ce trimestre',
      deltaType: 'neutral' as const,
    },
    {
      icon: Zap,
      bgColor: 'bg-[rgba(107,70,140,0.1)]',
      iconColor: 'text-[#6B468C]',
      value: `${stats?.success_rate ?? 0}%`,
      label: 'Taux de succès',
      delta: stats?.delta_success_rate != null
        ? `+${stats.delta_success_rate}pts vs marché`
        : 'vs marché',
      deltaType: 'up' as const,
    },
  ]

  return (
    <div className="grid grid-cols-4 gap-3 px-6 py-4 bg-white border-b border-[var(--border)] flex-shrink-0">
      {kpis.map((kpi, idx) => {
        const IconComponent = kpi.icon
        return (
          <div
            key={idx}
            className="flex items-center gap-3 p-2.5 border border-[var(--border)] rounded-lg bg-[var(--cream)]"
          >
            <div
              className={`${kpi.bgColor} ${kpi.iconColor} w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0`}
            >
              <IconComponent size={16} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-mono text-lg font-semibold text-[var(--navy)]">
                {kpi.value}
              </div>
              <div className="text-xs text-[var(--muted)] mt-0.5">{kpi.label}</div>
            </div>
            <div
              className={`text-xs font-semibold px-1.5 py-1 rounded-lg flex-shrink-0 ${
                kpi.deltaType === 'up'
                  ? 'bg-[rgba(31,122,77,0.08)] text-[#1F7A4D]'
                  : 'bg-[rgba(107,101,96,0.1)] text-[var(--muted)]'
              }`}
            >
              {kpi.delta}
            </div>
          </div>
        )
      })}
    </div>
  )
}