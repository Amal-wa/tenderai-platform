'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { motion } from 'framer-motion'
import { ArrowLeft, ArrowRight, Check } from 'lucide-react'
import { step3Schema, type Step3Data } from '@/lib/validations/register'

interface Step3FormProps {
  onSubmit: (data: Step3Data) => void
  onBack: () => void
  isLoading?: boolean
  defaultValues?: Partial<Step3Data>
}

interface Plan {
  id: 'fondements' | 'avancee' | 'entreprise'
  title: string
  priceMonthly: number | string
  priceAnnual: number | string
  description: string
  features: string[]
  recommended?: boolean
}

const PLANS: Plan[] = [
  {
    id: 'fondements',
    title: 'Fondements',
    priceMonthly: 60,
    priceAnnual: 576,
    description: 'Volume limité · jusqu\'à 5 utilisateurs',
    features: [
      'Ingestion PDF/Word/Excel',
      'IA de rédaction + templates',
      'RBAC + MFA',
    ],
  },
  {
    id: 'avancee',
    title: 'Version avancée',
    priceMonthly: 290,
    priceAnnual: 2784,
    description: 'Équipes centralisées · AOs multiples',
    features: [
      'Matrice de conformité auditée',
      'Moteur de pricing paramétrique',
      'Agent proactif + alertes',
    ],
    recommended: true,
  },
  {
    id: 'entreprise',
    title: 'Entreprise',
    priceMonthly: 'Sur devis',
    priceAnnual: 'Sur devis',
    description: 'Groupes multi-filiales · TUNEPS/GCC',
    features: [
      'Pack souveraineté VPC/KMS',
      'Simulation Monte-Carlo',
      'Support 24/7 + SLA',
    ],
  },
]

export default function Step3Form({
  onSubmit,
  onBack,
  isLoading = false,
  defaultValues,
}: Step3FormProps): JSX.Element {
  const {
    handleSubmit,
    watch,
    setValue,
    formState: { isValid },
  } = useForm<Step3Data>({
    resolver: zodResolver(step3Schema),
    mode: 'onChange',
    defaultValues: {
      plan: defaultValues?.plan || 'avancee',
      billing: defaultValues?.billing || 'annual',
    },
  })

  const plan = watch('plan')
  const billing = watch('billing')
  const isAnnual = billing === 'annual'

  const handlePlanSelect = (planId: 'fondements' | 'avancee' | 'entreprise') => {
    setValue('plan', planId)
  }

  const handleBillingToggle = (value: 'monthly' | 'annual') => {
    setValue('billing', value)
  }

  const handleSubmitClick = () => {
    if (plan === 'entreprise') {
      // Open mailto for sales inquiry
      window.location.href = 'mailto:sales@tenderai.tn?subject=Demande%20d\'information%20-%20Plan%20Entreprise'
    } else {
      handleSubmit((data: any) => onSubmit(data as Step3Data))()
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
    >
      <h1 className="text-2xl font-bold text-navy mb-2">Choisissez votre formule</h1>
      <p className="text-muted text-sm mb-6">Démarrez avec 14 jours d'essai gratuit</p>

      <form onSubmit={(e) => { e.preventDefault(); handleSubmitClick() }} className="space-y-6">
        {/* Billing toggle */}
        <div className="flex items-center justify-center gap-4">
          <button
            type="button"
            onClick={() => handleBillingToggle('monthly')}
            className={`px-4 py-2 rounded-lg font-medium transition-all text-sm ${
              !isAnnual
                ? 'bg-amber text-white'
                : 'bg-white text-navy border border-cream-border hover:border-amber/50'
            }`}
          >
            Mensuel
          </button>
          <button
            type="button"
            onClick={() => handleBillingToggle('annual')}
            className={`px-4 py-2 rounded-lg font-medium transition-all text-sm relative ${
              isAnnual
                ? 'bg-amber text-white'
                : 'bg-white text-navy border border-cream-border hover:border-amber/50'
            }`}
          >
            Annuel
            {isAnnual && (
              <span className="absolute -top-2 -right-3 bg-success text-white text-[10px] px-1.5 py-0.5 rounded-full">
                −20%
              </span>
            )}
          </button>
        </div>

        {/* Plan cards */}
        <div className="space-y-3">
          {PLANS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => handlePlanSelect(p.id)}
              className={`relative w-full p-5 rounded-2xl border-1.5 cursor-pointer transition-all text-left ${
                plan === p.id
                  ? 'border-amber bg-amber/5'
                  : 'border-cream-border bg-white hover:border-amber/40'
              }`}
            >
              {p.recommended && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-amber text-white text-xs font-semibold px-3 py-1 rounded-full">
                  Recommandé
                </div>
              )}

              {plan === p.id && (
                <div className="absolute top-3 right-3">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <circle cx="10" cy="10" r="10" fill="#C4962A" />
                    <path
                      d="M6 10l3 3 5-5"
                      stroke="white"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
              )}

              <div className="font-heading font-bold text-navy mb-1">{p.title}</div>
              <div className="text-amber font-semibold text-sm mb-2">
                {isAnnual ? `${p.priceAnnual} TND/an` : `${p.priceMonthly} TND/mois`}
              </div>
              <p className="text-xs text-muted mb-3">{p.description}</p>

              <ul className="space-y-1">
                {p.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-xs text-navy">
                    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                      <circle
                        cx="8"
                        cy="8"
                        r="7"
                        fill={plan === p.id ? 'rgba(196,150,42,0.15)' : '#E8F5EF'}
                      />
                      <path
                        d="M5 8l2.5 2.5L11 5"
                        stroke={plan === p.id ? '#C4962A' : '#1E7C5A'}
                        strokeWidth="1.3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
            </button>
          ))}
        </div>

        {/* Trial notice */}
        <div className="flex items-center gap-2 p-3 bg-success/10 border border-success/20 rounded-lg">
          <Check className="w-4 h-4 text-success flex-shrink-0" />
          <p className="text-xs text-success font-medium">
            14 jours gratuits — aucune carte débitée avant le{' '}
            {new Date(Date.now() + 14 * 86400000).toLocaleDateString('fr-FR', {
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            })}
          </p>
        </div>

        {/* Link to full pricing */}
        <p className="text-center text-xs text-muted">
          <a href="/pricing" target="_blank" rel="noopener noreferrer" className="text-amber hover:underline">
            Voir la comparaison complète →
          </a>
        </p>

        {/* Navigation */}
        <div className="flex gap-3 mt-6">
          <button
            type="button"
            onClick={onBack}
            className="flex-1 py-3.5 bg-white text-navy font-semibold rounded-xl border border-cream-border hover:border-amber/50 transition-all flex items-center justify-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Retour
          </button>
          <button
            type="submit"
            disabled={!isValid || isLoading}
            className="flex-1 py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {plan === 'entreprise' ? 'Nous contacter' : 'Continuer'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </motion.div>
  )
}
