'use client'

export const dynamic = 'force-dynamic'

import { Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import AuthLeftPanel from '@/components/auth/AuthLeftPanel'
import { extractErrorMessage } from '@/lib/api'
import { getPasswordStrength } from '@/lib/utils/passwordStrength'
import api from '@/lib/api'
import { Eye, EyeOff, Loader2 } from 'lucide-react'

// ──────────────────────────────────────────────────────────────────────────
// INVITATION ACCEPT SCHEMA
// ──────────────────────────────────────────────────────────────────────────

const invitationSchema = z
  .object({
    full_name: z
      .string()
      .min(1, 'Nom complet requis')
      .max(255, 'Nom trop long'),
    password: z
      .string()
      .min(12, '12 caractères minimum')
      .regex(/[A-Z]/, 'Une majuscule requise')
      .regex(/[0-9]/, 'Un chiffre requis')
      .regex(/[^A-Za-z0-9]/, 'Un caractère spécial requis'),
    confirmPassword: z.string(),
    acceptTerms: z.boolean().refine((v) => v === true, 'Obligatoire'),
  })
  .refine((d: any) => d.password === d.confirmPassword, {
    message: 'Les mots de passe ne correspondent pas',
    path: ['confirmPassword'],
  })

type InvitationFormData = z.infer<typeof invitationSchema>

export default function AcceptInvitationPage(): JSX.Element {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0F1C35]" />}>
      <AcceptInvitationInner />
    </Suspense>
  )
}

