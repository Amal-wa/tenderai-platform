'use client'
import { motion } from 'framer-motion'
import type { SectorStat } from '@/lib/admin/analytics'

interface SectorChartProps {
  sectors: SectorStat[]
}

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.08 },
  },
}

const barVariants = {
  hidden: { scaleX: 0 },
  visible: {
    scaleX: 1,
    transition: { duration: 0.6, ease: [0.4, 0, 0.2, 1] },
  },
}

export default function SectorChart({ sectors }: SectorChartProps): React.ReactElement {
  return (
    <div className="bg-white rounded-2xl p-6 border border-[var(--cream-3)]">
      <h3 className="font-heading text-[15px] font-bold text-[var(--navy)] mb-1">
        Win rate par secteur
      </h3>
      <p className="text-[11px] text-[var(--text-4)] mb-6">
        Comparaison T1 2026 vs T4 2025
      </p>

      {/* Legend */}
      <div className="flex gap-4 mb-6">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[var(--amber)]" />
          <span className="text-[10px] text-[var(--text-3)]">T1 2026</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[var(--cream-3)]" />
          <span className="text-[10px] text-[var(--text-3)]">T4 2025</span>
        </div>
      </div>

      {/* Bars */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-4"
      >
        {sectors.map((sector) => (
          <motion.div key={sector.name} className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[13px] text-[var(--navy)] w-44">{sector.name}</span>
              <span className="text-[13px] font-bold text-[var(--navy)]">
                {sector.value}%
              </span>
            </div>
            <div className="flex gap-2">
              <motion.div
                variants={barVariants}
                className="flex-1 h-1.5 rounded origin-left"
                style={{ backgroundColor: sector.color }}
              />
              <div className="flex-1 h-1.5 rounded bg-[var(--cream-2)]" />
            </div>
            <div className="flex items-center justify-between ps-44">
              <span
                className={`text-[10px] font-semibold ${
                  sector.deltaType === 'up'
                    ? 'text-[var(--success)]'
                    : sector.deltaType === 'down'
                      ? 'text-[var(--danger)]'
                      : 'text-[var(--text-4)]'
                }`}
              >
                {sector.delta}
              </span>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  )
}
