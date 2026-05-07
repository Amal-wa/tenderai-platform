'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { useAuditLogs, type GetAuditLogsParams } from '@/hooks/useAuditLogs'
import type { AuditLogItem } from '@/lib/api'
import {
  FileText,
  Users,
  Lock,
  Building2,
  Shield,
  Zap,
  BarChart3,
  Search,
  ChevronLeft,
  ChevronRight,
  X,
  AlertCircle,
  CheckCircle2,
  Clock,
} from 'lucide-react'

const ACTION_LABELS: Record<string, string> = {
  'session.started': 'Connexion',
  'session.ended': 'Déconnexion',
  'session.failed': 'Tentative échouée',
  'session.refreshed': 'Renouvellement de session',
  'session.suspicious': 'Activité suspecte',
  'session.rejected': 'Session révoquée',
  'totp.activated': 'Activation 2FA',
  'totp.login_success': 'Connexion 2FA réussie',
  'totp.login_failed': 'Échec 2FA',
  'totp.setup_initiated': 'Configuration 2FA initiée',
  'totp.backup_codes_regenerated': 'Codes de secours régénérés',
  'auth.password_changed': 'Changement de mot de passe',
  'user.created': 'Utilisateur créé',
  'user.updated': 'Utilisateur modifié',
  'user.deleted': 'Utilisateur supprimé',
  'user.email_verified': 'Email vérifié',
  'user.verification_email_resent': 'Email de vérification renvoyé',
  'user.profile_updated': 'Profil mis à jour',
  'role.created': 'Rôle créé',
  'role.assigned': 'Rôle attribué',
  'document.created': 'Document uploadé',
  'document.deleted': 'Document supprimé',
  'document.downloaded': 'Document téléchargé',
  'tenant.updated': 'Paramètres mis à jour',
  'tenant.logo_updated': 'Logo mis à jour',
  'apikey.created': 'Clé API créée',
  'apikey.revoked': 'Clé API révoquée',
  'analysis.started': 'Analyse lancée',
  'analysis.exported': 'Rapport exporté',
}

const getActionLabel = (action: string): string =>
  ACTION_LABELS[action] ?? action.replace(/\./g, ' › ')

const RESOURCE_META: Record<string, { icon: React.ReactNode; label: string; bgColor: string }> = {
  document: { icon: <FileText className="w-3 h-3" />, label: 'document', bgColor: 'bg-blue-100' },
  user: { icon: <Users className="w-3 h-3" />, label: 'user', bgColor: 'bg-purple-100' },
  auth: { icon: <Lock className="w-3 h-3" />, label: 'auth', bgColor: 'bg-green-100' },
  tenant: { icon: <Building2 className="w-3 h-3" />, label: 'tenant', bgColor: 'bg-amber-100' },
  role: { icon: <Shield className="w-3 h-3" />, label: 'role', bgColor: 'bg-pink-100' },
  api_key: { icon: <Zap className="w-3 h-3" />, label: 'api key', bgColor: 'bg-gray-100' },
  analysis: { icon: <BarChart3 className="w-3 h-3" />, label: 'analysis', bgColor: 'bg-emerald-100' },
}

const ACTION_BADGE_CLASS: Record<string, string> = {
  'session.started': 'bg-blue-50 text-blue-700 border-blue-200',
  'session.ended': 'bg-gray-50 text-gray-700 border-gray-200',
  'session.failed': 'bg-amber-50 text-amber-700 border-amber-200',
  'user.created': 'bg-green-50 text-green-700 border-green-200',
  'user.deleted': 'bg-red-50 text-red-700 border-red-200',
  'totp.activated': 'bg-green-50 text-green-700 border-green-200',
  'totp.login_failed': 'bg-amber-50 text-amber-700 border-amber-200',
}

const STATUS_BADGE_CLASS: Record<string, string> = {
  success: 'bg-green-50 text-green-700 border-green-200',
  failure: 'bg-red-50 text-red-700 border-red-200',
}

interface DetailPanelState {
  open: boolean
  log: any | null
}

