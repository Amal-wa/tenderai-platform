'use client'

import { useState } from 'react'
import Link from 'next/link'

interface Feature {
  label: string
  features: string[]
}

interface Plan {
  id: string
  title: string
  description: string
  monthlyPrice: number
  annualPrice: number
  annualTotal: number | null
  annualSavings: number | null
  featured: boolean
  badge?: string
  priceNote?: string
  cta: string
  ctaVariant: 'outlined' | 'filled'
  socialProof: string
  categories: Feature[]
}

const plans: Plan[] = [
  {
    id: 'fondements',
    title: 'Fondements',
    description:
      'Pour les équipes traitant un volume limité d\'appels d\'offres.',
    monthlyPrice: 60,
    annualPrice: 48,
    annualTotal: 576,
    annualSavings: 144,
    featured: false,
    cta: 'Commencer',
    ctaVariant: 'outlined',
    socialProof: '⭐ Utilisé par 47 équipes en Tunisie',
    categories: [
      {
        label: 'Traitement documentaire',
        features: [
          'Ingestion intelligente (PDF/Word/Excel)',
          'Export DOCX/PDF soigné (respect charte graphique)',
        ],
      },
      {
        label: 'Rédaction IA',
        features: [
          'IA de rédaction — brouillons + reformulation',
          'Bibliothèque de contenu & templates sectoriels',
        ],
      },
      {
        label: 'Collaboration',
        features: [
          'Workflow collaboratif — assignation, relectures, notifications',
        ],
      },
      {
        label: 'Sécurité',
        features: [
          'RBAC + MFA',
          'Reporting & Analytics — taux succès AO, temps gagné',
        ],
      },
    ],
  },
  {
    id: 'avancee',
    title: 'Version avancée',
    description:
      'Pour les équipes centralisées gérant plusieurs AOs simultanément.',
    monthlyPrice: 290,
    annualPrice: 232,
    annualTotal: 2784,
    annualSavings: 696,
    featured: true,
    badge: 'Le plus populaire',
    cta: 'Commencer',
    ctaVariant: 'filled',
    socialProof: '🏆 Choix de 68% des équipes en croissance',
    categories: [
      {
        label: 'Conformité',
        features: [
          'Matrice de conformité auditable (obligatoire / pondérée / preuves / traçabilité)',
          'Explainability / Guardrails IA — chaque réponse générée cite sa source',
        ],
      },
      {
        label: 'Pricing',
        features: [
          'Moteur de pricing paramétrique (coûts, marges, risques, bordereaux)',
          'Auto-assemblage d\'annexes — coffre documentaire + alertes expiration',
        ],
      },
      {
        label: 'IA & Agent',
        features: [
          'Agent proactif — alertes délais, critères manquants, annexes expirées',
          'Mode éditeur interactif WYSIWYG + volet RAG latéral',
        ],
      },
      {
        label: 'Intégrations',
        features: [
          'CRM/ERP/DMS (Salesforce, Odoo, SharePoint)',
          'Accès API complet',
        ],
      },
    ],
  },
  {
    id: 'entreprise',
    title: 'Entreprise',
    description:
      'Pour les grands groupes multi-filiales et les marchés régionaux (Tunisie, Maroc, GCC).',
    monthlyPrice: 890,
    annualPrice: 890,
    annualTotal: null,
    annualSavings: null,
    featured: false,
    priceNote: 'Prix de départ · Sur devis selon périmètre',
    cta: 'Nous contacter',
    ctaVariant: 'outlined',
    socialProof: '🌍 3 groupes régionaux actifs (Tunisie, Maroc, GCC)',
    categories: [
      {
        label: 'Souveraineté',
        features: [
          'Pack souveraineté — hébergement régional, VPC, KMS',
          'Référentiels pays/secteurs — TUNEPS, CNSS, garanties bancaires GCC',
        ],
      },
      {
        label: 'IA avancée',
        features: [
          'Simulation Monte-Carlo + Win Probability Score',
          'Training IA continu sur historique gagnant/perdant',
        ],
      },
      {
        label: 'Opérations',
        features: [
          'Multi-filiales & multi-lots — réponse commune inter-entités',
          'Auto-soumission portails publics (TUNEPS, Maroc, GCC)',
        ],
      },
      {
        label: 'Support',
        features: [
          'Connecteurs e-signature (DocuSign / Yousign)',
          'Application mobile — suivi AO + validation en déplacement',
          'Support 24/7 + SLA garanti',
        ],
      },
    ],
  },
]

interface PricingCardProps {
  plan: Plan
  isAnnual: boolean
}

