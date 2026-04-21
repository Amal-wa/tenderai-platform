'use client'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Plus, Bell, FileText, Clock, TrendingUp, ShieldCheck, AlertTriangle,
  SlidersHorizontal, ChevronDown
} from 'lucide-react'
import { extractErrorMessage, getDashboard } from '@/lib/api'
import type { UserDashboardResponse } from '@/types/dashboard'

// Types
type StatusType = 'todos' | 'brouillon' | 'soumis' | 'analyse' | 'gagne' | 'perdu'
type ColorType = 'default' | 'danger' | 'amber' | 'success' | 'neutral'

interface MetaChip {
  val: string
  label: string
  color: ColorType
}

interface AOItem {
  id: number
  sector: string
  title: string
  client: string
  status: StatusType
  statusLabel: string
  conformite: number
  conformiteColor: ColorType
  meta: MetaChip[]
  footerLeft?: string
  footerVal?: string
  footerValColor?: ColorType
  footerWarn?: string
  actionLabel: string
  actionVariant: 'primary' | 'secondary' | 'success' | 'danger'
  borderColor: string
}

interface StatItem {
  val: string
  label: string
  iconBg: string
  icon: React.ReactNode
  iconColor: string
  valColor?: string
}

// MOCK data
const mockAOs: AOItem[] = [
  {
    id: 1,
    sector: 'Informatique & SI',
    title: 'Min. Éducation — Fournitures informatiques',
    client: 'Ministère de l\'Éducation',
    status: 'soumis',
    statusLabel: 'Soumis',
    conformite: 87,
    conformiteColor: 'amber',
    meta: [
      { val: 'J−4', label: 'Échéance', color: 'danger' },
      { val: '8', label: 'Documents', color: 'default' },
      { val: '480 K', label: 'TND estimé', color: 'default' },
    ],
    footerLeft: 'Soumis le 10 avr.',
    actionLabel: 'Voir le dossier',
    actionVariant: 'primary',
    borderColor: '#378ADD',
  },
]

// ──────────────────────────────────────────────────────────────────
// TOPBAR COMPONENT
// ──────────────────────────────────────────────────────────────────

interface TopbarProps {
  userName: string
  notificationCount: number
}

function Topbar({ userName, notificationCount }: TopbarProps): React.ReactElement {
  const initials = userName
    .split(' ')
    .slice(0, 2)
    .map(n => n[0])
    .join('')
    .toUpperCase() || 'U'

  return (
    <header className="bg-white border-b border-[#E5E0D8] h-14 px-7 sticky top-0 z-20 flex items-center justify-between">
      <div>
        <p className="text-[11px] text-[#9B9590] font-medium">Mon espace</p>
        <h1 className="font-heading text-[17px] font-bold text-[#0F1C35]">Mes Appels d'offres</h1>
      </div>

      <div className="flex gap-[10px] items-center">
        <button className="flex items-center gap-[6px] bg-[#C4962A] text-[#0F1C35] text-xs font-bold px-[14px] py-[7px] rounded-lg hover:bg-[#d4a93c] transition">
          <Plus size={14} />
          Soumettre un AO
        </button>

        <button className="relative w-8 h-8 bg-[#F5F3EE] border border-[#E5E0D8] rounded-full flex items-center justify-center hover:bg-[#EDE9E2] transition">
          <Bell size={15} className="text-[#6B6560]" />
          {notificationCount > 0 && (
            <span className="absolute top-[3px] right-[3px] w-2 h-2 bg-[#E24B4A] border-2 border-white rounded-full" />
          )}
        </button>

        <div className="flex items-center gap-[7px] bg-[#F5F3EE] border border-[#E5E0D8] rounded-full py-1 pl-1 pr-[10px]">
          <div className="w-6 h-6 bg-[#C4962A] rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-white text-[9px] font-bold">{initials}</span>
          </div>
          <span className="text-xs font-semibold text-[#0F1C35]">{userName.split(' ')[0]}</span>
        </div>
      </div>
    </header>
  )
}

// ──────────────────────────────────────────────────────────────────
// STAT CARD COMPONENT
// ──────────────────────────────────────────────────────────────────

function StatCard({ val, label, iconBg, icon, valColor }: StatCardProps): React.ReactElement {
  return (
    <div className="bg-white border border-[#E5E0D8] rounded-[14px] p-[16px_18px] flex items-center gap-3">
      <div className="w-9 h-9 rounded-[9px] flex items-center justify-center flex-shrink-0" style={{ backgroundColor: iconBg }}>
        {icon}
      </div>
      <div>
        <p className="text-[22px] font-extrabold leading-none font-heading" style={{ color: valColor || '#0F1C35' }}>
          {val}
        </p>
        <p className="text-[11px] text-[#6B6560] mt-[2px]">{label}</p>
      </div>
    </div>
  )
}

interface StatCardProps extends StatItem {}

// ──────────────────────────────────────────────────────────────────
// AO CARD COMPONENT
// ──────────────────────────────────────────────────────────────────

interface AOCardProps {
  ao: AOItem
}

