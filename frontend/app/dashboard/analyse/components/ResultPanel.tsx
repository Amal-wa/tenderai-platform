'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Copy, Download, AlertTriangle, CheckCircle2 } from 'lucide-react'
import type { AnalyseResult } from '@/types/analyse'

interface ResultPanelProps {
  result: AnalyseResult | null
  loading: boolean
  onExport: () => void
  canExport: boolean
}

export default function ResultPanel({ result, loading, onExport, canExport }: ResultPanelProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    if (!result?.reponse_generee) return

    setDisplayedText('')
    setIsTyping(true)
    let index = 0
    const text = result.reponse_generee

    const interval = setInterval(() => {
      if (index <= text.length) {
        setDisplayedText(text.slice(0, index))
        index++
      } else {
        setIsTyping(false)
        clearInterval(interval)
      }
    }, 16)

    return () => clearInterval(interval)
  }, [result?.reponse_generee])

  const getScoreColor = (score: number) => {
    if (score >= 75) return { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Bon' }
    if (score >= 50) return { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Moyen' }
    return { bg: 'bg-red-100', text: 'text-red-700', label: 'Faible' }
  }

  const handleCopy = async () => {
    if (result?.reponse_generee) {
      await navigator.clipboard.writeText(result.reponse_generee).catch(() => {})
    }
  }

  if (loading) {
    const steps = [
      'Extraction du texte (OCR)…',
      'Analyse sémantique NER…',
      'Vérification conformité réglementaire…',
      'Génération de la réponse IA…',
    ]

    return (
      <div className="bg-white border border-gray-200 rounded-2xl p-4.5 flex flex-col h-full">
        <div className="flex-1 flex flex-col items-center justify-center gap-6 py-8">
          <div className="space-y-3 w-full max-w-xs">
            {steps.map((step, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0.4 }}
                animate={{ opacity: 1 }}
                transition={{ delay: idx * 0.2, duration: 0.5 }}
                className="flex items-center gap-2 text-sm"
              >
                <motion.div
                  className="w-2 h-2 rounded-full bg-amber-500"
                  animate={idx === 0 ? { scale: [1, 1.5, 1] } : {}}
                  transition={{ duration: 1, repeat: Infinity }}
                />
                <span className="text-gray-700 font-medium">{step}</span>
              </motion.div>
            ))}
          </div>
          <div className="w-full max-w-xs h-1 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-amber-500"
              initial={{ width: '0%' }}
              animate={{ width: '100%' }}
              transition={{ duration: 3, ease: 'easeInOut' }}
            />
          </div>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="bg-white border border-gray-200 rounded-2xl p-4.5 flex flex-col h-full">
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', textAlign: 'center', padding: 40, gap: 12 }}>
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="#0F1C35" strokeWidth="1.2" opacity={0.15}>
            <path d="M24 3l6 12h12l-9 8 3 12-12-7-12 7 3-12-9-8h12z" />
          </svg>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#6B6560' }}>
            Prêt pour l'analyse
          </div>
          <div style={{ fontSize: 11, color: '#6B6560', opacity: 0.7 }}>
            Sélectionnez un document et configurez votre analyse
          </div>
        </div>
      </div>
    )
  }

  const conformColor = getScoreColor(result.score_conformite)
  const techColor = getScoreColor(result.score_technique)
  const riskColor = getScoreColor(100 - result.score_risque)

  return (
    <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        <div className="p-4.5 space-y-3">
          <div className="flex gap-2">
            <div className={`flex-1 ${conformColor.bg} ${conformColor.text} rounded-lg p-3 text-center`}>
              <div className="font-mono text-xl font-bold">{result.score_conformite}%</div>
              <div className="text-xs font-medium mt-1">Conformité</div>
            </div>
            <div className={`flex-1 ${techColor.bg} ${techColor.text} rounded-lg p-3 text-center`}>
              <div className="font-mono text-xl font-bold">{result.score_technique}%</div>
              <div className="text-xs font-medium mt-1">Technique</div>
            </div>
            <div className={`flex-1 ${riskColor.bg} ${riskColor.text} rounded-lg p-3 text-center`}>
              <div className="font-mono text-xl font-bold">{100 - result.score_risque}%</div>
              <div className="text-xs font-medium mt-1">Faible risque</div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs font-bold text-gray-900 uppercase tracking-widest mb-2">Résumé</div>
            <div className="text-sm text-gray-700 leading-relaxed">{result.resume}</div>
          </div>

          {result.criteres_manquants?.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-2">
                <AlertTriangle size={14} className="text-amber-600" />
                <div className="text-xs font-bold text-gray-900 uppercase tracking-widest">Critères manquants</div>
              </div>
              <ul className="space-y-1.5">
                {result.criteres_manquants.map((criteria, idx) => (
                  <li key={idx} className="flex gap-2 text-sm text-gray-700">
                    <span className="text-amber-600 font-bold">•</span>
                    <span>{criteria}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.risques?.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-2">
                <AlertTriangle size={14} className="text-red-600" />
                <div className="text-xs font-bold text-gray-900 uppercase tracking-widest">Risques identifiés</div>
              </div>
              <ul className="space-y-1.5">
                {result.risques.map((risk, idx) => (
                  <li key={idx} className="flex gap-2 text-sm text-gray-700">
                    <span className="text-red-600 font-bold">•</span>
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs font-bold text-gray-900 uppercase tracking-widest mb-2">Réponse générée</div>
            <div className="text-sm text-gray-700 leading-relaxed">
              {displayedText}
              {isTyping && <span className="w-0.5 h-4 bg-amber-500 animate-pulse inline-block ml-1" />}
            </div>
          </div>

          {result.recommandations?.length > 0 && (
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-2">
                <CheckCircle2 size={14} className="text-emerald-600" />
                <div className="text-xs font-bold text-gray-900 uppercase tracking-widest">Recommandations</div>
              </div>
              <ul className="space-y-1.5">
                {result.recommandations.map((rec, idx) => (
                  <li key={idx} className="flex gap-2 text-sm text-gray-700">
                    <span className="text-emerald-600 font-bold">✓</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      <div className="flex gap-2 p-3.5 border-t border-gray-200 bg-gray-50 flex-shrink-0">
        <button
          onClick={handleCopy}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 border border-gray-300 bg-white text-gray-900 rounded-lg text-xs font-semibold hover:bg-gray-50 transition-all"
        >
          <Copy size={14} />
          Copier la réponse
        </button>
        <button
          onClick={onExport}
          disabled={!canExport}
          className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
            canExport
              ? 'bg-gray-900 text-white hover:bg-gray-800'
              : 'bg-gray-300 text-gray-600 cursor-not-allowed opacity-50'
          }`}
        >
          <Download size={14} />
          Exporter PDF
        </button>
      </div>
    </div>
  )
}
