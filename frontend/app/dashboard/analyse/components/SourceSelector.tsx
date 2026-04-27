'use client'

import { Upload, FileText } from 'lucide-react'
import type { TenderDocument } from '@/types/documents'

interface SourceSelectorProps {
  sourceMode: 'ao' | 'annexe'
  onSourceChange: (mode: 'ao' | 'annexe') => void
  selectedAO: string
  onAOChange: (tenerId: string) => void
  tenders: TenderDocument[] | null
  annexeFile: File | null
  onAnnexeSelect: (file: File) => void
  onAnnexeRemove: () => void
}

export default function SourceSelector({
  sourceMode,
  onSourceChange,
  selectedAO,
  onAOChange,
  tenders,
  annexeFile,
  onAnnexeSelect,
  onAnnexeRemove,
}: SourceSelectorProps) {
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      onAnnexeSelect(e.target.files[0])
    }
  }

  return (
    <div style={{ background: '#fff', border: '1px solid #E8E4DF', borderRadius: 12, padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 12 }} className="flex-shrink-0">
      <span style={{ fontSize: 11, fontWeight: 700, color: '#6B6560', letterSpacing: '0.08em', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
        Source
      </span>

      <div style={{ display: 'flex', gap: 6 }}>
        <button
          onClick={() => onSourceChange('ao')}
          style={{
            padding: '6px 14px',
            borderRadius: 7,
            fontSize: 12,
            fontWeight: 600,
            border: sourceMode === 'ao' ? 'none' : '1px solid #E8E4DF',
            background: sourceMode === 'ao' ? '#0F1C35' : '#F5F0E8',
            color: sourceMode === 'ao' ? '#fff' : '#6B6560',
            cursor: 'pointer',
            transition: 'all 0.15s',
          }}
        >
          AO existant
        </button>
        <button
          onClick={() => onSourceChange('annexe')}
          style={{
            padding: '6px 14px',
            borderRadius: 7,
            fontSize: 12,
            fontWeight: 600,
            border: sourceMode === 'annexe' ? 'none' : '1px solid #E8E4DF',
            background: sourceMode === 'annexe' ? '#0F1C35' : '#F5F0E8',
            color: sourceMode === 'annexe' ? '#fff' : '#6B6560',
            cursor: 'pointer',
            transition: 'all 0.15s',
          }}
        >
          Document annexe
        </button>
      </div>

      {sourceMode === 'ao' && (
        <select
          value={selectedAO}
          onChange={(e) => onAOChange(e.target.value)}
          className="flex-1 max-w-xs border border-gray-200 rounded-lg px-3 py-1.5 text-xs font-medium text-gray-900 bg-gray-50 cursor-pointer outline-none focus:border-amber-500"
        >
          <option value="">Sélectionner un AO...</option>
          {tenders?.map((tender) => (
            <option key={tender.id} value={tender.id}>
              {tender.filename}
            </option>
          ))}
        </select>
      )}

      {sourceMode === 'annexe' && (
        <>
          <input
            type="file"
            id="annexeFileInput"
            onChange={handleFileSelect}
            accept=".pdf,.docx,.doc,.jpg,.jpeg,.png"
            style={{ display: 'none' }}
          />
          {!annexeFile ? (
            <label
              htmlFor="annexeFileInput"
              className="flex items-center gap-2 px-3 py-1.5 border border-gray-200 rounded-lg text-xs text-gray-600 cursor-pointer hover:border-amber-500 hover:text-amber-600 transition-all bg-gray-50"
            >
              <Upload size={14} />
              <span className="font-medium">Sélectionner fichier</span>
            </label>
          ) : (
            <div className="flex items-center gap-2 px-3 py-1.5 text-xs text-emerald-700 bg-emerald-50 rounded-lg">
              <FileText size={14} />
              <span className="font-medium">{annexeFile.name}</span>
              <button
                onClick={onAnnexeRemove}
                className="ml-2 text-emerald-600 hover:text-emerald-800"
                aria-label="Remove file"
              >
                ✕
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