function CheckmarkIcon(): JSX.Element {
  return (
    <svg
      className="w-5 h-5 text-amber flex-shrink-0"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.2" />
      <path
        d="M8 12L11 15L16 9"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function PricingCard({ plan, isAnnual }: PricingCardProps): JSX.Element {
  const [expandedCategories, setExpandedCategories] = useState<
    Record<string, boolean>
  >({
    [plan.categories[0]?.label]: true,
  })

  const currentPrice = isAnnual ? plan.annualPrice : plan.monthlyPrice

  const toggleCategory = (label: string): void => {
    setExpandedCategories((prev) => ({
      ...prev,
      [label]: !prev[label],
    }))
  }

  const cardClasses = plan.featured
    ? 'bg-navy border-2 border-amber rounded-2xl p-8 shadow-lg scale-105 relative'
    : 'bg-white border border-cream-border rounded-2xl p-8'

  const textColor = plan.featured ? 'text-white' : 'text-navy'
  const descColor = plan.featured ? 'text-white/70' : 'text-muted'
  const priceColor = plan.featured ? 'text-amber' : 'text-navy'
  const labelColor = plan.featured ? 'text-amber' : 'text-muted'

  return (
    <div className={cardClasses}>
      {plan.badge && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-amber text-white text-xs font-semibold px-4 py-1.5 rounded-full whitespace-nowrap">
          {plan.badge}
        </div>
      )}

      {/* Header */}
      <h3 className={`font-heading text-2xl font-bold mb-2 ${textColor}`}>
        {plan.title}
      </h3>
      <p className={`text-sm mb-6 ${descColor}`}>{plan.description}</p>

      {/* Price */}
      <div className="mb-6">
        <div className="flex items-baseline gap-1 mb-2">
          <span className={`font-heading text-5xl font-bold transition-all duration-300 ${priceColor}`}>
            {currentPrice}
          </span>
          <span className={`text-sm ${descColor}`}>
            TND/{isAnnual ? 'an' : 'mois'}
          </span>
        </div>

        {plan.annualSavings && isAnnual && (
          <p className={`text-xs font-semibold ${plan.featured ? 'text-amber' : 'text-success'}`}>
            économisez {plan.annualSavings} TND
          </p>
        )}

        {plan.priceNote && (
          <p className={`text-xs ${descColor}`}>{plan.priceNote}</p>
        )}
      </div>

      {/* CTA Button */}
      <Link
        href={plan.cta === 'Nous contacter' ? '/contact' : '/login'}
        className={`block w-full h-12 px-6 py-3 rounded-xl font-semibold text-center transition-all mb-3 ${
          plan.featured
            ? plan.ctaVariant === 'filled'
              ? 'bg-white/10 border border-white text-white hover:bg-white/20'
              : 'bg-white text-navy hover:bg-cream'
            : plan.ctaVariant === 'filled'
              ? 'bg-amber text-white hover:bg-amber-light border border-amber'
              : 'bg-white text-navy border border-navy hover:bg-navy hover:text-white'
        }`}
      >
        {plan.cta}
      </Link>

      {/* Social proof */}
      <p className={`text-xs text-center ${plan.featured ? 'text-white/50' : 'text-muted'}`}>
        {plan.socialProof}
      </p>

      {/* Divider */}
      <div
        className={`my-8 ${plan.featured ? 'border-t border-white/10' : 'border-t border-cream-border'}`}
      ></div>

      {/* Feature Categories */}
      <div className="space-y-3">
        {plan.categories.map((category) => (
          <div key={category.label}>
            {/* Category header */}
            <button
              onClick={() => toggleCategory(category.label)}
              className={`w-full flex items-center justify-between py-2 ${labelColor} hover:opacity-80 transition-opacity`}
            >
              <span className="text-xs font-bold uppercase tracking-wider">
                {category.label}
              </span>
              <svg
                className={`w-4 h-4 transition-transform ${
                  expandedCategories[category.label] ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 14l-7 7m0 0l-7-7m7 7V3"
                />
              </svg>
            </button>

            {/* Category features */}
            {expandedCategories[category.label] && (
              <div className="space-y-2 mt-3 ml-0">
                {category.features.map((feature, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <CheckmarkIcon />
                    <span className={`text-sm leading-relaxed ${descColor}`}>
                      {feature}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function PricingSection(): JSX.Element {
  const [isAnnual, setIsAnnual] = useState(false)

  return (
    <section id="pricing" className="py-24 px-6 lg:px-12 bg-cream">
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <p className="text-xs font-bold text-amber uppercase tracking-widest mb-3">
            Tarification
          </p>
          <h2 className="font-heading text-4xl font-bold text-navy mb-4">
            Simple et transparent
          </h2>
          <p className="text-muted max-w-xl mx-auto">
            Des formules pensées pour chaque stade de votre croissance
          </p>
        </div>

        {/* Billing toggle */}
        <div className="flex items-center justify-center gap-3 flex-wrap mb-10 px-4">
          <span
            className={`text-sm font-medium whitespace-nowrap transition-colors ${
              !isAnnual ? 'text-navy' : 'text-muted'
            }`}
          >
            Mensuel
          </span>
          <button
            onClick={() => setIsAnnual(!isAnnual)}
            className={`relative inline-flex items-center w-12 h-6 rounded-full cursor-pointer transition-colors duration-200 shrink-0 overflow-hidden focus:outline-none focus-visible:ring-2 focus-visible:ring-amber focus-visible:ring-offset-2 ${
              isAnnual ? 'bg-amber' : 'bg-cream-border'
            }`}
            role="switch"
            aria-checked={isAnnual}
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200 ${
                isAnnual ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
          <span
            className={`text-sm font-medium whitespace-nowrap transition-colors ${
              isAnnual ? 'text-navy' : 'text-muted'
            }`}
          >
            Annuel
          </span>
          {isAnnual && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-amber text-white text-xs font-semibold whitespace-nowrap shrink-0">
              -20%
            </span>
          )}
        </div>

        {/* Pricing cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center mb-16">
          {plans.map((plan) => (
            <PricingCard key={plan.id} plan={plan} isAnnual={isAnnual} />
          ))}
        </div>
      </div>
    </section>
  )
}