function AOCard({ ao }: AOCardProps): React.ReactElement {
  const getFillColor = (color: ColorType | 'neutral'): string => {
    switch (color) {
      case 'amber': return '#C4962A'
      case 'danger': return '#E24B4A'
      case 'success': return '#1D9E75'
      default: return '#6B6560'
    }
  }

  const getMetaChipColor = (color: ColorType | 'neutral'): string => {
    switch (color) {
      case 'amber': return '#C4962A'
      case 'danger': return '#E24B4A'
      case 'success': return '#1D9E75'
      default: return '#6B6560'
    }
  }

  const getActionBtnClasses = (variant: 'primary' | 'secondary' | 'success' | 'danger'): string => {
    switch (variant) {
      case 'primary': return 'bg-[#378ADD] text-white hover:bg-[#2970c2]'
      case 'secondary': return 'bg-[#F5F3EE] text-[#6B6560] border border-[#E5E0D8] hover:bg-[#EDE9E2]'
      case 'success': return 'bg-[#1D9E75] text-white hover:bg-[#178b64]'
      case 'danger': return 'bg-[#E24B4A] text-white hover:bg-[#d43f3e]'
      default: return ''
    }
  }

  return (
    <motion.div
      layoutId={`ao-${ao.id}`}
      className="bg-white border-l-4 border-t border-r border-b rounded-[12px] p-[14px] hover:shadow-md transition"
      style={{ borderLeftColor: ao.borderColor }}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[9px] font-mono font-bold text-white bg-[#6B6560] px-1.5 py-0.5 rounded">
              {ao.sector.substring(0, 8)}
            </span>
          </div>
          <h4 className="font-heading text-[12px] font-bold text-[#0F1C35] leading-tight line-clamp-2">
            {ao.title}
          </h4>
          <p className="text-[9px] text-[#9B9590] mt-1">{ao.client}</p>
        </div>
        <span
          className={`text-[9px] font-bold px-2 py-1 rounded-full whitespace-nowrap ms-2 ${
            ao.status === 'gagne'
              ? 'bg-[#1D9E75] text-white'
              : ao.status === 'perdu' || ao.status === 'analyse'
                ? 'bg-[#E24B4A] text-white'
                : ao.status === 'soumis'
                  ? 'bg-[#378ADD] text-white'
                  : 'bg-[#E5E0D8] text-[#6B6560]'
          }`}
        >
          {ao.statusLabel}
        </span>
      </div>

      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[9px] text-[#9B9590] font-semibold">Conformité</span>
          <span className="text-xs font-bold" style={{ color: getFillColor(ao.conformiteColor) }}>
            {ao.conformite}%
          </span>
        </div>
        <div className="h-[5px] bg-[#EDE9E2] rounded-full overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: getFillColor(ao.conformiteColor) }}
            initial={{ width: 0 }}
            animate={{ width: `${ao.conformite}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-[6px]">
        {ao.meta.map((chip, idx) => (
          <div key={idx} className="bg-[#F5F3EE] rounded-[7px] p-[6px_8px] text-center">
            <p className="text-xs font-bold" style={{ color: getMetaChipColor(chip.color) }}>
              {chip.val}
            </p>
            <p className="text-[9px] text-[#9B9590] mt-[1px]">{chip.label}</p>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between mt-[2px]">
        <div>
          {ao.footerWarn ? (
            <div className="flex items-center gap-1 bg-[#FCEAEA] px-2 py-[3px] rounded-[6px]">
              <AlertTriangle size={11} className="text-[#E24B4A] flex-shrink-0" />
              <span className="text-[10px] font-semibold text-[#E24B4A]">{ao.footerWarn}</span>
            </div>
          ) : (
            <>
              <span className="text-[11px] font-semibold text-[#6B6560]">{ao.footerLeft}</span>
              {ao.footerVal && (
                <span className="text-[11px] font-bold ms-1" style={{ color: getMetaChipColor(ao.footerValColor || 'default') }}>
                  {ao.footerVal}
                </span>
              )}
            </>
          )}
        </div>

        <button className={`text-[11px] font-bold px-3 py-[5px] rounded-[7px] transition ${getActionBtnClasses(ao.actionVariant)}`}>
          {ao.actionLabel}
        </button>
      </div>
    </motion.div>
  )
}

// ──────────────────────────────────────────────────────────────────
// MAIN PAGE COMPONENT
// ──────────────────────────────────────────────────────────────────

export default function UserPage(): React.ReactElement {
  const [dashboardData, setDashboardData] = useState<UserDashboardResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeFilter, setActiveFilter] = useState('Tous')

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true)
        const data = await getDashboard()
        setDashboardData(data)
      } catch (err) {
        setError(extractErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
  }, [])

  const formatPercent = (val?: number) => val !== undefined ? Math.round(val) + '%' : '--'

  const realStats: StatItem[] = [
    {
      val: String(dashboardData?.kpis.my_documents ?? '--'),
      label: 'AOs total',
      iconBg: '#EDE9E2',
      icon: <FileText size={18} color="#6B6560" />,
      iconColor: '#6B6560',
    },
    {
      val: String(dashboardData?.kpis.my_documents ?? '--'),
      label: 'AOs actifs',
      iconBg: '#E6F1FB',
      icon: <Clock size={18} color="#378ADD" />,
      iconColor: '#378ADD',
      valColor: '#378ADD',
    },
    {
      val: '68%',
      label: 'Win rate',
      iconBg: '#E1F5EE',
      icon: <TrendingUp size={18} color="#1D9E75" />,
      iconColor: '#1D9E75',
      valColor: '#1D9E75',
    },
    {
      val: formatPercent(dashboardData?.kpis.my_avg_score),
      label: 'Conformité moy.',
      iconBg: 'rgba(196,150,42,0.10)',
      icon: <ShieldCheck size={18} color="#C4962A" />,
      iconColor: '#C4962A',
      valColor: '#C4962A',
    },
  ]

  const unreadNotifications = dashboardData?.notifications?.filter(n => !n.is_read).length ?? 0
  const urgentNotifications = dashboardData?.notifications?.filter(n => n.type === 'urgent').slice(0, 2) ?? []

  const filterOptions = [
    { label: 'Tous', count: dashboardData?.my_documents?.length ?? 0 },
    { label: 'Brouillon', count: 2 },
    { label: 'Soumis', count: 1 },
    { label: 'En analyse', count: 1 },
    { label: 'Gagné', count: 1 },
    { label: 'Perdu', count: 1 },
  ]

  if (error) {
    return (
      <>
        <Topbar userName={dashboardData?.user?.full_name || 'User'} notificationCount={unreadNotifications} />
        <main className="flex-1 overflow-y-auto p-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            <p className="font-semibold">Erreur</p>
            <p className="text-sm">{error}</p>
          </div>
        </main>
      </>
    )
  }

  return (
    <>
      <Topbar userName={dashboardData?.user?.full_name || 'User'} notificationCount={unreadNotifications} />

      <main className="flex-1 overflow-y-auto p-[24px_28px_48px]">
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#C4962A]"></div>
            </div>
            <p className="text-[#9B9590] mt-4">Chargement du dashboard...</p>
          </div>
        )}

        {!loading && dashboardData && (
          <>
            <div className="grid grid-cols-4 gap-3 mb-4">
              {realStats.map((stat, idx) => (
                <StatCard key={idx} {...stat} />
              ))}
            </div>

            {urgentNotifications.length > 0 && (
              <div className="bg-[rgba(226,75,74,0.07)] border border-[rgba(226,75,74,0.18)] rounded-[10px] p-[10px_16px] flex items-center gap-[10px] mb-5">
                <AlertTriangle size={15} className="text-[#E24B4A] flex-shrink-0" />
                <p className="text-xs text-[#E24B4A] font-medium flex-1">
                  <strong>{urgentNotifications.length} alerte{urgentNotifications.length > 1 ? 's' : ''} active{urgentNotifications.length > 1 ? 's' : ''} :</strong> {urgentNotifications.map(n => n.message).join(' · ')}
                </p>
                <a href="#" className="text-[11px] font-bold text-[#E24B4A] whitespace-nowrap hover:underline">
                  Voir tout →
                </a>
              </div>
            )}

            <div className="flex items-center justify-between mb-[18px]">
              <div className="flex gap-[6px] flex-wrap">
                {filterOptions.map((option) => (
                  <button
                    key={option.label}
                    onClick={() => setActiveFilter(option.label)}
                    className={`flex items-center gap-[5px] px-3 py-[5px] rounded-full text-xs font-semibold transition ${
                      activeFilter === option.label
                        ? 'bg-[#0F1C35] text-white border border-[#0F1C35]'
                        : 'bg-white border border-[#E5E0D8] text-[#6B6560] hover:bg-[#F5F3EE]'
                    }`}
                  >
                    {option.label}
                    <span className="text-[10px] font-bold opacity-70">{option.count}</span>
                  </button>
                ))}
              </div>

              <button className="flex items-center gap-[5px] bg-white border border-[#E5E0D8] rounded-lg px-[10px] py-[5px] text-xs text-[#6B6560] cursor-pointer hover:bg-[#F5F3EE] transition">
                <SlidersHorizontal size={14} />
                Échéance (proche → loin)
                <ChevronDown size={14} />
              </button>
            </div>

            {dashboardData.my_documents && dashboardData.my_documents.length > 0 ? (
              <div className="grid grid-cols-3 gap-4">
                {mockAOs.map((ao) => (
                  <AOCard key={ao.id} ao={ao} />
                ))}
              </div>
            ) : (
              <div className="bg-white rounded-lg p-12 text-center border border-[#E5E0D8]">
                <FileText size={48} className="mx-auto text-[#9B9590] opacity-40 mb-4" />
                <p className="text-[#9B9590] font-medium">Aucun appel d'offres pour le moment</p>
              </div>
            )}
          </>
        )}
      </main>
    </>
  )
}
