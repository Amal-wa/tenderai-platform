'use client'
import { useState } from 'react'
import NpsDonut from './NpsDonut'
import type { AlertItem, NpsData } from '@/lib/admin/analytics'

interface AlertsPanelProps {
  alerts: AlertItem[]
  nps: NpsData
}

function getChipClasses(chipType: string): string {
  switch (chipType) {
    case 'danger':
      return 'bg-[var(--danger-bg)] text-[var(--danger)]'
    case 'warning':
      return 'bg-[var(--amber-soft)] text-[var(--amber)]'
    case 'success':
      return 'bg-[var(--success-bg)] text-[var(--success)]'
    default:
      return ''
  }
}

export default function AlertsPanel({
  alerts,
  nps,
}: AlertsPanelProps): React.ReactElement {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({})

  return (
    <div className="bg-white rounded-2xl p-6 border border-[var(--cream-3)] flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="font-heading text-[15px] font-bold text-[var(--navy)]">
            AOs prioritaires
          </h3>
          <p className="text-[11px] text-[var(--text-4)]">
            Alertes actives · 3 AOs
          </p>
        </div>
        <a href="#" className="text-[11px] font-semibold text-[var(--amber)] hover:underline">
          Voir tout →
        </a>
      </div>

      {/* Alerts */}
      <div className="space-y-3 mb-6 flex-1">
        {alerts.map((alert, idx) => (
          <div
            key={alert.name}
            onClick={() => setExpanded((p) => ({ ...p, [idx]: !p[idx] }))}
            className={`p-4 border border-[var(--cream-3)] rounded-lg cursor-pointer transition-colors ${
              expanded[idx] ? 'bg-[var(--cream)]' : 'hover:bg-[var(--cream)]'
            }`}
          >
            {/* Indicator dot + Row */}
            <div className="flex items-start gap-3">
              <div
                className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
                style={{
                  backgroundColor:
                    alert.chipType === 'danger'
                      ? 'var(--danger)'
                      : alert.chipType === 'warning'
                        ? 'var(--amber)'
                        : 'var(--success)',
                }}
              />
              <div className="flex-1 min-w-0">
                <p className="text-[13px] font-semibold text-[var(--navy)] truncate">
                  {alert.name}
                </p>
                <p className="text-[11px] text-[var(--text-4)] mt-0.5">{alert.meta}</p>

                {/* Chip + Score Bar */}
                <div className="flex items-center gap-3 mt-2">
                  <span
                    className={`text-[9px] font-bold px-2 py-1 rounded-full ${getChipClasses(
                      alert.chipType
                    )}`}
                  >
                    {alert.chip}
                  </span>
                  <div className="flex-1 h-1 bg-[var(--cream-2)] rounded overflow-hidden">
                    <div
                      className="h-full bg-[var(--amber)]"
                      style={{ width: `${alert.score}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-bold text-[var(--navy)]">
                    {alert.score}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Divider */}
      <div className="border-t border-[var(--cream-3)] pt-6" />

      {/* NPS */}
      <div className="flex items-center gap-4">
        <NpsDonut score={nps.score} label={nps.label} vsMarket={nps.vsMarket} />
      </div>
    </div>
  )
}