// CSV Export utility
function generateCSV(logs: AuditLogItem[]): string {
  const headers = [
    'ID',
    'Date/Heure',
    'Action',
    'Ressource',
    'Utilisateur',
    'Email',
    'Statut',
    'IP Address',
    'Raison',
  ]

  const rows = logs.map((log) => [
    log.id,
    new Date(log.timestamp).toLocaleString('fr-FR'),
    getActionLabel(log.action),
    log.resource_type,
    log.user_name || 'système',
    log.user_email || '-',
    log.status === 'success' ? 'Succès' : 'Échec',
    log.ip_address || '-',
    log.reason || '-',
  ])

  // Escape CSV fields and build CSV string
  const csvContent = [
    headers.map((h) => `"${h}"`).join(','),
    ...rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(',')),
  ].join('\n')

  return csvContent
}

interface DetailPanelState {
  open: boolean
  log: any | null
}

export default function AuditLogDashboard() {
  const router = useRouter()
  const { user, isLoading } = useAuth()
  const hasCheckedPermissions = useRef(false)
  
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [action, setAction] = useState<string>('')
  const [resourceType, setResourceType] = useState<string>('')
  const [since, setSince] = useState<string>('')
  const [until, setUntil] = useState<string>('')
  const [search, setSearch] = useState<string>('')
  const [detailPanel, setDetailPanel] = useState<DetailPanelState>({ open: false, log: null })

  const params: GetAuditLogsParams = {
    page,
    pageSize,
    ...(action && { action }),
    ...(resourceType && { resourceType }),
    ...(since && { since }),
    ...(until && { until }),
    ...(search && { search }),
  }

  const { logs, total, totalPages, isLoading: logsLoading, error } = useAuditLogs(params)

  useEffect(() => {
    if (!hasCheckedPermissions.current && !isLoading && user) {
      hasCheckedPermissions.current = true
      const userRole = typeof user.role === 'string' ? user.role : user.role?.name
      const isAdmin = userRole === 'admin' || userRole === 'superadmin' || userRole === 'system_admin'

      if (!isAdmin) {
        router.replace('/dashboard')
      }
    }
  }, [user, isLoading, router])

  const handleFilterChange = () => {
    setPage(1)
  }

  const handleSearch = (query: string) => {
    setSearch(query)
    handleFilterChange()
  }

  const handleDateChange = (type: 'since' | 'until', value: string) => {
    if (type === 'since') setSince(value)
    else setUntil(value)
    handleFilterChange()
  }

  const handleActionChange = (val: string) => {
    setAction(val)
    handleFilterChange()
  }

  const handleResourceTypeChange = (val: string) => {
    setResourceType(val)
    handleFilterChange()
  }

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize)
    setPage(1)
  }

  const handleDownloadCSV = () => {
    const csv = generateCSV(logs)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    const timestamp = new Date().toISOString().split('T')[0]
    link.setAttribute('href', url)
    link.setAttribute('download', `audit-logs-${timestamp}.csv`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const stats = {
    total,
    success: logs.filter((l) => l.status === 'success').length,
    failed: logs.filter((l) => l.status === 'failure').length,
    today: logs.filter((l) => {
      const logDate = new Date(l.timestamp).toDateString()
      return logDate === new Date().toDateString()
    }).length,
  }

  const userRole = typeof user?.role === 'string' ? user?.role : user?.role?.name
  const isAdmin = userRole === 'admin' || userRole === 'superadmin' || userRole === 'system_admin'

  if (isLoading || (user && !isAdmin)) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600 mb-4"></div>
          <p className="text-gray-600 text-sm">Vérification des permissions...</p>
        </div>
      </div>
    )
  }

  if (!isAdmin) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-700 max-w-md text-center">
          <AlertCircle className="w-6 h-6 mx-auto mb-2" />
          <p className="font-semibold mb-1">Accès refusé</p>
          <p className="text-sm">Seuls les administrateurs peuvent accéder à cette page.</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-700 max-w-md">
          <AlertCircle className="w-6 h-6 mb-2" />
          <p className="font-semibold mb-1">Erreur de chargement</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-gray-900">Journal d'audit</h1>
          <p className="text-sm text-gray-600 mt-1">Suivi immuable des actions et modifications système</p>
        </div>
        <button
          onClick={handleDownloadCSV}
          disabled={logs.length === 0}
          className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 16v-4m0 0V8m0 4l-4-4m4 4l4-4M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Exporter CSV
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total" value={total} icon={<BarChart3 className="w-4 h-4" />} />
        <StatCard label="Succès" value={stats.success} icon={<CheckCircle2 className="w-4 h-4 text-green-600" />} />
        <StatCard label="Erreurs (page)" value={stats.failed} icon={<AlertCircle className="w-4 h-4 text-red-600" />} />
        <StatCard label="Aujourd'hui" value={stats.today} icon={<Clock className="w-4 h-4" />} />
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <div className="relative md:col-span-2">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher..."
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
          </div>

          <select
            value={action}
            onChange={(e) => handleActionChange(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
          >
            <option value="">Tous les actions</option>
            {Object.entries(ACTION_LABELS).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>

          <select
            value={resourceType}
            onChange={(e) => handleResourceTypeChange(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
          >
            <option value="">Tous les ressources</option>
            {Object.entries(RESOURCE_META).map(([key, meta]) => (
              <option key={key} value={key}>
                {meta.label}
              </option>
            ))}
          </select>

          <select
            value={pageSize}
            onChange={(e) => handlePageSizeChange(Number(e.target.value))}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
          >
            <option value="10">10 / page</option>
            <option value="20">20 / page</option>
            <option value="50">50 / page</option>
            <option value="100">100 / page</option>
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-600 mb-1 font-medium">Depuis</label>
            <input
              type="date"
              value={since}
              onChange={(e) => handleDateChange('since', e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1 font-medium">Jusqu'au</label>
            <input
              type="date"
              value={until}
              onChange={(e) => handleDateChange('until', e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setPage(1)
                setPageSize(20)
                setAction('')
                setResourceType('')
                setSince('')
                setUntil('')
                setSearch('')
              }}
              className="w-full px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
            >
              Réinitialiser
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-4 py-3 text-left font-medium text-gray-600 text-xs uppercase tracking-wider">
                  ID
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600 text-xs uppercase tracking-wider">
                  Utilisateur
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600 text-xs uppercase tracking-wider">
                  Action
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600 text-xs uppercase tracking-wider">
                  Ressource
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600 text-xs uppercase tracking-wider">
                  Statut
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600 text-xs uppercase tracking-wider">
                  IP
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600 text-xs uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              {logsLoading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    <div className="flex items-center justify-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-amber-600"></div>
                      Chargement...
                    </div>
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    Aucun enregistrement d'audit trouvé
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr
                    key={log.id}
                    onClick={() => setDetailPanel({ open: true, log })}
                    className="border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 text-gray-900 font-mono text-xs">{String(log.id).slice(0, 8)}</td>
                    <td className="px-4 py-3">
                      {log.user_email ? (
                        <span className="text-gray-900 text-xs">{log.user_email}</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                          <Zap className="w-3 h-3" />
                          System
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${
                          ACTION_BADGE_CLASS[log.action] || 'bg-gray-50 text-gray-700 border-gray-200'
                        }`}
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                        {getActionLabel(log.action)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-5 h-5 rounded flex items-center justify-center text-gray-700 ${
                            RESOURCE_META[log.resource_type]?.bgColor || 'bg-gray-100'
                          }`}
                        >
                          {RESOURCE_META[log.resource_type]?.icon}
                        </div>
                        <span className="text-gray-900 text-xs">
                          {RESOURCE_META[log.resource_type]?.label || log.resource_type}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${
                          STATUS_BADGE_CLASS[log.status] || 'bg-gray-50 text-gray-700 border-gray-200'
                        }`}
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 font-mono text-xs">
                      {log.ip_address || '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(log.timestamp).toLocaleString('fr-FR')}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between text-xs text-gray-600">
          <span>
            Page {page} de {totalPages} • {total} enregistrements au total
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="w-7 h-7 flex items-center justify-center rounded border border-gray-200 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const pageNum = i + 1
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`w-7 h-7 flex items-center justify-center rounded text-xs font-medium ${
                    pageNum === page
                      ? 'bg-gray-900 text-white border border-gray-900'
                      : 'border border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {pageNum}
                </button>
              )
            })}
            {totalPages > 5 && <span className="px-2 py-1">...</span>}
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="w-7 h-7 flex items-center justify-center rounded border border-gray-200 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {detailPanel.open && detailPanel.log && (
        <DetailPanel log={detailPanel.log} onClose={() => setDetailPanel({ open: false, log: null })} />
      )}
    </div>
  )
}

function StatCard({ label, value, icon }: { label: string; value: number; icon?: React.ReactNode }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-start justify-between">
      <div>
        <p className="text-xs text-gray-600 font-medium mb-2">{label}</p>
        <p className="text-3xl font-bold text-gray-900">{value}</p>
      </div>
      {icon && <div className="text-gray-400">{icon}</div>}
    </div>
  )
}

function DetailPanel({ log, onClose }: { log: AuditLogItem; onClose: () => void }) {
  const resourceMeta = RESOURCE_META[log.resource_type] || { label: log.resource_type }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end z-50">
      <div className="bg-white w-full md:w-2/3 lg:w-1/2 max-h-[90vh] overflow-y-auto rounded-t-lg md:rounded-lg shadow-lg">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">
            Événement {log.id} — {log.action.replace(/_/g, ' ')} · {resourceMeta.label}
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {!log.user_id && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 flex gap-3">
              <Zap className="w-5 h-5 text-purple-700 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-purple-900 text-sm">Événement système</p>
                <p className="text-purple-800 text-xs mt-1">
                  Cet événement a été généré par le système (APScheduler, pipeline de traitement,
                  etc.), pas par une action utilisateur.
                </p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-6">
            <DetailItem label="ID" value={String(log.id)} />
            <DetailItem label="Tenant ID" value={log.tenant_id.slice(0, 12)} />
            <DetailItem label="Action" value={log.action.replace(/_/g, ' ')} />
            <DetailItem label="Statut" value={log.status} isStatus={true} />
            <DetailItem label="Ressource" value={log.resource_type.replace(/_/g, ' ')} />
            <DetailItem label="Resource ID" value={log.resource_id?.slice(0, 12) || '—'} />
            <DetailItem label="Utilisateur" value={log.user_email || log.user_name || 'système'} />
            <DetailItem label="Date/Heure" value={new Date(log.timestamp).toLocaleString('fr-FR')} />
            <DetailItem label="IP Address" value={log.ip_address || '—'} />
            <DetailItem label="User Agent" value={log.user_agent?.substring(0, 30) || '—'} />
          </div>

          {log.reason && (
            <div>
              <p className="text-xs font-medium text-gray-600 mb-2 uppercase tracking-wider">
                Raison
              </p>
              <div className="bg-gray-50 border border-gray-200 rounded p-3 font-mono text-xs text-gray-700">
                {log.reason}
              </div>
            </div>
          )}

          {log.old_value && (
            <div>
              <p className="text-xs font-medium text-gray-600 mb-2 uppercase tracking-wider">
                Ancienne valeur
              </p>
              <div className="bg-gray-50 border border-gray-200 rounded p-3 font-mono text-xs text-gray-600 overflow-x-auto">
                <pre>{JSON.stringify(log.old_value, null, 2)}</pre>
              </div>
            </div>
          )}

          {log.new_value && (
            <div>
              <p className="text-xs font-medium text-gray-600 mb-2 uppercase tracking-wider">
                Nouvelle valeur
              </p>
              <div className="bg-gray-50 border border-gray-200 rounded p-3 font-mono text-xs text-gray-600 overflow-x-auto">
                <pre>{JSON.stringify(log.new_value, null, 2)}</pre>
              </div>
            </div>
          )}

          {log.hash && (
            <div>
              <p className="text-xs font-medium text-gray-600 mb-2 uppercase tracking-wider">
                Hash (chaîne d'intégrité)
              </p>
              <div className="bg-gray-50 border border-gray-200 rounded p-3 font-mono text-xs text-gray-600 break-all">
                {log.hash}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function DetailItem({ label, value, isStatus }: { label: string; value: string; isStatus?: boolean }) {
  return (
    <div>
      <p className="text-xs text-gray-600 mb-1 font-medium">{label}</p>
      {isStatus ? (
        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${
          value === 'success'
            ? 'bg-green-50 text-green-700 border-green-200'
            : 'bg-red-50 text-red-700 border-red-200'
        }`}>
          <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
          {value}
        </span>
      ) : (
        <p className="text-sm text-gray-900 font-mono break-all">{value}</p>
      )}
    </div>
  )
}
