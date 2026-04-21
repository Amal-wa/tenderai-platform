'use client'
import { motion } from 'framer-motion'
import {
  TrendingUp, FileText, Trophy, Shield, AlertTriangle, Cpu,
  Star, Clock, Timer, RefreshCw, CalendarX, Users, ScanLine,
  Award, UserMinus
} from 'lucide-react'
import type { KpiMetric } from '@/lib/admin/analytics'

interface KpiCardProps {
  metric: KpiMetric
  accentColor?: string
  className?: string
}

const iconMap: Record<string, React.ComponentType<{ size: number; className?: string }>> = {
  'Win rate': TrendingUp,
  'AOs soumis': FileText,
  'Valeur': Trophy,
  'Conformité': Shield,
  'Critères manquants': AlertTriangle,
  'Précision NER': Cpu,
  'Satisfaction': Star,
  'Heures économisées': Clock,
  'Temps moyen': Timer,
  'Taux réutilisation': RefreshCw,
  'Délais manqués': CalendarX,
  'Collaborateurs': Users,
  'Documents OCR': ScanLine,
  'ROI': TrendingUp,
  'Churn': UserMinus,
  'NPS': Award,
}

function getIconForTitle(title: string): React.ComponentType<{ size: number; className?: string }> {
  for (const [key, icon] of Object.entries(iconMap)) {
    if (title.includes(key)) return icon
  }
  return FileText
}

function getDeltaClasses(deltaType: string): string {
  switch (deltaType) {
    case 'up':
      return 'bg-[var(--success-bg)] text-[var(--success)]'
    case 'down':
      return 'bg-[var(--danger-bg)] text-[var(--danger)]'
    case 'neutral':
      return 'bg-[var(--cream-2)] text-[var(--text-3)]'
    case 'amber':
      return 'bg-[var(--amber-soft)] text-[var(--amber)]'
    default:
      return ''
  }
}

function getBarColor(color: string): string {
  switch (color) {
    case 'success':
      return 'var(--success)'
    case 'danger':
      return 'var(--danger)'
    case 'info':
      return 'var(--info)'
    case 'amber':
      return 'var(--amber)'
    case 'purple':
      return '#7F77DD'
    default:
      return 'var(--navy)'
  }
}

export default function KpiCard({
  metric,
  className = '',
}: KpiCardProps): React.ReactElement {
  const Icon = getIconForTitle(metric.title)
  const bgClass = metric.darkVariant ? 'bg-[var(--navy)]' : 'bg-white border border-[var(--cream-3)]'
  const borderClass = metric.alertVariant ? 'border-s-[3px] border-[var(--danger)] rounded-s-none' : ''
  const textColor = metric.darkVariant ? 'text-white' : 'text-[var(--navy)]'

  return (
    <motion.div
      className={`${bgClass} rounded-2xl p-5 ${borderClass} ${className}`}
      whileHover={{ y: -3 }}
      transition={{ duration: 0.2 }}
      role="region"
      aria-label={metric.title}
    >
      <style>{`
        .kpi-accent-bar {
          position: relative;
          overflow: hidden;
        }
        .kpi-accent-bar::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 2px;
          background: ${getBarColor(metric.barColor)};
          transform: scaleX(0);
          transform-origin: left;
          transition: transform 0.3s ease;
        }
        .kpi-accent-bar:hover::before {
          transform: scaleX(1);
        }
      `}</style>

      <div className="kpi-accent-bar">
        {/* Top Row - Icon + Delta Chip */}
        <div className="flex items-center justify-between mb-3">
          <Icon
            size={18}
            className={metric.darkVariant ? 'text-white/60' : 'text-[var(--text-3)]'}
          />
          <span
            className={`text-[10px] font-bold px-2 py-1 rounded-full ${getDeltaClasses(
              metric.deltaType
            )}`}
          >
            {metric.delta}
          </span>
        </div>

        {/* Value */}
        <p className={`font-heading text-[28px] font-black ${metric.darkVariant ? 'text-[var(--amber)]' : 'text-[var(--navy)]'} mb-2`}>
          {metric.value}
        </p>

        {/* Label */}
        <p
          className={`text-xs ${metric.darkVariant ? 'text-white/40' : 'text-[var(--text-3)]'} mb-4`}
        >
          {metric.title}
        </p>

        {/* Sub */}
        <p
          className={`text-[11px] ${metric.darkVariant ? 'text-white/30' : 'text-[var(--text-4)]'} mb-3`}
        >
          {metric.sub}
        </p>

        {/* Progress Bar */}
        <div className={`h-1 rounded-full overflow-hidden ${metric.darkVariant ? 'bg-white/10' : 'bg-[var(--cream-2)]'}`}>
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: getBarColor(metric.barColor) }}
            initial={{ width: 0 }}
            animate={{ width: `${metric.barWidth}%` }}
            transition={{
              duration: 1.1,
              ease: [0.4, 0, 0.2, 1],
            }}
          />
        </div>
      </div>
    </motion.div>
  )
}
