'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import Link from 'next/link'
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  Loader2,
  ArrowRight,
  ArrowLeft,
  Building2,
  Globe,
  Users,
  Check,
  ChevronDown,
} from 'lucide-react'
import AuthLeftPanel from '@/components/auth/AuthLeftPanel'
import StepIndicator from '@/components/ui/StepIndicator'
import TenderAILogo from '@/components/ui/TenderAILogo'
import { register } from '@/lib/api'
import { saveTokens } from '@/lib/auth'

// ────────────────────────────────────────────────────────────────────────────
// TYPES & CONSTANTS
// ────────────────────────────────────────────────────────────────────────────

type StandardStep = 'account' | 'organization' | 'plan' | 'confirm'
type InviteStep = 'account' | 'confirm'

interface AccountForm {
  firstName: string
  lastName: string
  email: string
  password: string
  confirmPassword: string
  acceptTerms: boolean
}

interface OrgForm {
  organizationName: string
  sector: string
  country: string
  size: string
  portals: string[]
}

interface PasswordValidation {
  valid: boolean
  errors: string[]
  strength: 0 | 1 | 2 | 3 | 4
}

const PASSWORD_RULES = {
  minLength: 12,
  maxLength: 128,
  requireUppercase: true,
  requireLowercase: true,
  requireDigit: true,
  requireSpecial: true,
  noSpaces: true,
}

const SECTORS = [
  'Construction & BTP',
  'Informatique & Télécommunications',
  'Santé & Pharmaceutique',
  'Énergie & Utilities',
  'Conseil & Services',
  'Industrie & Manufacture',
  'Transport & Logistique',
  'Autre',
]

const COUNTRIES = [
  { value: 'TN', label: '🇹🇳 Tunisie' },
  { value: 'MA', label: '🇲🇦 Maroc' },
  { value: 'DZ', label: '🇩🇿 Algérie' },
  { value: 'SA', label: '🇸🇦 Arabie Saoudite' },
  { value: 'AE', label: '🇦🇪 Émirats Arabes Unis' },
  { value: 'FR', label: '🇫🇷 France' },
  { value: 'OTHER', label: '🌍 Autre' },
]

const SIZES = ['1–10', '11–50', '51–200', '201–500', '500+']

const PORTALS = ['TUNEPS', 'CNSS', 'ANPE', 'Marchés GCC', 'Portails européens', 'Autre']

interface Plan {
  id: 'fondements' | 'avancee' | 'entreprise'
  title: string
  price: string
  description: string
  highlights: string[]
  recommended?: boolean
}

const PLANS: Plan[] = [
  {
    id: 'fondements',
    title: 'Fondements',
    price: '60 TND/mois',
    description: 'Pour les équipes traitant un volume limité d\'AOs.',
    highlights: [
      'Ingestion PDF/Word/Excel',
      'IA de rédaction',
      'RBAC + MFA',
    ],
  },
  {
    id: 'avancee',
    title: 'Version avancée',
    price: '290 TND/mois',
    description: 'Pour les équipes centralisées gérant plusieurs AOs.',
    highlights: [
      'Matrice de conformité auditable',
      'Moteur de pricing paramétrique',
      'Agent proactif + alertes',
    ],
    recommended: true,
  },
  {
    id: 'entreprise',
    title: 'Entreprise',
    price: 'Sur devis',
    description: 'Pour les grands groupes et marchés régionaux.',
    highlights: [
      'Pack souveraineté VPC/KMS',
      'Auto-soumission TUNEPS/GCC',
      'Support 24/7 + SLA',
    ],
  },
]

// ────────────────────────────────────────────────────────────────────────────
// PASSWORD VALIDATION
// ────────────────────────────────────────────────────────────────────────────

