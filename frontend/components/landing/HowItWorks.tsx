'use client'

import { motion } from 'framer-motion'
import { Upload, Brain, Trophy } from 'lucide-react'

interface StepProps {
  number: number
  icon: React.ReactNode
  title: string
  description: string
  index: number
}

function Step({ number, icon, title, description, index }: StepProps) {
  return (
    <motion.div
      whileInView={{ opacity: 1, y: 0 }}
      initial={{ opacity: 0, y: 20 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.15 }}
      className="relative z-10 flex flex-col items-center text-center"
    >
      {/* Step circle */}
      <div className="w-14 h-14 rounded-full bg-navy flex items-center justify-center mb-6 shadow-[0_4px_16px_rgba(19,32,58,0.25)]">
        <span className="text-white font-bold text-lg">0{number}</span>
      </div>
      {/* Icon pill below number */}
      <div className="w-10 h-10 rounded-xl bg-amber-muted flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-navy mb-3">{title}</h3>
      <p className="text-sm text-muted leading-relaxed max-w-[220px]">{description}</p>
    </motion.div>
  )
}

export default function HowItWorks(): JSX.Element {
  const steps = [
    {
      number: 1,
      icon: <Upload className="w-5 h-5 text-amber" />,
      title: 'Importez vos appels',
      description: 'Téléchargez vos PDF, documents Word ou textes. L\'IA détecte la langue et la structure automatiquement.',
    },
    {
      number: 2,
      icon: <Brain className="w-5 h-5 text-amber" />,
      title: 'L\'IA analyse',
      description: 'Notre IA deeptech analyse en temps réel conformité, risques et écarts par rapport aux exigences.',
    },
    {
      number: 3,
      icon: <Trophy className="w-5 h-5 text-amber" />,
      title: 'Décidez et remportez',
      description: 'Obtenez un rapport détaillé avec score de confiance et recommandations actionnables.',
    },
  ]

  return (
    <section className="bg-white py-24 px-6">
      <div className="max-w-4xl mx-auto text-center">
        <p className="text-xs font-bold text-amber uppercase tracking-[0.14em] mb-3">
          LE PROCESSUS
        </p>
        <h2 className="text-4xl font-bold text-navy tracking-tight mb-4">
          Comment ça marche
        </h2>
        <p className="text-base text-muted max-w-xl mx-auto mb-16">
          De l'import à la soumission, TenderAI automatise chaque étape de votre processus AO.
        </p>

        <div className="relative grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Connector line (desktop only) */}
          <div className="hidden md:block absolute top-[28px] left-[20%] right-[20%] h-px border-t-2 border-dashed border-amber/30 z-0" />

          {steps.map((step, i) => (
            <Step key={step.title} {...step} index={i} />
          ))}
        </div>
      </div>
    </section>
  )
}
