'use client'
import { Bell, Download, ChevronDown } from 'lucide-react'

export default function Topbar(): React.ReactElement {
  return (
    <header className="h-[58px] bg-white border-b border-[var(--cream-3)] px-8 sticky top-0 z-20 flex items-center justify-between">
      {/* Left */}
      <div>
        <p className="text-[11px] text-[var(--text-4)] font-medium">
          Mon espace · Analyse IA
        </p>
        <h1 className="font-heading text-[18px] font-bold text-[var(--navy)]">
          Vue d'ensemble
        </h1>
      </div>

      {/* Right */}
      <div className="flex items-center gap-4">
        {/* Period Selector */}
        <button
          className="flex items-center gap-1.5 px-3 py-1.5 border border-[var(--cream-3)] bg-white hover:bg-[var(--cream)] rounded-lg transition-colors"
          aria-label="Changer la période"
        >
          <span className="text-xs font-semibold text-[var(--navy)]">T1 2026</span>
          <ChevronDown size={14} className="text-[var(--text-3)]" />
        </button>

        {/* Export Button */}
        <button className="flex items-center gap-2 px-4 py-2 bg-[var(--navy)] text-white font-heading text-xs font-semibold rounded-lg hover:bg-[var(--navy-2)] transition-colors">
          <Download size={14} />
          Exporter
        </button>

        {/* Notifications */}
        <button
          className="relative flex items-center justify-center w-10 h-10 hover:bg-[var(--cream)] rounded-lg transition-colors"
          aria-label="Notifications"
        >
          <Bell size={18} className="text-[var(--text-3)]" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[var(--danger)] border-2 border-white" />
        </button>
      </div>
    </header>
  )
}
