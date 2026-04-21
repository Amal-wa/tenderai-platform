'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { motion } from 'framer-motion'
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowRight,
  Loader,
} from 'lucide-react'
import {
  step1Schema,
  type Step1Data,
} from '@/lib/validations/register'
import { getPasswordStrength } from '@/lib/utils/passwordStrength'
import { detectDomainOrg } from '@/lib/utils/domainDetect'
import { useCheckEmail } from '@/hooks/useCheckEmail'

interface Step1FormProps {
  onSubmit: (data: Step1Data) => void
  isLoading?: boolean
  defaultValues?: Partial<Step1Data>
}

export default function Step1Form({
  onSubmit,
  isLoading = false,
  defaultValues,
}: Step1FormProps): JSX.Element {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isValid },
  } = useForm<Step1Data>({
    resolver: zodResolver(step1Schema),
    mode: 'onBlur',
    defaultValues: {
      firstName: defaultValues?.firstName || '',
      lastName: defaultValues?.lastName || '',
      email: defaultValues?.email || '',
      password: defaultValues?.password || '',
      confirmPassword: defaultValues?.confirmPassword || '',
      acceptTerms: defaultValues?.acceptTerms || false,
    },
  })

  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [domainMatch, setDomainMatch] = useState<{ orgName: string; sector: string } | null>(null)

  const password = watch('password')
  const email = watch('email')
  const passwordStrength = getPasswordStrength(password)

  // 📧 Vérifier l'unicité de l'email en temps réel (débounce 500ms)
  const { exists, isLoading: emailCheckLoading, error: emailCheckError } = useCheckEmail(email)

  const handleEmailBlur = () => {
    const match = detectDomainOrg(email)
    setDomainMatch(match)
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
    >
      <h1 className="text-2xl font-bold text-navy mb-2">Votre identité</h1>
      <p className="text-muted text-sm mb-6">
        Renseignez vos données personnelles
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Name fields — 2 cols */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="firstName" className="block text-xs font-semibold text-navy mb-1.5">
              Prénom
            </label>
            <input
              {...register('firstName')}
              id="firstName"
              type="text"
              placeholder="John"
              className={`w-full px-4 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-3 transition-all ${
                errors.firstName
                  ? 'border-danger focus:ring-danger/20'
                  : 'border-cream-border focus:ring-amber/20 focus:border-amber'
              }`}
            />
            {errors.firstName && (
              <p className="text-xs text-danger mt-1 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.firstName.message}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="lastName" className="block text-xs font-semibold text-navy mb-1.5">
              Nom
            </label>
            <input
              {...register('lastName')}
              id="lastName"
              type="text"
              placeholder="Doe"
              className={`w-full px-4 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-3 transition-all ${
                errors.lastName
                  ? 'border-danger focus:ring-danger/20'
                  : 'border-cream-border focus:ring-amber/20 focus:border-amber'
              }`}
            />
            {errors.lastName && (
              <p className="text-xs text-danger mt-1 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {errors.lastName.message}
              </p>
            )}
          </div>
        </div>

        {/* SSO buttons row */}
        <div className="flex gap-2 mb-4">
          <button
            type="button"
            onClick={() => console.warn('SSO not yet configured')}
            className="flex-1 py-2.5 border border-cream-border rounded-lg hover:border-amber/50 transition-colors flex items-center justify-center gap-2 text-sm font-medium text-navy"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="12" cy="12" r="10" opacity="0.2" />
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" />
            </svg>
            Google
          </button>
          <button
            type="button"
            onClick={() => console.warn('SSO not yet configured')}
            className="flex-1 py-2.5 border border-cream-border rounded-lg hover:border-amber/50 transition-colors flex items-center justify-center gap-2 text-sm font-medium text-navy"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11.4 24H0V0h11.4c6.3 0 11.4 5.1 11.4 11.4S17.7 24 11.4 24z" opacity="0.5" />
              <path d="M24 0h-11.4v24H24c6.3 0 11.4-5.1 11.4-11.4S30.3 0 24 0z" opacity="0.3" />
            </svg>
            Microsoft
          </button>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3 my-4">
          <div className="flex-1 h-px bg-cream-border" />
          <span className="text-xs text-muted">ou par email</span>
          <div className="flex-1 h-px bg-cream-border" />
        </div>

        {/* Email field */}
        <div>
          <label htmlFor="email" className="block text-xs font-semibold text-navy mb-1.5">
            Adresse email
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
            <input
              {...register('email')}
              id="email"
              type="email"
              onBlur={handleEmailBlur}
              placeholder="vous@entreprise.tn"
              className={`w-full pl-10 pr-10 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-3 transition-all ${
                exists || errors.email
                  ? 'border-danger focus:ring-danger/20'
                  : 'border-cream-border focus:ring-amber/20 focus:border-amber'
              }`}
            />
            {emailCheckLoading && (
              <Loader className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-amber animate-spin pointer-events-none" />
            )}
          </div>

          {/* Domain match notification */}
          {domainMatch && !exists && !emailCheckError && (
            <div className="mt-2 p-3 bg-amber/10 border border-amber/20 rounded-lg text-xs text-amber">
              Domaine <strong>{domainMatch.orgName}</strong> détecté — organisation pré-remplie à l'étape suivante
            </div>
          )}

          {/* Email already exists error */}
          {exists && (
            <p className="text-xs text-danger mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              Un compte avec cet email existe déjà
            </p>
          )}

          {/* Email check request error */}
          {emailCheckError && (
            <p className="text-xs text-danger mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {emailCheckError}
            </p>
          )}

          {/* Validation error */}
          {errors.email && !exists && !emailCheckError && (
            <p className="text-xs text-danger mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {errors.email.message}
            </p>
          )}
        </div>

        {/* Password field */}
        <div>
          <label htmlFor="password" className="block text-xs font-semibold text-navy mb-1.5">
            Mot de passe
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
            <input
              {...register('password')}
              id="password"
              type={showPassword ? 'text' : 'password'}
              placeholder="••••••••••••"
              className={`w-full pl-10 pr-10 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-3 transition-all ${
                errors.password
                  ? 'border-danger focus:ring-danger/20'
                  : 'border-cream-border focus:ring-amber/20 focus:border-amber'
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
          {password && (
            <div className="flex gap-1 mt-2">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className={`h-1 flex-1 rounded-full transition-all ${
                    i <= passwordStrength.score
                      ? `bg-[${passwordStrength.color}]`
                      : 'bg-cream-border'
                  }`}
                  style={{
                    backgroundColor: i <= passwordStrength.score
                      ? passwordStrength.color
                      : undefined,
                  }}
                />
              ))}
            </div>
          )}

          {/* Security note */}
          <p className="text-[10px] text-muted/60 flex items-center gap-1.5 mt-2">
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
        <div>
          <label htmlFor="confirmPassword" className="block text-xs font-semibold text-navy mb-1.5">
            Confirmer le mot de passe
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
            <input
              {...register('confirmPassword')}
              id="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              placeholder="••••••••••••"
              className={`w-full pl-10 pr-10 py-3 rounded-xl border bg-white text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:ring-3 transition-all ${
                errors.confirmPassword
                  ? 'border-danger focus:ring-danger/20'
                  : 'border-cream-border focus:ring-amber/20 focus:border-amber'
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
          {errors.confirmPassword && (
            <p className="text-xs text-danger mt-1 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {errors.confirmPassword.message}
            </p>
          )}
        </div>

        {/* Terms checkbox */}
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            {...register('acceptTerms')}
            type="checkbox"
            className="mt-1 accent-amber"
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
        {errors.acceptTerms && (
          <p className="text-xs text-danger flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {errors.acceptTerms.message}
          </p>
        )}

        {/* Submit button */}
        <button
          type="submit"
          disabled={!isValid || isLoading || exists || emailCheckLoading}
          className="w-full py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all shadow-lg shadow-amber/30 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-6"
        >
          Continuer
          <ArrowRight className="w-4 h-4" />
        </button>

        {/* Already have account link */}
        <p className="text-center text-xs text-muted mt-4">
          Déjà un compte ?{' '}
          <Link href="/login" className="text-amber font-semibold hover:text-amber-light">
            Se connecter
          </Link>
        </p>
      </form>
    </motion.div>
  )
}
