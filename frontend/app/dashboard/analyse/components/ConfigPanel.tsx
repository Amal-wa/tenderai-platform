'use client'

import { Sparkles } from 'lucide-react'
import type { AnalyseRequest } from '@/types/analyse'

interface ConfigPanelProps {
  config: AnalyseRequest
  onConfigChange: (updates: Partial<AnalyseRequest>) => void
  canAnalyze: boolean
  isLoading: boolean
  onAnalyze: () => void
}

export default function ConfigPanel({
  config,
  onConfigChange,
  canAnalyze,
  isLoading,
  onAnalyze,
}: ConfigPanelProps) {
  const handleTypeSelect = (type: AnalyseRequest['type']) => {
    onConfigChange({ type })
  }

  const handleLangSelect = (lang: AnalyseRequest['lang']) => {
    onConfigChange({ lang })
  }

  const handleScopeToggle = (scope: AnalyseRequest['scope'][number]) => {
    const newScope = config.scope.includes(scope)
      ? config.scope.filter((s) => s !== scope)
      : [...config.scope, scope]
    onConfigChange({ scope: newScope })
  }

  const handleDetailSelect = (detail: AnalyseRequest['detail']) => {
    onConfigChange({ detail })
  }

  const types: Array<{ label: string; value: AnalyseRequest['type'] }> = [
    { label: 'Conformité', value: 'conformite' },
    { label: 'Technique', value: 'technique' },
    { label: 'Financier', value: 'financier' },
    { label: 'Complet', value: 'complet' },
  ]

  const languages: Array<{ label: string; value: AnalyseRequest['lang'] }> = [
    { label: 'FR', value: 'FR' },
    { label: 'AR', value: 'AR' },
    { label: 'EN', value: 'EN' },
  ]

  const scopes: Array<{ label: string; value: AnalyseRequest['scope'][number] }> = [
    { label: 'Critères manquants', value: 'criteres' },
    { label: 'Risques', value: 'risques' },
    { label: 'Génération réponse', value: 'reponse' },
    { label: 'Score conformité', value: 'score' },
  ]

  const details: Array<{ label: string; value: AnalyseRequest['detail'] }> = [
    { label: 'Synthèse', value: 'synthese' },
    { label: 'Approfondi', value: 'approfondi' },
  ]

  return (
    <div style={{ background: '#fff', border: '1px solid #E8E4DF', borderRadius: 14, padding: '16px 20px', display: 'flex', flexDirection: 'column' }} className="h-full">
      <div className="flex items-center gap-2 pb-3.5 border-b border-gray-200 mb-4 flex-shrink-0">
        <div className="w-7 h-7 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <Sparkles size={14} />
        </div>
        <div>
          <div className="text-xs font-bold text-gray-900">Configuration</div>
          <div className="text-xs text-gray-600 mt-0.5">Personnalisez l'analyse</div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#6B6560', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8, marginTop: 16 }}>Type d'analyse</div>
          <div className="grid grid-cols-2 gap-1.5">
            {types.map((type) => (
              <button
                key={type.value}
                onClick={() => handleTypeSelect(type.value)}
                style={{
                  padding: '8px 12px',
                  borderRadius: 8,
                  fontSize: 12,
                  fontWeight: 600,
                  border: config.type === type.value ? 'none' : '1px solid #E8E4DF',
                  background: config.type === type.value ? 'rgba(196,150,42,0.12)' : '#fff',
                  color: config.type === type.value ? '#C4962A' : '#6B6560',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  textAlign: 'center',
                  width: '100%',
                }}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#6B6560', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8, marginTop: 16 }}>Langue</div>
          <div className="grid grid-cols-3 gap-1.5">
            {languages.map((lang) => (
              <button
                key={lang.value}
                onClick={() => handleLangSelect(lang.value)}
                style={{
                  padding: '8px 12px',
                  borderRadius: 8,
                  fontSize: 12,
                  fontWeight: 600,
                  border: config.lang === lang.value ? 'none' : '1px solid #E8E4DF',
                  background: config.lang === lang.value ? 'rgba(196,150,42,0.12)' : '#fff',
                  color: config.lang === lang.value ? '#C4962A' : '#6B6560',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  textAlign: 'center',
                  width: '100%',
                }}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#6B6560', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8, marginTop: 16 }}>Périmètre</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {scopes.map((scope) => (
              <button
                key={scope.value}
                onClick={() => handleScopeToggle(scope.value)}
                style={{
                  padding: '8px 12px',
                  borderRadius: 8,
                  fontSize: 12,
                  fontWeight: config.scope.includes(scope.value) ? 600 : 500,
                  border: config.scope.includes(scope.value) ? '1px solid #C4962A' : '1px solid #E8E4DF',
                  background: config.scope.includes(scope.value) ? 'rgba(196,150,42,0.12)' : '#fff',
                  color: config.scope.includes(scope.value) ? '#C4962A' : '#6B6560',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  textAlign: 'center',
                  width: '100%',
                }}
              >
                {scope.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#6B6560', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8, marginTop: 16 }}>Niveau de détail</div>
          <div className="grid grid-cols-2 gap-1.5">
            {details.map((detail) => (
              <button
                key={detail.value}
                onClick={() => handleDetailSelect(detail.value)}
                style={{
                  padding: '8px 12px',
                  borderRadius: 8,
                  fontSize: 12,
                  fontWeight: 600,
                  border: config.detail === detail.value ? 'none' : '1px solid #E8E4DF',
                  background: config.detail === detail.value ? 'rgba(196,150,42,0.12)' : '#fff',
                  color: config.detail === detail.value ? '#C4962A' : '#6B6560',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  textAlign: 'center',
                  width: '100%',
                }}
              >
                {detail.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <button
        onClick={onAnalyze}
        disabled={!canAnalyze || isLoading}
        style={{
          width: '100%',
          marginTop: 20,
          padding: '12px',
          background: isLoading ? '#C4962A' : (!canAnalyze ? 'rgba(15,28,53,0.3)' : '#0F1C35'),
          color: '#fff',
          border: 'none',
          borderRadius: 10,
          fontSize: 13,
          fontWeight: 700,
          cursor: canAnalyze && !isLoading ? 'pointer' : 'not-allowed',
          transition: 'all 0.2s',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          opacity: !canAnalyze && !isLoading ? 0.5 : 1,
        }}
      >
        {isLoading ? (
          <>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ animation: 'spin 1s linear infinite' }}>
              <path d="M7 1a6 6 0 1 1 0 12A6 6 0 0 1 7 1" strokeOpacity="0.3" />
              <path d="M7 1a6 6 0 0 1 6 6" />
            </svg>
            Analyse en cours...
          </>
        ) : (
          <>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M7 1l1.5 4H13l-3.5 2.5 1.5 4L7 9.5 3 11.5l1.5-4L1 5h4.5z" />
            </svg>
            Lancer l'analyse IA
          </>
        )}
      </button>
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
