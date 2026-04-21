'use client'

import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'

interface StatBlockProps {
  number: number
  suffix: string
  label: string
  context: string
}

function StatBlock({ number, suffix, label, context }: StatBlockProps) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const hasStarted = useRef(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !hasStarted.current) {
          hasStarted.current = true
          const duration = 1200
          const step = number / (duration / 16)
          let current = 0

          const timer = setInterval(() => {
            current += step
            if (current >= number) {
              setCount(number)
              clearInterval(timer)
            } else {
              setCount(Math.round(current))
            }
          }, 16)

          return () => clearInterval(timer)
        }
        return undefined
      },
      { threshold: 0.3 }
    )

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => {
      observer.disconnect()
    }
  }, [number])

  return (
    <div ref={ref} className="px-8 py-6 text-center">
      <p className="text-[44px] lg:text-[52px] font-bold text-amber leading-none mb-2">
        {count}
        {suffix}
      </p>
      <p className="text-sm text-white/50 leading-snug">{label}</p>
      <p className="text-xs text-white/30 mt-1">{context}</p>
    </div>
  )
}

export default function StatsSection(): JSX.Element {
  return (
    <section className="bg-[#13203A] py-20 px-6 relative overflow-hidden">
      {/* Subtle amber glow center */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 60% 50% at 50% 100%, rgba(196,150,42,0.08) 0%, transparent 70%)',
        }}
      />

      <div className="relative max-w-7xl mx-auto">
        {/* Eyebrow above stats */}
        <p className="text-center text-xs font-semibold text-amber/70 uppercase tracking-[0.14em] mb-10">
          Des résultats mesurables dès le premier mois
        </p>

        <div className="grid grid-cols-2 lg:grid-cols-4">
          <div className="px-8 py-6 text-center border-r border-white/[0.08] hidden sm:block">
            <StatBlock number={247} suffix="" label="Appels d'offres analysés" context="ce trimestre" />
          </div>
          <div className="px-8 py-6 text-center border-r border-white/[0.08]">
            <StatBlock number={94} suffix="%" label="Conformité moyenne" context="+3pts vs marché" />
          </div>
          <div className="px-8 py-6 text-center border-r border-white/[0.08] hidden lg:block">
            <StatBlock number={1840} suffix="h" label="Heures économisées" context="par nos clients" />
          </div>
          <div className="px-8 py-6 text-center">
            <StatBlock number={68} suffix="%" label="Taux de victoire" context="vs 41% sans TenderAI" />
          </div>
        </div>

        {/* Bottom CTA nudge */}
        <div className="text-center mt-12 pt-10 border-t border-white/[0.08]">
          <p className="text-sm text-white/50 mb-4">
            Rejoignez les équipes qui transforment leur performance AO
          </p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className="inline-flex items-center gap-2 bg-amber hover:bg-amber-light text-white font-semibold text-sm px-6 py-3 rounded-xl transition-colors"
          >
            Démarrer gratuitement
            <ArrowRight className="w-4 h-4" />
          </motion.button>
        </div>
      </div>
    </section>
  )
}
