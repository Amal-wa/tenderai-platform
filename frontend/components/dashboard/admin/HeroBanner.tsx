'use client'
import { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import type { HeroData } from '@/lib/admin/analytics'

interface HeroBannerProps {
  hero: HeroData
}

export default function HeroBanner({ hero }: HeroBannerProps): React.ReactElement {
  const { user } = useAuth()
  const [aosCount, setAosCount] = useState(0)
  const [winRateCount, setWinRateCount] = useState(0)
  const [conformiteCount, setConformiteCount] = useState(0)

  // Extract first name from full_name
  const firstName = user?.full_name?.split(' ')[0] || 'Utilisateur'

  useEffect(() => {
    let frameId: number
    const startTime = Date.now()
    const duration = 1400

    const animate = () => {
      const now = Date.now()
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)

      setAosCount(Math.floor(hero.aos * progress))
      setWinRateCount(Math.floor(hero.winRate * progress))
      setConformiteCount(Math.floor(hero.conformite * progress))

      if (progress < 1) {
        frameId = requestAnimationFrame(animate)
      }
    }

    frameId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(frameId)
  }, [hero])

  return (
    <div className="bg-[var(--navy)] rounded-2xl p-8 mb-7 grid grid-cols-[1fr_auto] gap-6 items-center relative overflow-hidden">
      {/* Decorative Orbs */}
      <div
        className="absolute top-[-40px] right-[120px] w-48 h-48 rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(196,150,42,0.12) 0%, transparent 70%)',
        }}
      />

      {/* Left Content */}
      <div>
        <p className="text-[13px] text-white/45 mb-1">Bonjour, {firstName} 👋</p>
        <h2 className="font-heading text-[26px] font-black text-white leading-tight mb-4">
          Performance{' '}
          <span className="text-[var(--amber-xl)]">au-dessus du marché</span>
          {' '}sur tous les axes
        </h2>

        {/* Badges */}
        <div className="flex flex-col gap-2">
          <div className="inline-flex items-center gap-2 w-fit px-3 py-2 rounded-lg bg-[rgba(29,158,117,0.2)]">
            <span className="text-[#5DCAA5] text-xs font-medium">
              ● Win rate +27pts vs concurrence
            </span>
          </div>
          <div className="inline-flex items-center gap-2 w-fit px-3 py-2 rounded-lg bg-[var(--amber-soft)]">
            <span className="text-[var(--amber-xl)] text-xs font-medium">
              ● 1 840h économisées ce trimestre
            </span>
          </div>
          <div className="inline-flex items-center gap-2 w-fit px-3 py-2 rounded-lg bg-[rgba(55,138,221,0.15)]">
            <span className="text-[#85B7EB] text-xs font-medium">
              {hero.tenant}
            </span>
          </div>
        </div>
      </div>

      {/* Right Stats */}
      <div className="flex items-center gap-6">
        <div className="text-center">
          <p className="font-heading text-[28px] font-black text-[var(--amber)]">
            {aosCount}
          </p>
          <p className="text-[10px] text-white/40 mt-1">AOs analysés</p>
        </div>

        <div className="w-px h-12 bg-white/8" />

        <div className="text-center">
          <p className="font-heading text-[28px] font-black text-[var(--amber)]">
            {winRateCount}%
          </p>
          <p className="text-[10px] text-white/40 mt-1">Win rate</p>
        </div>

        <div className="w-px h-12 bg-white/8" />

        <div className="text-center">
          <p className="font-heading text-[28px] font-black text-[var(--amber)]">
            {conformiteCount}%
          </p>
          <p className="text-[10px] text-white/40 mt-1">Conformité</p>
        </div>
      </div>
    </div>
  )
}
