'use client'
import { motion } from 'framer-motion'
import Topbar from '@/components/dashboard/Topbar'
import HeroBanner from './HeroBanner'
import KpiCard from './KpiCard'
import SectionHeader from './SectionHeader'
import type { AdminDashboardResponse } from '@/types/dashboard'
import type { HeroData, KpiMetric } from '@/lib/admin/analytics'
import { Clock, AlertCircle } from 'lucide-react'

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.07 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] } },
}

interface AnalyticsDashboardProps {
  data: AdminDashboardResponse | null
  loading: boolean
  error?: boolean
}

// Map action types to French labels
const BUSINESS_ACTIONS = [
  'document.created',
  'document.updated',
  'document.deleted',
  'document.downloaded',
  'user.created',
  'user.updated',
  'role.assigned',
]

const actionLabels: Record<string, string> = {
  'document.created': 'Document ajouté',
  'document.updated': 'Document modifié',
  'document.deleted': 'Document supprimé',
  'document.downloaded': 'Document téléchargé',
  'user.created': 'Membre ajouté',
  'user.updated': 'Membre modifié',
  'role.assigned': 'Rôle assigné',
}

// Relative time formatter
function timeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (seconds < 60) return 'à l\'instant'
  if (seconds < 3600) return `il y a ${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `il y a ${Math.floor(seconds / 3600)}h`
  if (seconds < 604800) return `il y a ${Math.floor(seconds / 86400)}j`
  return date.toLocaleDateString('fr-FR')
}

// Team Activity Component
function TeamActivitySection({ activities }: { activities: AdminDashboardResponse['team_activity'] | undefined }) {
  if (!activities || activities.length === 0) {
    return (
      <div className="text-center py-8 text-[#9B9590]">
        <Clock size={24} className="mx-auto mb-2 opacity-30" />
        <p className="text-sm">Aucune activité récente</p>
      </div>
    )
  }

  const filteredActivities = activities.filter(item =>
    BUSINESS_ACTIONS.includes(item.action)
  )

  if (filteredActivities.length === 0) {
    return (
      <div className="text-center py-8 text-[#9B9590]">
        <Clock size={24} className="mx-auto mb-2 opacity-30" />
        <p className="text-sm">Aucune activité récente</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {filteredActivities.slice(0, 5).map((item, idx) => {
        const initials = item.full_name
          .split(' ')
          .slice(0, 2)
          .map(n => n[0])
          .join('')
          .toUpperCase()

        const actionLabel = actionLabels[item.action] || item.action
        const time = timeAgo(item.timestamp)

        return (
          <div key={idx} className="flex items-start gap-3 pb-3 border-b border-[#E5E0D8] last:border-0">
            {/* Avatar */}
            <div className="w-8 h-8 rounded-full bg-[#C4962A] flex items-center justify-center flex-shrink-0 text-xs font-bold text-white">
              {initials}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-[#0F1C35]">
                {item.full_name}
              </p>
              <p className="text-xs text-[#6B6560] mt-0.5">{actionLabel}</p>
              <p className="text-[10px] text-[#9B9590] mt-1">{time}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default function AnalyticsDashboard(props: AnalyticsDashboardProps): React.ReactElement {
  const { data, loading, error } = props

  const heroData: HeroData = data ? {
    aos: data.kpis.total_documents ?? 0,
    winRate: data.kpis.win_rate ?? 0,
    conformite: Math.round(data.kpis.avg_compliance_score ?? 0),
    tenant: data.tenant.name,
  } : {
    aos: 0,
    winRate: 0,
    conformite: 0,
    tenant: 'N/A',
  }

  const couche1: KpiMetric[] = data?.kpis ? [
    {
      title: 'Win rate global',
      value: `${Math.round(data.kpis.win_rate ?? 0)}%`,
      delta: '+27 pts',
      deltaType: 'up',
      sub: 'vs marché (41%)',
      barColor: 'success',
      barWidth: data.kpis.win_rate ?? 0,
    },
    {
      title: 'AOs soumis / analysés',
      value: `${data.status_distribution?.completed ?? 0} / ${data.kpis.total_documents ?? 0}`,
      delta: '14%',
      deltaType: 'neutral',
      sub: 'Taux de conversion',
      barColor: 'info',
      barWidth: Math.round(((data.status_distribution?.completed ?? 0) / (data.kpis.total_documents ?? 1)) * 100),
    },
  ] : []

  if (error) {
    return (
      <main className="flex-1 overflow-y-auto bg-[var(--cream)]">
        <Topbar />
        <div className="p-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-700">
            <AlertCircle size={24} className="mb-2" />
            <p className="font-semibold">Erreur de chargement</p>
            <p className="text-sm mt-2">Impossible de charger le dashboard. Veuillez réessayer.</p>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="flex-1 overflow-y-auto bg-[var(--cream)]">
      <Topbar />
      <div className="p-8">
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <div className="inline-block">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#C4962A]"></div>
            </div>
            <p className="text-[#9B9590] mt-4">Chargement du dashboard...</p>
          </motion.div>
        )}

        {!loading && (
          <>
            <HeroBanner hero={heroData} />

            <SectionHeader label="Performance commerciale" color="amber" />
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-2 gap-4 mb-7"
            >
              {couche1.map((m) => (
                <motion.div key={m.title} variants={itemVariants}>
                  <KpiCard metric={m} />
                </motion.div>
              ))}
            </motion.div>

            <div className="grid grid-cols-[1fr_380px] gap-4 mb-8">
              <div className="bg-white border border-[#E5E0D8] rounded-lg p-6">
                <h3 className="font-heading text-[14px] font-bold text-[#0F1C35] mb-4">
                  Documents récents
                </h3>
                {data?.recent_documents && data.recent_documents.length > 0 ? (
                  <div className="space-y-3">
                    {data.recent_documents.slice(0, 5).map((doc) => (
                      <div key={doc.id} className="flex items-center justify-between pb-3 border-b border-[#E5E0D8] last:border-0">
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-[#0F1C35] truncate">{doc.filename}</p>
                          <p className="text-[10px] text-[#9B9590] mt-1">{doc.document_type}</p>
                        </div>
                        <span className="text-[10px] font-semibold text-[#6B6560] whitespace-nowrap ms-2">{doc.status}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-[#9B9590]">Aucun document récent</p>
                )}
              </div>

              <div className="bg-white border border-[#E5E0D8] rounded-lg p-6">
                <h3 className="font-heading text-[14px] font-bold text-[#0F1C35] mb-4">
                  Activité récente
                </h3>
                <TeamActivitySection activities={data?.team_activity} />
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  )
}
