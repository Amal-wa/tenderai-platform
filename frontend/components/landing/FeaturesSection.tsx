'use client'

import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  FileSearch,
  ShieldCheck,
  Zap,
  LayoutDashboard,
  Lock,
  Headphones,
} from 'lucide-react'

interface HighlightCardProps {
  icon: React.ReactNode
  metric: string
  metricLabel: string
  title: string
  description: string
  iconBg: string
  index: number
}

function HighlightCard({ icon, metric, metricLabel, title, description, iconBg, index }: HighlightCardProps) {
  return (
    <motion.div
      whileInView={{ opacity: 1, y: 0 }}
      initial={{ opacity: 0, y: 20 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1 }}
      className="group bg-white rounded-2xl p-8 border border-cream-border hover:border-amber/40 hover:shadow-[0_8px_32px_rgba(196,150,42,0.10)] transition-all duration-300 relative overflow-hidden"
    >
      {/* Amber top bar on hover */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-amber scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
      {/* Icon */}
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-5 ${iconBg}`}>
        {icon}
      </div>
      {/* Metric */}
      <p className="text-3xl font-bold text-amber mb-1">{metric}</p>
      <p className="text-xs text-muted mb-3">{metricLabel}</p>
      {/* Title + desc */}
      <h3 className="text-base font-semibold text-navy mb-2">{title}</h3>
      <p className="text-sm text-muted leading-relaxed">{description}</p>
    </motion.div>
  )
}

interface SecondaryCardProps {
  icon: React.ReactNode
  title: string
  description: string
  iconBg: string
}

function SecondaryCard({ icon, title, description, iconBg }: SecondaryCardProps) {
  return (
    <div className="bg-white rounded-xl p-6 border border-cream-border hover:shadow-md transition-all duration-200 flex items-start gap-4">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${iconBg}`}>
        {icon}
      </div>
      <div>
        <h3 className="text-sm font-semibold text-navy mb-1">{title}</h3>
        <p className="text-xs text-muted leading-relaxed">{description}</p>
      </div>
    </div>
  )
}

export default function FeaturesSection(): JSX.Element {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
          }
        })
      },
      { threshold: 0.1 }
    )

    const reveals = ref.current?.querySelectorAll('.reveal')
    reveals?.forEach((el) => observer.observe(el))

    return () => observer.disconnect()
  }, [])

  return (
    <section ref={ref} className="bg-cream py-24 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <p className="text-xs font-bold text-amber uppercase tracking-[0.14em] mb-3">
            LA PLATEFORME
          </p>
          <h2 className="text-4xl lg:text-5xl font-bold text-navy tracking-tight leading-[1.15]">
            Tout ce qu'il faut pour<br />gérer vos appels d'offres
          </h2>
        </div>

        {/* Part A — 3 highlight cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-5">
          <HighlightCard
            index={0}
            icon={<FileSearch className="w-5 h-5 text-amber" />}
            metric="−80%"
            metricLabel="de temps de préparation"
            title="Analyse NLP avancée"
            description="Détection automatique des manques et risques de non-conformité avec IA deeptech."
            iconBg="bg-amber/10"
          />
          <HighlightCard
            index={1}
            icon={<ShieldCheck className="w-5 h-5 text-emerald-600" />}
            metric="94%"
            metricLabel="score de conformité moyen"
            title="Conformité garantie"
            description="Vérification RGPD, marchés publics et normes sectorielles en temps réel."
            iconBg="bg-emerald-100"
          />
          <HighlightCard
            index={2}
            icon={<Zap className="w-5 h-5 text-amber" />}
            metric="×3"
            metricLabel="plus d'AOs soumis"
            title="Gain de temps radical"
            description="Réduisez les délais d'analyse de 90% avec l'automatisation complète."
            iconBg="bg-amber/10"
          />
        </div>

        {/* Part B — 3 secondary cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <SecondaryCard
            icon={<LayoutDashboard className="w-4 h-4 text-navy" />}
            title="Dashboard temps réel"
            description="Suivez tous vos appels d'offres en un coup d'œil avec des KPIs détaillés."
            iconBg="bg-navy/10"
          />
          <SecondaryCard
            icon={<Lock className="w-4 h-4 text-amber" />}
            title="Sécurité bancaire"
            description="Données chiffrées, backups redondants, conformité ISO 27001."
            iconBg="bg-amber-muted"
          />
          <SecondaryCard
            icon={<Headphones className="w-4 h-4 text-emerald-600" />}
            title="Support dédié"
            description="Équipe joignable 24/7 en français, arabe et anglais."
            iconBg="bg-emerald-50"
          />
        </div>
      </div>

      <style jsx>{`
        @keyframes reveal {
          from {
            opacity: 0;
            transform: translateY(1.5rem);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .reveal {
          opacity: 0;
          animation: reveal 0.6s ease forwards;
        }

        .reveal.visible {
          animation-play-state: running;
        }

        .reveal-delay-0 {
          animation-delay: 0s;
        }

        .reveal-delay-1 {
          animation-delay: 0.1s;
        }

        .reveal-delay-2 {
          animation-delay: 0.2s;
        }
      `}</style>
    </section>
  )
}
