'use client'

import { motion } from 'framer-motion'
import { ArrowLeft, ArrowRight, Loader2, Check } from 'lucide-react'
import { RegisterFormData } from '@/lib/validations/register'

interface Step4ConfirmProps {
  data: Partial<RegisterFormData>
  onSubmit: () => void
  onBack: () => void
  onEdit: (step: 1 | 2 | 3) => void
  isLoading?: boolean
}

const PLANS: Record<string, { title: string; price: string }> = {
  fondements: { title: 'Fondements', price: 'À partir de 60 TND/mois' },
  avancee: { title: 'Version avancée', price: 'À partir de 290 TND/mois' },
  entreprise: { title: 'Entreprise', price: 'Sur devis' },
}

export default function Step4Confirm({
  data,
  onSubmit,
  onBack,
  onEdit,
  isLoading = false,
}: Step4ConfirmProps): JSX.Element {
  const fullName = `${data.firstName} ${data.lastName}`.trim()
  const planData = PLANS[(data.plan || 'avancee') as keyof typeof PLANS]

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
    >
      <h1 className="text-2xl font-bold text-navy mb-6">Vérification</h1>

      {/* Trial banner */}
      <div className="flex items-start gap-3 p-4 bg-success/10 border border-success/20 rounded-lg mb-6">
        <Check className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-success font-semibold">
            14 jours gratuits — aucune carte débitée
          </p>
          <p className="text-xs text-success/80">
            Avant le {new Date(Date.now() + 14 * 86400000).toLocaleDateString('fr-FR', {
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            })}
          </p>
        </div>
      </div>

      {/* Summary cards */}
      <div className="space-y-3 mb-6">
        {/* Account summary */}
        <div className="bg-white border border-cream-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-navy uppercase tracking-wide">
              Compte
            </span>
            <button
              onClick={() => onEdit(1)}
              className="text-xs text-amber hover:underline font-medium"
            >
              Modifier
            </button>
          </div>
          <div className="text-sm font-semibold text-navy">{fullName}</div>
          <div className="text-xs text-muted">{data.email}</div>
        </div>

        {/* Organization summary */}
        <div className="bg-white border border-cream-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-navy uppercase tracking-wide">
              Organisation
            </span>
            <button
              onClick={() => onEdit(2)}
              className="text-xs text-amber hover:underline font-medium"
            >
              Modifier
            </button>
          </div>
          <div className="text-sm font-semibold text-navy">{data.orgName}</div>
          <div className="text-xs text-muted">
            {data.sector} · 🇹🇳 Tunisie · {data.orgSize} employés
          </div>
        </div>

        {/* Plan summary */}
        <div className="bg-white border border-cream-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-navy uppercase tracking-wide">
              Formule
            </span>
            <button
              onClick={() => onEdit(3)}
              className="text-xs text-amber hover:underline font-medium"
            >
              Modifier
            </button>
          </div>
          <div className="text-sm font-semibold text-navy">{planData.title}</div>
          <div className="text-xs text-muted">
            {planData.price} · 14 jours gratuits
          </div>
        </div>
      </div>

      {/* Submit button */}
      <button
        onClick={onSubmit}
        disabled={isLoading}
        className="w-full py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all shadow-lg shadow-amber/30 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 mb-3"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Création en cours...
          </>
        ) : (
          <>
            Créer mon compte
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>

      {/* Back button */}
      <button
        onClick={onBack}
        className="w-full py-3.5 bg-white text-navy font-semibold rounded-xl border border-cream-border hover:border-amber/50 transition-all flex items-center justify-center gap-2"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour
      </button>
    </motion.div>
  )
}
