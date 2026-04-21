'use client'

import { useState } from 'react'
import {
  LayoutDashboard,
  BarChart2,
  FileText,
  Users,
  Settings,
} from 'lucide-react'

export default function DashboardMockup(): JSX.Element {
  const [selectedAO, setSelectedAO] = useState(0)

  const aoList = [
    {
      name: 'Mise en plac...',
      date: '15 mars 2026',
      status: 'En cours',
      statusColor: 'bg-amber text-white',
      score: 94,
    },
    {
      name: 'Modernis...',
      date: '12 mars 2026',
      status: 'En révision',
      statusColor: 'bg-navy text-white',
      score: 87,
    },
    {
      name: 'Infrastruct...',
      date: '10 mars 2026',
      status: '✓ Validé',
      statusColor: 'bg-success text-white',
      score: 98,
    },
  ]

  const stats = [
    { icon: '📄', value: '247', label: 'Appels publiés', badge: '+24%', badgeColor: 'bg-success' },
    { icon: '✓', value: '94%', label: 'Conformité moy.', badge: 'En cours', badgeColor: 'bg-amber' },
    { icon: '⏱', value: '1840h', label: 'Temps épargné', badge: '+8%', badgeColor: 'bg-success' },
    { icon: '🏆', value: '68%', label: 'Taux de victoire', badge: '+12%', badgeColor: 'bg-success' },
  ]

  const selectedScore = aoList[selectedAO]?.score || 94
  const metrics = [
    { label: 'Conformité technique', value: 94, color: 'bg-amber' },
    { label: 'Complétude dossier', value: 87, color: 'bg-green-500' },
    { label: 'Risques identifiés', value: 12, color: 'bg-red-500' },
  ]

  return (
    <div className="relative animate-float">
      {/* Outer container with border and shadow */}
      <div className="border border-cream-border rounded-2xl shadow-2xl bg-white h-[600px]">
        {/* Browser chrome */}
        <div className="bg-gray-100 border-b border-gray-300 px-4 py-2.5">
          {/* Top dots */}
          <div className="flex gap-2 mb-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-amber-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          {/* URL bar */}
          <div className="bg-white border border-cream-border rounded-md px-3 py-1.5 flex items-center justify-center">
            <span className="text-xs text-gray-500">🔒 app.tenderai.tn</span>
          </div>
        </div>

        {/* Main content area */}
        <div className="flex h-full">
          {/* Sidebar */}
          <div className="w-48 bg-navy border-r border-navy-light px-3 py-4 flex flex-col">
            {/* Logo + Title */}
            <div className="flex items-center gap-2 mb-4 px-2">
              <div className="w-6 h-6 bg-amber rounded flex items-center justify-center text-navy font-bold text-xs">
                T
              </div>
              <span className="font-heading font-bold text-white text-sm">TenderAI</span>
            </div>

            {/* Tenant block */}
            <div className="bg-navy-light rounded-lg mx-0 my-3 p-2">
              <p className="text-xs font-bold text-white">TUNISIE TELECOM</p>
              <p className="text-xs text-amber">Plan Pro</p>
            </div>

            {/* Nav items */}
            <nav className="flex-1 space-y-1">
              {[
                { id: 'dashboard', label: 'Tableau de bord', icon: LayoutDashboard, active: true },
                { id: 'analytics', label: 'Analytics', icon: BarChart2, active: false },
                { id: 'documents', label: 'Documents', icon: FileText, active: false },
                { id: 'team', label: 'Équipe', icon: Users, active: false },
                { id: 'settings', label: 'Paramètres', icon: Settings, active: false },
              ].map(({ label, icon: Icon, active }) => (
                <div
                  key={label}
                  className={`flex items-center gap-2 px-2 py-2 rounded-lg text-xs cursor-pointer transition-colors ${
                    active
                      ? 'bg-amber/15 text-amber'
                      : 'text-white/50 hover:text-white/70'
                  }`}
                >
                  <Icon size={14} />
                  <span className="font-medium">{label}</span>
                </div>
              ))}
            </nav>

            {/* User avatar footer */}
            <div className="flex items-center gap-2 border-t border-white/10 pt-3">
              <div className="w-8 h-8 rounded-full bg-amber text-navy font-bold text-xs flex items-center justify-center">
                SB
              </div>
              <div className="flex-1 text-xs">
                <p className="font-semibold text-white">Sami</p>
                <p className="text-white/50 truncate">Sami.benKhalifa...</p>
              </div>
            </div>
          </div>

          {/* Main area */}
          <div className="flex-1 bg-cream flex flex-col overflow-visible">
            {/* Header */}
            <div className="border-b border-cream-border px-6 py-4 flex items-center justify-between">
              <div>
                <h3 className="font-heading font-bold text-sm text-navy">Appels d'offres</h3>
                <p className="text-xs text-muted">Tableau de bord · lundi 15 mars 2026</p>
              </div>
              <button className="bg-amber text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-amber-light transition-colors">
                📥 Importer
              </button>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-4 gap-2 px-6 py-4 bg-cream border-b border-cream-border">
              {stats.map((stat, i) => (
                <div key={i} className="bg-white border border-cream-border rounded-xl p-2.5">
                  <p className="text-lg font-heading font-bold text-navy">{stat.value}</p>
                  <p className="text-xs text-muted mb-2">{stat.label}</p>
                  <span className={`text-[9px] font-semibold ${stat.badgeColor} px-1.5 py-0.5 rounded-full text-white`}>
                    {stat.badge}
                  </span>
                </div>
              ))}
            </div>

            {/* Content area */}
            <div className="flex-1 px-6 py-4 overflow-visible flex gap-4">
              {/* Table section */}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-sm text-navy">Derniers appels ('26)</h4>
                  <a href="#" className="text-xs font-semibold text-amber hover:underline">
                    Voir tout →
                  </a>
                </div>
                <div className="space-y-2">
                  {aoList.map((ao, i) => (
                    <div
                      key={i}
                      onClick={() => setSelectedAO(i)}
                      className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${
                        selectedAO === i
                          ? 'bg-white border-l-4 border-l-amber'
                          : 'bg-white/50 hover:bg-white'
                      }`}
                    >
                      <span className="text-xs text-navy font-medium">{ao.name}</span>
                      <span className="text-xs text-muted">{ao.date}</span>
                      <span className={`text-xs font-semibold px-2 py-1 rounded ${ao.statusColor}`}>
                        {ao.status}
                      </span>
                      <span className="text-xs font-bold text-navy">{ao.score}%</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Score card */}
              <div className="w-44 bg-white border border-cream-border rounded-lg p-4">
                <h4 className="font-semibold text-sm text-navy mb-4">Score IA</h4>

                {/* Donut SVG */}
                <div className="relative w-32 h-32 mx-auto mb-4">
                  <svg viewBox="0 0 120 120" className="w-full h-full">
                    <circle
                      cx="60"
                      cy="60"
                      r="45"
                      fill="none"
                      stroke="#E5E0D8"
                      strokeWidth="8"
                    />
                    <circle
                      cx="60"
                      cy="60"
                      r="45"
                      fill="none"
                      stroke="#C4962A"
                      strokeWidth="8"
                      strokeDasharray={`${(selectedScore / 100) * 283} 283`}
                      strokeLinecap="round"
                      style={{ transform: 'rotate(-90deg)', transformOrigin: '60px 60px' }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="font-heading font-bold text-xl text-navy">
                      {selectedScore}%
                    </span>
                  </div>
                </div>

                {/* Mini bars */}
                <div className="space-y-2">
                  {metrics.map((metric, i) => (
                    <div key={i}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-muted">{metric.label}</span>
                        <span className="text-xs font-semibold text-navy">{metric.value}%</span>
                      </div>
                      <div className="h-1.5 bg-cream-border rounded-full overflow-hidden">
                        <div
                          className={`h-full ${metric.color}`}
                          style={{ width: `${metric.value}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Eligibility badge */}
                <div className="mt-4 pt-4 border-t border-cream-border">
                  <span className="text-xs text-green-600 font-medium">✓ Éligible à soumission</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes float {
          0%,
          100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-8px);
          }
        }

        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
      `}</style>
    </div>
  )
}
