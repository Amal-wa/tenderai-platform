import { motion } from 'framer-motion'
import { Search, Bell, Command } from 'lucide-react'

export default function Topbar() {
  const today = new Date()
  const dateStr = today.toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })

  return (
    <header className="sticky top-0 z-10 h-12 bg-white/95 backdrop-blur-sm
      border-b border-black/[0.06] flex items-center px-6 gap-4">
      {/* Breadcrumb */}
      <span className="text-[13px] font-semibold text-navy">Tableau de bord</span>
      <div className="w-px h-4 bg-black/10" />

      {/* Search */}
      <div className="relative w-60">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-black/30" />
        <input
          type="text"
          placeholder="Rechercher un AO..."
          className="w-full h-8 pl-9 pr-14 rounded-lg border border-black/10 bg-black/[0.02]
            font-sans text-[12px] text-navy placeholder:text-black/30
            focus:outline-none focus:border-gold focus:ring-2 focus:ring-gold/10
            transition-all"
        />
        <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-0.5
          border border-black/12 rounded px-1 py-0.5 text-[10px] font-mono text-black/30">
          <Command className="w-2.5 h-2.5" />K
        </kbd>
      </div>

      <div className="ml-auto flex items-center gap-2">
        {/* Date */}
        <span className="font-mono text-[11px] text-black/40 bg-black/[0.03] border border-black/08
          px-2.5 py-1 rounded-lg">
          {dateStr}
        </span>

        {/* AI chip */}
        <div className="flex items-center gap-1.5 bg-navy border border-gold/25
          px-3 py-1.5 rounded-full">
          <div className="w-1.5 h-1.5 rounded-full bg-gold animate-breathe" />
          <span className="text-[11px] font-medium text-white/75 font-sans">IA · RAG actif</span>
        </div>

        {/* Notifications */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="relative w-[34px] h-[34px] rounded-lg border border-black/10
            bg-white flex items-center justify-center"
        >
          <Bell className="w-[15px] h-[15px] text-black/50" />
          <span className="absolute top-1.5 right-1.5 w-[5px] h-[5px] rounded-full
            bg-red-500 border-2 border-white" />
        </motion.button>

        {/* Avatar */}
        <div
          className="w-[30px] h-[30px] rounded-lg flex items-center justify-center
            text-[10px] font-bold text-white flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #C4962A, #9a6e1a)' }}
        >
          AM
        </div>
      </div>
    </header>
  )
}