function validatePassword(pwd: string): PasswordValidation {
  const errors: string[] = []

  if (pwd.length < PASSWORD_RULES.minLength) errors.push(`Minimum ${PASSWORD_RULES.minLength} caractères`)
  if (pwd.length > PASSWORD_RULES.maxLength) errors.push(`Maximum ${PASSWORD_RULES.maxLength} caractères`)
  if (PASSWORD_RULES.requireUppercase && !/[A-Z]/.test(pwd)) errors.push('Au moins une majuscule')
  if (PASSWORD_RULES.requireLowercase && !/[a-z]/.test(pwd)) errors.push('Au moins une minuscule')
  if (PASSWORD_RULES.requireDigit && !/[0-9]/.test(pwd)) errors.push('Au moins un chiffre')
  if (PASSWORD_RULES.requireSpecial && !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd))
    errors.push('Au moins un caractère spécial')
  if (PASSWORD_RULES.noSpaces && /\s/.test(pwd)) errors.push('Pas d\'espaces autorisés')

  // Strength score (0-4)
  let strengthNum = 0
  if (pwd.length >= PASSWORD_RULES.minLength) strengthNum++
  if (pwd.length >= 16) strengthNum++
  if (/[!@#$%^&*]/.test(pwd) && /[0-9]/.test(pwd)) strengthNum++
  if (pwd.length >= 20 && errors.length === 0) strengthNum = 4

  const strength: 0 | 1 | 2 | 3 | 4 = Math.min(strengthNum, 4) as 0 | 1 | 2 | 3 | 4

  return { valid: errors.length === 0, errors, strength }
}

const PASSWORD_RULES_UI = [
  { label: '12 caractères minimum', test: (p: string) => p.length >= 12 },
  { label: 'Une majuscule (A–Z)', test: (p: string) => /[A-Z]/.test(p) },
  { label: 'Une minuscule (a–z)', test: (p: string) => /[a-z]/.test(p) },
  { label: 'Un chiffre (0–9)', test: (p: string) => /[0-9]/.test(p) },
  { label: 'Un caractère spécial (!@#$...)', test: (p: string) => /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(p) },
]

// ────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ────────────────────────────────────────────────────────────────────────────

export default function RegistrationPageClient(): JSX.Element {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Detect mode from URL
  const inviteToken = searchParams.get('token')
  const inviteEmail = searchParams.get('email')
  const isInviteMode = !!inviteToken

  // Standard mode steps
  const standardSteps = [
    { id: 'account', label: 'Compte', number: 1 },
    { id: 'organization', label: 'Organisation', number: 2 },
    { id: 'plan', label: 'Formule', number: 3 },
    { id: 'confirm', label: 'Confirmation', number: 4 },
  ]

  // Invite mode steps
  const inviteSteps = [
    { id: 'account', label: 'Compte', number: 1 },
    { id: 'confirm', label: 'Confirmation', number: 2 },
  ]

  // FORM STATE ─────────────────────────────────────────────────────────────
  const [currentStep, setCurrentStep] = useState<StandardStep | InviteStep>('account')
  const [isLoading, setIsLoading] = useState(false)
  const [generalError, setGeneralError] = useState<string>('')

  // Account form
  const [accountForm, setAccountForm] = useState<AccountForm>({
    firstName: '',
    lastName: '',
    email: inviteEmail || '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
  })

  // Organization form
  const [orgForm, setOrgForm] = useState<OrgForm>({
    organizationName: '',
    sector: '',
    country: 'TN',
    size: '',
    portals: [],
  })

  // Plan selection
  const [selectedPlan, setSelectedPlan] = useState<'fondements' | 'avancee' | 'entreprise'>('avancee')

  // Field visibility toggles
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [passwordFocused, setPasswordFocused] = useState(false)

  // UI state
  const [expandedCountrySelect, setExpandedCountrySelect] = useState(false)
  const [expandedSectorSelect, setExpandedSectorSelect] = useState(false)

  // Validation
  const [errors, setErrors] = useState<Record<string, string>>({})

  const passwordValidation = validatePassword(accountForm.password)

  // ─────────────────────────────────────────────────────────────────────────
  // VALIDATION & NAVIGATION
  // ─────────────────────────────────────────────────────────────────────────

  const canProceedStep1 =
    accountForm.firstName.trim().length > 0 &&
    accountForm.lastName.trim().length > 0 &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(accountForm.email) &&
    passwordValidation.valid &&
    accountForm.password === accountForm.confirmPassword &&
    accountForm.acceptTerms

  const canProceedStep2 =
    orgForm.organizationName.trim().length > 0 &&
    orgForm.sector.length > 0 &&
    orgForm.country.length > 0 &&
    orgForm.size.length > 0

  const handleNextStep = () => {
    setGeneralError('')
    if (currentStep === 'account') {
      // Validate account form
      const newErrors: Record<string, string> = {}
      if (!accountForm.firstName.trim()) newErrors.firstName = 'Prénom requis'
      if (!accountForm.lastName.trim()) newErrors.lastName = 'Nom requis'
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(accountForm.email)) newErrors.email = 'Email invalide'
      if (!passwordValidation.valid) newErrors.password = passwordValidation.errors[0] || 'Mot de passe invalide'
      if (accountForm.password !== accountForm.confirmPassword)
        newErrors.confirmPassword = 'Les mots de passe ne correspondent pas'
      if (!accountForm.acceptTerms) newErrors.terms = 'Vous devez accepter les conditions'

      if (Object.keys(newErrors).length > 0) {
        setErrors(newErrors)
        return
      }
      setErrors({})

      if (isInviteMode) {
        setCurrentStep('confirm')
      } else {
        setCurrentStep('organization')
      }
    } else if (currentStep === 'organization') {
      const newErrors: Record<string, string> = {}
      if (!orgForm.organizationName.trim()) newErrors.organizationName = 'Nom requis'
      if (!orgForm.sector) newErrors.sector = 'Secteur requis'
      if (!orgForm.country) newErrors.country = 'Pays requis'
      if (!orgForm.size) newErrors.size = 'Taille requise'

      if (Object.keys(newErrors).length > 0) {
        setErrors(newErrors)
        return
      }
      setErrors({})
      setCurrentStep('plan')
    } else if (currentStep === 'plan') {
      setCurrentStep('confirm')
    }
  }

  const handlePreviousStep = () => {
    setGeneralError('')
    if (currentStep === 'organization') {
      setCurrentStep('account')
    } else if (currentStep === 'plan') {
      setCurrentStep('organization')
    } else if (currentStep === 'confirm') {
      if (isInviteMode) {
        setCurrentStep('account')
      } else {
        setCurrentStep('plan')
      }
    }
  }

  const handleGoToStep = (step: StandardStep | InviteStep) => {
    setGeneralError('')
    setCurrentStep(step)
  }

  // ─────────────────────────────────────────────────────────────────────────
  // SUBMISSION
  // ─────────────────────────────────────────────────────────────────────────

  const handleSubmit = async () => {
    setGeneralError('')
    setIsLoading(true)

    try {
      const fullName = `${accountForm.firstName.trim()} ${accountForm.lastName.trim()}`

      // Call registration API
      // Tokens are returned as httpOnly cookies, not in response body
      await register(accountForm.email, accountForm.password, fullName)

      // Redirect to dashboard after success
      setTimeout(() => {
        router.push('/dashboard')
      }, 500)
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : 'Erreur lors de la création du compte'
      setGeneralError(message)
      setIsLoading(false)
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER HELPERS
  // ─────────────────────────────────────────────────────────────────────────

  const renderLeftPanel = () => {
    if (currentStep === 'account') {
      return (
        <AuthLeftPanel
          headline={isInviteMode ? `Rejoignez ${inviteEmail?.split('@')[1] || 'votre organisation'}` : 'Créez votre compte'}
          subtext={
            isInviteMode
              ? 'Vous avez été invité à rejoindre cet espace TenderAI. Créez votre accès en quelques secondes.'
              : 'Rejoignez les équipes qui remportent plus de marchés publics.'
          }
          features={
            isInviteMode
              ? [
                  'Accès immédiat à l\'espace de votre organisation',
                  'Rôle et permissions définis par votre administrateur',
                  'Aucune carte bancaire requise',
                ]
              : [
                  'Essai gratuit 14 jours — aucune carte requise',
                  'Déploiement en moins de 5 minutes',
                  'Support FR/AR/EN inclus',
                  'Données hébergées en région MENA',
                ]
          }
          inviteBadge={
            isInviteMode
              ? {
                  orgName: inviteEmail?.split('@')[1] || 'votre organisation',
                  email: inviteEmail || '',
                }
              : undefined
          }
        />
      )
    } else if (currentStep === 'organization') {
      return (
        <AuthLeftPanel
          headline="Votre organisation"
          subtext="Ces informations nous permettent de personnaliser TenderAI pour votre contexte métier."
          features={[
            'Isolation complète des données par organisation',
            'RBAC granulaire — 6 rôles hiérarchiques',
            'Support des marchés TUNEPS, CNSS, GCC',
            'Multi-filiales disponible en plan Entreprise',
          ]}
        />
      )
    } else if (currentStep === 'plan') {
      return (
        <AuthLeftPanel
          headline="Choisissez votre formule"
          subtext="Commencez avec 14 jours d'essai gratuit sur n'importe quel plan. Aucune carte bancaire requise."
          features={[
            '14 jours d\'essai gratuit — sans engagement',
            'Changement de plan possible à tout moment',
            'Annulation en 1 clic',
            'Migration de données incluse si upgrade',
          ]}
        />
      )
    } else {
      return (
        <AuthLeftPanel
          headline={isInviteMode ? 'Presque terminé !' : 'Presque terminé !'}
          subtext={isInviteMode ? 'Confirmez vos informations pour rejoindre l\'organisation.' : 'Vérifiez vos informations avant de créer votre compte.'}
        />
      )
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // MAIN RENDER
  // ─────────────────────────────────────────────────────────────────────────

  const stepsToShow = isInviteMode ? inviteSteps : standardSteps

  return (
    <div className="min-h-screen w-full flex">
      {/* LEFT PANEL */}
      {renderLeftPanel()}

      {/* RIGHT PANEL — Cream */}
      <div className="w-full lg:w-[60%] bg-cream flex flex-col justify-between p-8 lg:p-12 overflow-y-auto">
        <div className="max-w-md mx-auto w-full">
          {/* Mobile Logo */}
          <div className="lg:hidden mb-8">
            <TenderAILogo size="md" theme="dark" />
          </div>

          {/* Step indicator */}
          <StepIndicator steps={stepsToShow} currentStep={currentStep} />

          {/* General error alert */}
          {generalError && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3 bg-danger/10 border border-danger/20 rounded-lg text-xs text-danger flex items-start gap-2 mb-6"
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{generalError}</span>
            </motion.div>
          )}

          {/* ─────────────────────────────────────────────────────────────────────────
              STEP 1 — ACCOUNT
              ───────────────────────────────────────────────────────────────────────── */}
          {currentStep === 'account' && (
            <motion.div
              key="account"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <h1 className="font-heading font-bold text-2xl text-navy mb-1">
                {isInviteMode ? 'Créez votre accès' : 'Votre identité'}
              </h1>
              <p className="text-sm text-muted mb-6">
                {isInviteMode ? 'Renseignez vos données personnelles' : 'Renseignez vos données personnelles'}
              </p>

              {/* Name fields — 2 columns */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                {/* First name */}
                <div>
                  <label htmlFor="firstName" className="block text-xs font-semibold text-navy mb-1.5">
                    Prénom
                  </label>
                  <input
                    id="firstName"
                    type="text"
                    value={accountForm.firstName}
                    onChange={(e) => setAccountForm({ ...accountForm, firstName: e.target.value })}
                    placeholder="John"
                    className={`w-full px-4 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:border-amber transition-all ${
                      errors.firstName ? 'border-danger focus:ring-danger/25' : 'border-cream-border focus:ring-amber/25 focus:border-amber'
                    }`}
                  />
                  {errors.firstName && (
                    <p className="text-xs text-danger mt-1 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {errors.firstName}
                    </p>
                  )}
                </div>

                {/* Last name */}
                <div>
                  <label htmlFor="lastName" className="block text-xs font-semibold text-navy mb-1.5">
                    Nom
                  </label>
                  <input
                    id="lastName"
                    type="text"
                    value={accountForm.lastName}
                    onChange={(e) => setAccountForm({ ...accountForm, lastName: e.target.value })}
                    placeholder="Doe"
                    className={`w-full px-4 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:border-amber transition-all ${
                      errors.lastName ? 'border-danger focus:ring-danger/25' : 'border-cream-border focus:ring-amber/25 focus:border-amber'
                    }`}
                  />
                  {errors.lastName && (
                    <p className="text-xs text-danger mt-1 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {errors.lastName}
                    </p>
                  )}
                </div>
              </div>

              {/* Email field */}
              <div className="mb-4">
                <label htmlFor="email" className="block text-xs font-semibold text-navy mb-1.5">
                  Adresse email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
                  <input
                    id="email"
                    type="email"
                    value={accountForm.email}
                    onChange={(e) => setAccountForm({ ...accountForm, email: e.target.value })}
                    disabled={isInviteMode}
                    placeholder="vous@entreprise.tn"
                    className={`w-full pl-10 pr-4 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:border-amber transition-all ${
                      isInviteMode ? 'bg-cream-bg text-muted/60' : ''
                    } ${errors.email ? 'border-danger focus:ring-danger/25' : 'border-cream-border focus:ring-amber/25 focus:border-amber'}`}
                  />
                </div>
                {isInviteMode && <p className="text-xs text-muted mt-1">Email défini par votre invitation</p>}
                {errors.email && (
                  <p className="text-xs text-danger mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {errors.email}
                  </p>
                )}
              </div>

              {/* Password field */}
              <div className="mb-2">
                <label htmlFor="password" className="block text-xs font-semibold text-navy mb-1.5">
                  Mot de passe
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={accountForm.password}
                    onChange={(e) => setAccountForm({ ...accountForm, password: e.target.value })}
                    onFocus={() => setPasswordFocused(true)}
                    onBlur={() => setPasswordFocused(false)}
                    maxLength={PASSWORD_RULES.maxLength}
                    placeholder="••••••••••••"
                    className={`w-full pl-10 pr-10 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:border-amber transition-all ${
                      errors.password ? 'border-danger focus:ring-danger/25' : 'border-cream-border focus:ring-amber/25 focus:border-amber'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-navy transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>

                {/* Password strength bar */}
                {accountForm.password.length > 0 && (
                  <div className="flex gap-1 mt-2">
                    {[1, 2, 3, 4].map((i) => {
                      const colors = {
                        0: 'bg-cream-border',
                        1: 'bg-danger',
                        2: 'bg-amber',
                        3: 'bg-amber-light',
                        4: 'bg-success',
                      }
                      return (
                        <div
                          key={i}
                          className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                            i <= passwordValidation.strength
                              ? colors[passwordValidation.strength]
                              : 'bg-cream-border'
                          }`}
                        />
                      )
                    })}
                  </div>
                )}

                {/* Password rules checklist */}
                {(passwordFocused || accountForm.password.length > 0) && (
                  <ul className="mt-2 space-y-1">
                    {PASSWORD_RULES_UI.map((rule, i) => {
                      const passed = rule.test(accountForm.password)
                      return (
                        <li key={i} className="flex items-center gap-2 text-xs transition-colors">
                          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                            <circle
                              cx="8"
                              cy="8"
                              r="7"
                              fill={passed ? 'rgba(30,124,90,0.15)' : 'rgba(0,0,0,0.05)'}
                            />
                            <path
                              d="M5 8l2.5 2.5L11 5"
                              stroke={passed ? '#1E7C5A' : '#D0CBC4'}
                              strokeWidth="1.3"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                          <span className={passed ? 'text-success' : 'text-muted'}>{rule.label}</span>
                        </li>
                      )
                    })}
                  </ul>
                )}

                {/* Security note */}
                <p className="text-[10px] text-muted/60 flex items-center gap-1.5 mt-3">
                  <svg
                    width="10"
                    height="10"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden="true"
                  >
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                  Mot de passe chiffré avec Argon2id · Jamais stocké en clair
                </p>
              </div>

              {/* Confirm password field */}
              <div className="mb-4">
                <label htmlFor="confirmPassword" className="block text-xs font-semibold text-navy mb-1.5">
                  Confirmer le mot de passe
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
                  <input
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={accountForm.confirmPassword}
                    onChange={(e) => setAccountForm({ ...accountForm, confirmPassword: e.target.value })}
                    maxLength={PASSWORD_RULES.maxLength}
                    placeholder="••••••••••••"
                    className={`w-full pl-10 pr-10 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:border-amber transition-all ${
                      errors.confirmPassword ? 'border-danger focus:ring-danger/25' : 'border-cream-border focus:ring-amber/25 focus:border-amber'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-navy transition-colors"
                  >
                    {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>

                {/* Password match feedback */}
                {accountForm.confirmPassword.length > 0 &&
                  (accountForm.password === accountForm.confirmPassword ? (
                    <p className="text-xs text-success mt-1 flex items-center gap-1">
                      <Check className="w-3 h-3" />
                      Les mots de passe correspondent
                    </p>
                  ) : (
                    <p className="text-xs text-danger mt-1 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      Les mots de passe ne correspondent pas
                    </p>
                  ))}
              </div>

              {/* Terms checkbox */}
              {!isInviteMode && (
                <label className="flex items-start gap-3 cursor-pointer mb-6">
                  <input
                    type="checkbox"
                    checked={accountForm.acceptTerms}
                    onChange={(e) => setAccountForm({ ...accountForm, acceptTerms: e.target.checked })}
                    className="mt-0.5 accent-amber"
                  />
                  <span className="text-xs text-muted">
                    J'accepte les{' '}
                    <Link href="/terms" className="text-amber hover:underline">
                      Conditions d'utilisation
                    </Link>
                    {' '}et la{' '}
                    <Link href="/privacy" className="text-amber hover:underline">
                      Politique de confidentialité
                    </Link>
                  </span>
                </label>
              )}

              {errors.terms && (
                <p className="text-xs text-danger mb-4 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  {errors.terms}
                </p>
              )}

              {/* Submit button */}
              <button
                onClick={handleNextStep}
                disabled={!canProceedStep1 || isLoading}
                className="w-full py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all shadow-amber disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 mb-4"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Continuer'}
                {!isLoading && <ArrowRight className="w-4 h-4" />}
              </button>

              {/* Already have account link */}
              <p className="text-center text-xs text-muted">
                Déjà un compte ?{' '}
                <Link href="/login" className="text-amber font-semibold hover:text-amber-light">
                  Se connecter
                </Link>
              </p>
            </motion.div>
          )}

          {/* ─────────────────────────────────────────────────────────────────────────
              STEP 2 — ORGANIZATION (Standard mode only)
              ───────────────────────────────────────────────────────────────────────── */}
          {currentStep === 'organization' && (
            <motion.div
              key="organization"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <h1 className="font-heading font-bold text-2xl text-navy mb-1">Votre organisation</h1>
              <p className="text-sm text-muted mb-6">Décrivez le contexte de votre équipe</p>

              {/* Organization name */}
              <div className="mb-4">
                <label htmlFor="orgName" className="block text-xs font-semibold text-navy mb-1.5">
                  Nom de l'organisation
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
                  <input
                    id="orgName"
                    type="text"
                    value={orgForm.organizationName}
                    onChange={(e) => setOrgForm({ ...orgForm, organizationName: e.target.value })}
                    placeholder="Ex: Groupe Sfax Industries"
                    className={`w-full pl-10 pr-4 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-2 focus:border-amber transition-all ${
                      errors.organizationName ? 'border-danger focus:ring-danger/25' : 'border-cream-border focus:ring-amber/25 focus:border-amber'
                    }`}
                  />
                </div>
                {errors.organizationName && (
                  <p className="text-xs text-danger mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {errors.organizationName}
                  </p>
                )}
              </div>

              {/* Sector select */}
              <div className="mb-4">
                <label className="block text-xs font-semibold text-navy mb-1.5">Secteur d'activité</label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setExpandedSectorSelect(!expandedSectorSelect)}
                    className={`w-full px-4 py-3 rounded-xl border bg-white text-sm text-left text-navy flex items-center justify-between transition-all ${
                      errors.sector ? 'border-danger focus:ring-danger/25' : 'border-cream-border focus:ring-amber/25 focus:border-amber'
                    }`}
                  >
                    <span className={orgForm.sector ? 'text-navy' : 'text-muted/50'}>
                      {orgForm.sector || 'Sélectionner un secteur'}
                    </span>
                    <ChevronDown className={`w-4 h-4 transition-transform ${expandedSectorSelect ? 'rotate-180' : ''}`} />
                  </button>
                  {expandedSectorSelect && (
                    <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-cream-border rounded-xl shadow-lg z-50">
                      {SECTORS.map((sector) => (
                        <button
                          key={sector}
                          type="button"
                          onClick={() => {
                            setOrgForm({ ...orgForm, sector })
                            setExpandedSectorSelect(false)
                          }}
                          className="w-full text-left px-4 py-3 text-sm text-navy hover:bg-cream transition-colors first:rounded-t-xl last:rounded-b-xl"
                        >
                          {sector}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {errors.sector && (
                  <p className="text-xs text-danger mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {errors.sector}
                  </p>
                )}
              </div>

              {/* Country select */}
              <div className="mb-4">
                <label className="block text-xs font-semibold text-navy mb-1.5">Pays principal</label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setExpandedCountrySelect(!expandedCountrySelect)}
                    className={`w-full px-4 py-3 rounded-xl border bg-white text-sm text-left text-navy flex items-center justify-between transition-all ${
                      errors.country ? 'border-danger focus:ring-danger/25' : 'border-cream-border focus:ring-amber/25 focus:border-amber'
                    }`}
                  >
                    <span className={orgForm.country ? 'text-navy' : 'text-muted/50'}>
                      {COUNTRIES.find((c) => c.value === orgForm.country)?.label || 'Sélectionner un pays'}
                    </span>
                    <Globe className="w-4 h-4" />
                  </button>
                  {expandedCountrySelect && (
                    <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-cream-border rounded-xl shadow-lg z-50">
                      {COUNTRIES.map((country) => (
                        <button
                          key={country.value}
                          type="button"
                          onClick={() => {
                            setOrgForm({ ...orgForm, country: country.value })
                            setExpandedCountrySelect(false)
                          }}
                          className="w-full text-left px-4 py-3 text-sm text-navy hover:bg-cream transition-colors first:rounded-t-xl last:rounded-b-xl"
                        >
                          {country.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {errors.country && (
                  <p className="text-xs text-danger mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {errors.country}
                  </p>
                )}
              </div>

              {/* Organization size — radio pills */}
              <div className="mb-4">
                <label className="block text-xs font-semibold text-navy mb-2">Taille de l'organisation</label>
                <div className="flex flex-wrap gap-2">
                  {SIZES.map((size) => (
                    <button
                      key={size}
                      type="button"
                      onClick={() => setOrgForm({ ...orgForm, size })}
                      className={`px-4 py-2 rounded-full text-sm font-medium border transition-all ${
                        orgForm.size === size
                          ? 'bg-amber text-white border-amber'
                          : 'bg-white text-navy border-cream-border hover:border-amber/50'
                      }`}
                    >
                      {size}
                    </button>
                  ))}
                </div>
                {errors.size && (
                  <p className="text-xs text-danger mt-1 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {errors.size}
                  </p>
                )}
              </div>

              {/* Portals — multi-select checkboxes */}
              <div className="mb-6">
                <label className="block text-xs font-semibold text-navy mb-2">Portails d'appels d'offres utilisés</label>
                <div className="grid grid-cols-2 gap-2">
                  {PORTALS.map((portal) => (
                    <label key={portal} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={orgForm.portals.includes(portal)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setOrgForm({ ...orgForm, portals: [...orgForm.portals, portal] })
                          } else {
                            setOrgForm({
                              ...orgForm,
                              portals: orgForm.portals.filter((p) => p !== portal),
                            })
                          }
                        }}
                        className="accent-amber"
                      />
                      <span className="text-xs text-navy">{portal}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Navigation buttons */}
              <div className="flex gap-3">
                <button
                  onClick={handlePreviousStep}
                  className="flex-1 py-3.5 bg-white text-navy font-semibold rounded-xl border border-cream-border hover:border-amber/50 transition-all flex items-center justify-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Retour
                </button>
                <button
                  onClick={handleNextStep}
                  disabled={!canProceedStep2 || isLoading}
                  className="flex-1 py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  Continuer
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}

          {/* ─────────────────────────────────────────────────────────────────────────
              STEP 3 — PLAN (Standard mode only)
              ───────────────────────────────────────────────────────────────────────── */}
          {currentStep === 'plan' && (
            <motion.div
              key="plan"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <h1 className="font-heading font-bold text-2xl text-navy mb-1">Choisissez votre formule</h1>
              <p className="text-sm text-muted mb-6">Démarrez avec 14 jours d'essai gratuit</p>

              {/* Plan cards */}
              <div className="space-y-3 mb-4">
                {PLANS.map((plan) => (
                  <button
                    key={plan.id}
                    type="button"
                    onClick={() => setSelectedPlan(plan.id)}
                    className={`relative p-5 rounded-2xl border-2 cursor-pointer transition-all w-full text-left ${
                      selectedPlan === plan.id
                        ? 'border-amber bg-amber/5'
                        : 'border-cream-border bg-white hover:border-amber/40'
                    }`}
                  >
                    {plan.recommended && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-amber text-white text-xs font-semibold px-3 py-1 rounded-full whitespace-nowrap">
                        Recommandé
                      </div>
                    )}

                    {selectedPlan === plan.id && (
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

                    <div className="font-heading font-bold text-navy mb-1">{plan.title}</div>
                    <div className="text-amber font-semibold text-sm mb-2">{plan.price}</div>
                    <p className="text-xs text-muted mb-3">{plan.description}</p>

                    <ul className="space-y-1">
                      {plan.highlights.map((h, i) => (
                        <li key={i} className="flex items-center gap-2 text-xs text-navy">
                          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                            <circle
                              cx="8"
                              cy="8"
                              r="7"
                              fill={selectedPlan === plan.id ? 'rgba(196,150,42,0.15)' : '#E8F5EF'}
                            />
                            <path
                              d="M5 8l2.5 2.5L11 5"
                              stroke={selectedPlan === plan.id ? '#C4962A' : '#1E7C5A'}
                              strokeWidth="1.3"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                          {h}
                        </li>
                      ))}
                    </ul>
                  </button>
                ))}
              </div>

              {/* Trial notice */}
              <div className="flex items-center gap-2 p-3 bg-success/10 border border-success/20 rounded-lg mb-6">
                <Check className="w-4 h-4 text-success flex-shrink-0" />
                <p className="text-xs text-success font-medium">
                  14 jours d'essai gratuit inclus — aucune carte bancaire requise
                </p>
              </div>

              {/* Link to pricing */}
              <p className="text-center text-xs text-muted mb-6">
                <Link href="/pricing" target="_blank" className="text-amber hover:underline">
                  Voir la comparaison complète →
                </Link>
              </p>

              {/* Navigation buttons */}
              <div className="flex gap-3">
                <button
                  onClick={handlePreviousStep}
                  className="flex-1 py-3.5 bg-white text-navy font-semibold rounded-xl border border-cream-border hover:border-amber/50 transition-all flex items-center justify-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Retour
                </button>
                <button
                  onClick={handleNextStep}
                  disabled={isLoading}
                  className="flex-1 py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  Continuer
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}

          {/* ─────────────────────────────────────────────────────────────────────────
              STEP 4 — CONFIRM
              ───────────────────────────────────────────────────────────────────────── */}
          {currentStep === 'confirm' && (
            <motion.div
              key="confirm"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {isInviteMode ? (
                <>
                  <h1 className="font-heading text-2xl font-bold text-navy mb-6">
                    Rejoindre {inviteEmail?.split('@')[1] || 'votre organisation'}
                  </h1>

                  {/* Invite summary */}
                  <div className="bg-white border border-cream-border rounded-xl p-4 flex items-center gap-4 mb-4">
                    <div className="w-10 h-10 bg-amber/10 rounded-full flex items-center justify-center flex-shrink-0">
                      <Users className="w-5 h-5 text-amber" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-navy">
                        {inviteEmail?.split('@')[1] || 'votre organisation'}
                      </div>
                      <div className="text-xs text-muted">Invitation valide · Accès immédiat</div>
                    </div>
                  </div>

                  {/* Account summary */}
                  <div className="bg-white border border-cream-border rounded-xl p-4 mb-6">
                    <div className="text-sm text-navy font-semibold">
                      {accountForm.firstName} {accountForm.lastName}
                    </div>
                    <div className="text-xs text-muted">{accountForm.email}</div>
                  </div>

                  {/* Submit button */}
                  <button
                    onClick={handleSubmit}
                    disabled={isLoading}
                    className="w-full py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all shadow-amber disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 mb-4"
                  >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Rejoindre l\'organisation'}
                    {!isLoading && <ArrowRight className="w-4 h-4" />}
                  </button>
                </>
              ) : (
                <>
                  <h1 className="font-heading text-2xl font-bold text-navy mb-6">Vérification</h1>

                  {/* Account summary */}
                  <div className="bg-white border border-cream-border rounded-xl p-4 mb-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-semibold text-navy uppercase tracking-wide">Compte</span>
                      <button
                        onClick={() => handleGoToStep('account')}
                        className="text-xs text-amber hover:underline"
                      >
                        Modifier
                      </button>
                    </div>
                    <div className="text-sm text-navy font-semibold">
                      {accountForm.firstName} {accountForm.lastName}
                    </div>
                    <div className="text-xs text-muted">{accountForm.email}</div>
                  </div>

                  {/* Organization summary */}
                  <div className="bg-white border border-cream-border rounded-xl p-4 mb-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-semibold text-navy uppercase tracking-wide">Organisation</span>
                      <button
                        onClick={() => handleGoToStep('organization')}
                        className="text-xs text-amber hover:underline"
                      >
                        Modifier
                      </button>
                    </div>
                    <div className="text-sm text-navy font-semibold">{orgForm.organizationName}</div>
                    <div className="text-xs text-muted">
                      {orgForm.sector} · {COUNTRIES.find((c) => c.value === orgForm.country)?.label} ·{' '}
                      {orgForm.size} employés
                    </div>
                  </div>

                  {/* Plan summary */}
                  <div className="bg-white border border-cream-border rounded-xl p-4 mb-6">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-semibold text-navy uppercase tracking-wide">Formule</span>
                      <button
                        onClick={() => handleGoToStep('plan')}
                        className="text-xs text-amber hover:underline"
                      >
                        Modifier
                      </button>
                    </div>
                    <div className="text-sm text-navy font-semibold">
                      {PLANS.find((p) => p.id === selectedPlan)?.title}
                    </div>
                    <div className="text-xs text-muted">
                      {PLANS.find((p) => p.id === selectedPlan)?.price} · 14 jours gratuits
                    </div>
                  </div>

                  {/* Submit button */}
                  <button
                    onClick={handleSubmit}
                    disabled={isLoading}
                    className="w-full py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all shadow-amber disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 mb-4"
                  >
                    {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Créer mon compte'}
                    {!isLoading && <ArrowRight className="w-4 h-4" />}
                  </button>
                </>
              )}

              {/* Back button */}
              <button
                onClick={handlePreviousStep}
                className="w-full py-3.5 bg-white text-navy font-semibold rounded-xl border border-cream-border hover:border-amber/50 transition-all flex items-center justify-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Retour
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}