function AcceptInvitationInner(): JSX.Element {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  const [isLoading, setIsLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [passwordStrength, setPasswordStrength] = useState(0)
  const [apiError, setApiError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<InvitationFormData>({
    resolver: zodResolver(invitationSchema),
    mode: 'onBlur',
  })

  const password = watch('password')

  // Update password strength when password changes
  if (password) {
    const strength = getPasswordStrength(password)
    if (passwordStrength !== strength.score) {
      setPasswordStrength(strength.score)
    }
  }

  // Show error if token is missing
  if (!token || token.trim() === '') {
    return (
      <div className="min-h-screen w-full flex">
        <AuthLeftPanel
          headline="Lien d'invitation invalide"
          subtext={() =>
            'Le lien d\'invitation a expiré ou est invalide. Veuillez contacter votre administrateur.'
          }
          features={[
            'Les liens d\'invitation restent valides 7 jours',
            'Chaque lien ne peut être utilisé qu\'une seule fois',
            'Pour une nouvelle invitation, contactez votre administrateur',
          ]}
          footerNote="🔗 Problème d'accès?"
        />

        <div className="w-full lg:w-[60%] bg-cream flex flex-col justify-center items-center p-8 lg:p-12">
          <div className="max-w-md w-full text-center">
            <div className="mb-6 flex justify-center">
              <div className="w-16 h-16 bg-danger/10 rounded-full flex items-center justify-center">
                <svg
                  className="w-8 h-8 text-danger"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
            <h1 className="text-2xl font-semibold text-navy mb-3">
              Lien d'invitation invalide
            </h1>
            <p className="text-sm text-gray-600 mb-8">
              Le lien d'invitation a expiré ou est invalide. Veuillez contacter
              votre administrateur pour une nouvelle invitation.
            </p>
            <button
              onClick={() => router.push('/auth/login')}
              className="w-full px-4 py-3 bg-navy text-cream rounded-xl font-medium hover:bg-navy/90 transition-colors"
            >
              Retour à l'accueil
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Handle form submission
  const onSubmit = async (data: InvitationFormData) => {
    try {
      setIsLoading(true)
      setApiError(null)

      await api.post('/api/v1/auth/invite/accept', {
        token,
        full_name: data.full_name,
        password: data.password,
      })

      router.push('/register/setup-2fa')
    } catch (err: any) {
      const errorMessage = extractErrorMessage(err)
      setApiError(errorMessage)
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex">
      {/* LEFT PANEL */}
      <AuthLeftPanel
        headline="Accepter votre invitation"
        subtext={() =>
          'Créez votre compte TenderAI en acceptant cette invitation. Vous pourrez accéder à tous les documents tendres.'
        }
        features={[
          'Authentification à deux facteurs obligatoire',
          'Accès sécurisé avec Ed25519',
          'Chiffrement des données',
          'Conformité RGPD',
        ]}
        footerNote="🛡️ Votre sécurité est notre priorité"
      />

      {/* RIGHT PANEL — 60% Cream */}
      <div className="w-full lg:w-[60%] bg-cream flex flex-col justify-center p-8 lg:p-12 overflow-y-auto">
        <div className="max-w-md mx-auto w-full">
          {/* Heading */}
          <div className="mb-8">
            <h1 className="text-2xl lg:text-3xl font-semibold text-navy mb-2">
              Créer votre compte
            </h1>
            <p className="text-sm text-gray-600">
              Configurez votre compte en quelques étapes simples
            </p>
          </div>

          {/* API Error Alert */}
          {apiError && (
            <div className="p-3 bg-danger/10 border border-danger/20 rounded-lg text-xs text-danger flex items-start gap-2 mb-6">
              <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 12 12">
                <circle cx="6" cy="6" r="5" fill="currentColor" opacity="0.2" />
                <circle cx="6" cy="3.5" r="0.75" />
                <path d="M6 5.5v2" stroke="currentColor" strokeWidth="0.75" strokeLinecap="round" />
              </svg>
              {apiError}
            </div>
          )}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Full Name */}
            <div>
              <label
                htmlFor="full_name"
                className="block text-sm font-medium text-navy mb-2"
              >
                Nom complet <span className="text-danger">*</span>
              </label>
              <input
                id="full_name"
                type="text"
                placeholder="Jean Dupont"
                {...register('full_name')}
                className={`w-full px-4 py-3 border-2 rounded-xl font-medium transition-all ${
                  errors.full_name
                    ? 'border-danger/50 bg-danger/5 focus:ring-0'
                    : 'border-gray-200 bg-white focus:border-amber focus:ring-3 focus:ring-amber/10'
                } focus:outline-none`}
              />
              {errors.full_name && (
                <p className="text-xs text-danger mt-1">
                  {errors.full_name.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-navy mb-2"
              >
                Mot de passe <span className="text-danger">*</span>
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Créez un mot de passe sécurisé"
                  {...register('password')}
                  className={`w-full px-4 py-3 border-2 rounded-xl font-medium transition-all pr-12 ${
                    errors.password
                      ? 'border-danger/50 bg-danger/5 focus:ring-0'
                      : 'border-gray-200 bg-white focus:border-amber focus:ring-3 focus:ring-amber/10'
                  } focus:outline-none`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  {showPassword ? (
                    <Eye className="w-5 h-5" />
                  ) : (
                    <EyeOff className="w-5 h-5" />
                  )}
                </button>
              </div>
              {password && (
                <div className="mt-2">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          passwordStrength === 0
                            ? 'w-0'
                            : passwordStrength === 1
                              ? 'w-1/4 bg-danger'
                              : passwordStrength === 2
                                ? 'w-2/4 bg-warning'
                                : passwordStrength === 3
                                  ? 'w-3/4 bg-amber'
                                  : 'w-full bg-success'
                        }`}
                      />
                    </div>
                    <span className="text-xs text-gray-600">
                      {passwordStrength === 0
                        ? ''
                        : passwordStrength === 1
                          ? 'Très faible'
                          : passwordStrength === 2
                            ? 'Faible'
                            : passwordStrength === 3
                              ? 'Fort'
                              : 'Très fort'}
                    </span>
                  </div>
                  <ul className="text-xs text-gray-600 space-y-1">
                    <li
                      className={`flex items-center gap-2 ${
                        password.length >= 12
                          ? 'text-success'
                          : 'text-gray-400'
                      }`}
                    >
                      <span>{password.length >= 12 ? '✓' : '○'}</span>
                      12 caractères minimum
                    </li>
                    <li
                      className={`flex items-center gap-2 ${
                        /[A-Z]/.test(password)
                          ? 'text-success'
                          : 'text-gray-400'
                      }`}
                    >
                      <span>{/[A-Z]/.test(password) ? '✓' : '○'}</span>
                      Une majuscule
                    </li>
                    <li
                      className={`flex items-center gap-2 ${
                        /[0-9]/.test(password)
                          ? 'text-success'
                          : 'text-gray-400'
                      }`}
                    >
                      <span>{/[0-9]/.test(password) ? '✓' : '○'}</span>
                      Un chiffre
                    </li>
                    <li
                      className={`flex items-center gap-2 ${
                        /[^A-Za-z0-9]/.test(password)
                          ? 'text-success'
                          : 'text-gray-400'
                      }`}
                    >
                      <span>{/[^A-Za-z0-9]/.test(password) ? '✓' : '○'}</span>
                      Un caractère spécial
                    </li>
                  </ul>
                </div>
              )}
              {errors.password && (
                <p className="text-xs text-danger mt-1">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-navy mb-2"
              >
                Confirmer le mot de passe <span className="text-danger">*</span>
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirm ? 'text' : 'password'}
                  placeholder="Confirmez votre mot de passe"
                  {...register('confirmPassword')}
                  className={`w-full px-4 py-3 border-2 rounded-xl font-medium transition-all pr-12 ${
                    errors.confirmPassword
                      ? 'border-danger/50 bg-danger/5 focus:ring-0'
                      : 'border-gray-200 bg-white focus:border-amber focus:ring-3 focus:ring-amber/10'
                  } focus:outline-none`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  {showConfirm ? (
                    <Eye className="w-5 h-5" />
                  ) : (
                    <EyeOff className="w-5 h-5" />
                  )}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="text-xs text-danger mt-1">
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>

            {/* Accept Terms */}
            <div className="flex items-start gap-3 pt-2">
              <input
                id="acceptTerms"
                type="checkbox"
                {...register('acceptTerms')}
                className="mt-1 w-4 h-4 rounded border-gray-300 text-amber focus:ring-amber cursor-pointer"
              />
              <label
                htmlFor="acceptTerms"
                className="text-sm text-gray-700 cursor-pointer"
              >
                J'accepte les{' '}
                <a
                  href="/terms"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-amber hover:underline font-medium"
                >
                  conditions d'utilisation
                </a>{' '}
                et la{' '}
                <a
                  href="/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-amber hover:underline font-medium"
                >
                  politique de confidentialité
                </a>
              </label>
            </div>
            {errors.acceptTerms && (
              <p className="text-xs text-danger">
                {errors.acceptTerms.message}
              </p>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-6 px-4 py-3 bg-navy text-cream rounded-xl font-semibold hover:bg-navy/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Création en cours...
                </>
              ) : (
                'Créer mon compte'
              )}
            </button>

            {/* Already have account */}
            <p className="text-center text-sm text-gray-600 mt-4">
              Vous avez déjà un compte?{' '}
              <a
                href="/auth/login"
                className="text-amber hover:underline font-medium"
              >
                Se connecter
              </a>
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
