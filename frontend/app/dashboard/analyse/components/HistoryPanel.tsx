'use client'

import { Clock } from 'lucide-react'
import type { AnalyseHistoryItem } from '@/types/analyse'

interface HistoryPanelProps {
  history: AnalyseHistoryItem[]
  onSelectItem: (item: AnalyseHistoryItem) => void
  loading: boolean
}

export default function HistoryPanel({ history, onSelectItem, loading }: HistoryPanelProps) {
  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-emerald-700 bg-emerald-100'
    if (score >= 50) return 'text-amber-700 bg-amber-100'
    return 'text-red-700 bg-red-100'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-xs text-gray-500">Chargement...</div>
      </div>
    )
  }

  if (!history || history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center px-4">
        <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center mb-3 opacity-30">
          <Clock size={20} className="text-gray-600" />
        </div>
        <div className="text-xs text-gray-600 font-medium">Aucune analyse enregistrée</div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {history.slice(0, 10).map((item) => {
        const date = new Date(item.created_at)
        const formattedDate = date.toLocaleDateString('fr-FR', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
        })
        const formattedTime = date.toLocaleTimeString('fr-FR', {
          hour: '2-digit',
          minute: '2-digit',
        })

        return (
          <button
            key={item.id}
            onClick={() => onSelectItem(item)}
            className="w-full text-left bg-gray-50 border border-gray-200 rounded-lg p-3 hover:border-amber-500 hover:bg-amber-50 transition-all cursor-pointer"
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="text-xs font-semibold text-gray-900 truncate flex-1 mr-2">{item.file_name}</div>
              <div className="text-xs font-mono text-gray-600 flex-shrink-0">
                {formattedDate} {formattedTime}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={`text-xs font-bold px-2 py-1 rounded-lg ${getScoreColor(item.score_conformite)}`}>
                {item.score_conformite}%
              </div>
              <div className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-lg font-semibold">{item.type}</div>
              <div className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-lg font-mono font-medium ml-auto">
                {item.lang}
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}
