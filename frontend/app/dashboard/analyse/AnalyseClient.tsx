'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { v4 as uuidv4 } from 'uuid'
import { useAuth } from '@/context/AuthContext'
import { extractErrorMessage } from '@/lib/api'
import { useAnalyse } from '@/hooks/useAnalyse'
import KpiStrip from './components/KpiStrip'
import SourceSelector from './components/SourceSelector'
import ConfigPanel from './components/ConfigPanel'
import ResultPanel from './components/ResultPanel'
import HistoryPanel from './components/HistoryPanel'
import type { AnalyseStats, AnalyseRequest, AnalyseResult, AnalyseHistoryItem } from '@/types/analyse'
import type { TenderDocument } from '@/types/documents'

export default function AnalyseClient() {
  const router = useRouter()
  const { user } = useAuth()
  const {
    fetchStats,
    fetchTenders,
    runAnalyse,
    fetchHistory,
    fetchAnalyseById,
    exportAnalyse,
    uploadDocument,
  } = useAnalyse()

  // Data state
  const [stats, setStats] = useState<AnalyseStats | null>(null)
  const [tenders, setTenders] = useState<TenderDocument[] | null>(null)
  const [history, setHistory] = useState<AnalyseHistoryItem[]>([])

  // UI state
  const [sourceMode, setSourceMode] = useState<'ao' | 'annexe'>('ao')
  const [selectedAO, setSelectedAO] = useState('')
  const [annexeFile, setAnnexeFile] = useState<File | null>(null)
  const [activeTab, setActiveTab] = useState<'result' | 'history'>('result')

  // Analysis state
  const [config, setConfig] = useState<AnalyseRequest>({
    type: 'conformite',
    lang: 'FR',
    scope: ['criteres', 'risques', 'reponse', 'score'],
    detail: 'synthese',
  })
  const [result, setResult] = useState<AnalyseResult | null>(null)

  // Loading state
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false) // FIX: déclaré
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return
    const userRole = typeof user.role === 'string' ? user.role : user.role?.name
    if (!['superadmin', 'admin', 'manager', 'analyst'].includes(userRole || '')) {
      router.push('/errors/403')
    }
  }, [user, router])

  // Initial data load
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true)
        const [statsData, tendersData] = await Promise.all([fetchStats(), fetchTenders()])
        if (statsData) setStats(statsData)
        if (tendersData?.items) setTenders(tendersData.items)

        setHistoryLoading(true)
        const historyData = await fetchHistory()
        if (historyData) setHistory(historyData)
      } catch (err) {
        setError(extractErrorMessage(err))
      } finally {
        setLoading(false)
        setHistoryLoading(false)
      }
    }
    loadInitialData()
  }, [fetchStats, fetchTenders, fetchHistory])

  const canAnalyze = sourceMode === 'ao' ? !!selectedAO : !!annexeFile

  const handleAnalyze = async () => {
    if (!canAnalyze || analyzing) return
    try {
      setAnalyzing(true)
      setError(null)

      const payload: AnalyseRequest = { ...config }

      if (sourceMode === 'annexe' && annexeFile) {
        // FIX: uuidv4() généré ici par upload, pas au niveau module
        const uploadResult = await uploadDocument(annexeFile, uuidv4())
        if (!uploadResult?.document_url) {
          throw new Error("Échec de l'upload du document")
        }
        payload.document_url = uploadResult.document_url
      } else if (sourceMode === 'ao' && selectedAO) {
        payload.tender_id = selectedAO
      }

      const analyseResult = await runAnalyse(payload)
      if (analyseResult) {
        setResult(analyseResult)
        setActiveTab('result')

        const newHistoryItem: AnalyseHistoryItem = {
          id: analyseResult.id,
          file_name:
            sourceMode === 'ao'
              ? (tenders?.find((t) => t.id === selectedAO)?.filename ?? "Appel d'offres")
              : (annexeFile?.name ?? 'Document'),
          created_at: analyseResult.created_at,
          type: config.type,
          score_conformite: analyseResult.score_conformite,
          lang: config.lang,
        }
        setHistory((prev) => [newHistoryItem, ...prev])
      }
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setAnalyzing(false)
    }
  }

  const handleHistoryItemSelect = async (item: AnalyseHistoryItem) => {
    try {
      setAnalyzing(true)
      const analyseResult = await fetchAnalyseById(item.id)
      if (analyseResult) {
        setResult(analyseResult)
        setActiveTab('result')
      }
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setAnalyzing(false)
    }
  }

  const handleExport = async () => {
    if (result?.id) await exportAnalyse(result.id)
  }

  const userRole = typeof user?.role === 'string' ? user.role : user?.role?.name
  const canExport = !!result && ['superadmin', 'admin', 'manager', 'analyst'].includes(userRole ?? '')

  return (
    <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#F5F0E8' }}>
      {/* Topbar */}
      <div className="flex items-center justify-between px-6 py-3.5 bg-white border-b border-gray-200 flex-shrink-0">
        <div>
          <div className="text-xs text-gray-600">Mon espace · Analyse IA</div>
          <h1 className="text-lg font-bold text-gray-900 mt-0.5">Analyse IA — Appels d'offres</h1>
        </div>
        <button
          onClick={handleExport}
          disabled={!canExport}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
            canExport
              ? 'bg-[var(--navy)] text-white hover:bg-[var(--navy2)]'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed opacity-50'
          }`}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M7 1v8M4 6l3 3 3-3" />
            <path d="M1 11v1a1 1 0 001 1h10a1 1 0 001-1v-1" />
          </svg>
          Exporter PDF
        </button>
      </div>

      {/* KPI Strip */}
      {!loading && <KpiStrip stats={stats} />}

      {/* Content */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-4 p-6">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-700 font-medium">
            {error}
          </div>
        )}

        {/* Source Selector */}
        <SourceSelector
          sourceMode={sourceMode}
          onSourceChange={setSourceMode}
          selectedAO={selectedAO}
          onAOChange={setSelectedAO}
          tenders={tenders}
          annexeFile={annexeFile}
          onAnnexeSelect={setAnnexeFile}
          onAnnexeRemove={() => setAnnexeFile(null)}
        />

        {/* Split panels */}
        <div className="flex-1 grid grid-cols-[380px_1fr] gap-4 min-h-0">
          {/* Left: Config */}
          <ConfigPanel
            config={config}
            onConfigChange={(updates) => setConfig((prev) => ({ ...prev, ...updates }))}
            canAnalyze={canAnalyze}
            isLoading={analyzing}
            onAnalyze={handleAnalyze}
          />

          {/* Right: Results / History */}
          <div className="bg-white border border-[var(--border)] rounded-2xl overflow-hidden flex flex-col">
            {/* Tabs */}
            <div className="flex border-b border-[var(--border)] flex-shrink-0">
              {(['result', 'history'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`relative flex-1 px-4 py-3 text-xs font-semibold transition-all ${
                    activeTab === tab
                      ? 'text-[var(--amber)] border-b-2 border-[var(--amber)] bg-white'
                      : 'text-[var(--muted)] hover:text-[var(--navy)]'
                  }`}
                >
                  {tab === 'result' ? 'Résultat actuel' : 'Historique'}
                  {tab === 'history' && history.length > 0 && (
                    <span className="ml-2 bg-[var(--amber-soft)] text-[var(--amber)] text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                      {history.length}
                    </span>
                  )}
                </button>
              ))}
            </div>

            {/* Panel body */}
            <div className="flex-1 overflow-y-auto p-4">
              {activeTab === 'result' ? (
                <ResultPanel
                  result={result}
                  loading={analyzing}
                  onExport={handleExport}
                  canExport={canExport}
                />
              ) : (
                <HistoryPanel
                  history={history}
                  onSelectItem={handleHistoryItemSelect}
                  loading={historyLoading}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}