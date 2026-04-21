'use client'

import TenderAILogo from '@/components/ui/TenderAILogo'

interface RegisterLeftPanelProps {
  step: 1 | 2 | 3 | 4
}

const STEP_CONTENT = {
  1: {
    headline: 'Créez votre compte',
    subheadline:
      'Rejoignez les équipes qui remportent plus de marchés publics.',
    checkpoints: [
      'Essai gratuit 14 jours — aucune carte requise',
      'Déploiement en moins de 5 minutes',
      'Support FR/AR/EN inclus',
      'Données hébergées en région MENA',
    ],
  },
  2: {
    headline: 'Votre organisation',
    subheadline:
      'Ces informations personnalisent TenderAI pour votre contexte métier.',
    checkpoints: [
      'Isolation complète des données par organisation',
      'RBAC granulaire — 6 rôles hiérarchiques',
      'Support des marchés TUNEPS, CNSS, GCC',
      'Multi-filiales disponible en plan Entreprise',
    ],
  },
  3: {
    headline: 'Choisissez votre formule',
    subheadline:
      'Démarrez avec 14 jours d\'essai gratuit sur n\'importe quel plan.',
    checkpoints: [
      '14 jours d\'essai gratuit — sans engagement',
      'Changement de plan possible à tout moment',
      'Annulation en 1 clic',
      'Migration de données incluse si upgrade',
    ],
  },
  4: {
    headline: 'Presque terminé !',
    subheadline:
      'Vérifiez vos informations avant de créer votre compte.',
    checkpoints: [
      'Accès instantané au tableau de bord',
      'Équipe d\'onboarding disponible',
      'Support prioritaire pendant l\'essai',
    ],
  },
}

export default function RegisterLeftPanel({
  step,
}: RegisterLeftPanelProps): JSX.Element {
  const content = STEP_CONTENT[step]

  // Render stepper
  const renderStepper = () => {
    const steps = [
      { num: 1, label: 'Compte' },
      { num: 2, label: 'Organisation' },
      { num: 3, label: 'Formule' },
      { num: 4, label: 'Confirmation' },
    ]

    return (
      <div className="mb-12">
        <div className="flex items-center justify-between">
          {steps.map((s, idx) => (
            <div key={s.num} className="flex items-center">
              {/* Step circle */}
              <div
                className={`relative w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
                  s.num < step
                    ? 'bg-amber text-white'
                    : s.num === step
                      ? 'bg-amber text-white ring-4 ring-amber ring-opacity-30'
                      : 'bg-white/10 text-white/50'
                }`}
              >
                {s.num < step ? (
                  <svg
                    className="w-5 h-5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  s.num
                )}
              </div>

              {/* Label */}
              <div className="mt-2 w-full text-center">
                <p
                  className={`text-xs font-medium transition-colors ${
                    s.num <= step
                      ? 'text-amber'
                      : 'text-white/40'
                  }`}
                >
                  {s.label}
                </p>
              </div>

              {/* Connector line */}
              {idx < steps.length - 1 && (
                <div
                  className={`h-1 w-8 mx-2 transition-colors ${
                    s.num < step ? 'bg-amber' : 'bg-white/10'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="hidden lg:flex w-[40%] bg-navy flex-col justify-between p-12 overflow-y-auto">
      {/* Top — Logo */}
      <div>
        <TenderAILogo size="lg" theme="dark" showText={true} />
      </div>

      {/* Middle — Stepper and Content */}
      <div className="my-12">
        {renderStepper()}

        {/* Headline + Subheadline */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-white leading-tight mb-4">
            {content.headline}
          </h2>
          <p className="text-white/60 text-sm leading-relaxed">
            {content.subheadline}
          </p>
        </div>

        {/* Checkpoints */}
        <ul className="space-y-3">
          {content.checkpoints.map((checkpoint) => (
            <li
              key={checkpoint}
              className="flex items-start gap-3 text-sm text-white/80"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                className="mt-0.5 flex-shrink-0"
                aria-hidden="true"
              >
                <circle cx="8" cy="8" r="7" fill="rgba(196,150,42,0.2)" />
                <path
                  d="M5 8l2.5 2.5L11 5"
                  stroke="#C4962A"
                  strokeWidth="1.3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              {checkpoint}
            </li>
          ))}
        </ul>
      </div>

      {/* Footer note */}
      <div className="pt-8 border-t border-white/10">
        <p className="text-xs text-white/40">
          🔒 Vos données ne quittent jamais vos serveurs
        </p>
      </div>
    </div>
  )
}
