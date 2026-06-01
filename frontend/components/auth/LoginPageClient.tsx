'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { AlertTriangle, CheckCircle } from 'lucide-react'
import TenderAILogo from '@/components/ui/TenderAILogo'
import { login, extractErrorMessage } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import type { LoginResponse } from '@/types/auth'

export default function LoginPageClient() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { finalizeLogin } = useAuth()

  // Form state
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showSuccess, setShowSuccess] = useState(false)

  // 429 rate limit countdown
  const [rateLimitReset, setRateLimitReset] = useState<number | null>(null)
  const [rateLimitCountdown, setRateLimitCountdown] = useState<number>(0)
  const [loginDisabled, setLoginDisabled] = useState(false)

  // Check for account creation success message
  useEffect(() => {
    if (searchParams.get('message') === 'account_ready') {
      setShowSuccess(true)
    }
  }, [searchParams])

  // Countdown timer for 429 rate limit
  useEffect(() => {
    if (!rateLimitReset) return

    const interval = setInterval(() => {
      const secondsRemaining = Math.max(0, Math.ceil((rateLimitReset - Date.now()) / 1000))
      setRateLimitCountdown(secondsRemaining)

      if (secondsRemaining === 0) {
        setRateLimitReset(null)
        setLoginDisabled(false)
        setError(null)
        clearInterval(interval)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [rateLimitReset])

  const handleLoginSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)

    if (!email || !password) {
      setError('Veuillez remplir tous les champs')
      return
    }

    setIsLoading(true)
    try {
      const loginResp: LoginResponse = await login(email, password)

      if (loginResp.requires_2fa && loginResp.partial_token) {
        sessionStorage.setItem('partial_token', loginResp.partial_token)
        router.push('/2fa-login')
      } else {
        try {
          await finalizeLogin()
        } catch (err: unknown) {
          const errorMessage = extractErrorMessage(err)
          console.error('[LoginPageClient] finalizeLogin() failed:', errorMessage)
          setError('Connexion réussie mais profil inaccessible. Rechargez la page.')
        }
      }
    } catch (err: unknown) {
      const error = err as any
      const status = error?.response?.status

      if (!error?.response) {
        setError('Impossible de joindre le serveur. Vérifiez votre connexion.')
      } else if (status === 429) {
        const resetTimestamp = parseInt(error?.response?.headers?.['x-ratelimit-reset'] || '0', 10)
        if (resetTimestamp > 0) {
          setRateLimitReset(resetTimestamp * 1000)
          setLoginDisabled(true)
          const secondsRemaining = Math.max(0, Math.ceil((resetTimestamp - Date.now() / 1000)))
          setRateLimitCountdown(secondsRemaining)
          setError(null)
        } else {
          setError('Trop de tentatives. Réessayez dans quelques instants.')
        }
      } else if (status && status >= 500) {
        if (process.env.NODE_ENV === 'development') {
          const requestId = error?.response?.headers?.['x-request-id']
          console.error(`[${status}] X-Request-ID: ${requestId}`)
        }
        setError('Erreur serveur. Veuillez réessayer.')
      } else {
        setError('Nom d\'utilisateur ou mot de passe incorrect.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex">
      {/* LEFT PANEL — 40% Navy */}
      <div className="hidden lg:flex lg:w-[40%] bg-[#0F1C35] flex-col justify-between p-12 overflow-y-auto">
        {/* Top — Logo */}
        <div>
          <TenderAILogo size="lg" theme="dark" showText={true} />
        </div>

        {/* Middle — Headline + Features */}
        <div className="flex flex-col gap-8 my-8">
          {/* Headline */}
          <div>
            <h2 className="font-heading text-3xl font-bold text-white leading-tight mb-4">
              Gérez vos appels d&apos;offres
              <br />
              avec{' '}
              <span className="text-[#C4962A] italic">l&apos;intelligence</span>
              <br />
              qu&apos;ils méritent
            </h2>
            <p className="text-white/60 text-sm leading-relaxed">
              La plateforme IA pour les équipes qui remportent plus de marchés
              publics.
            </p>
          </div>

          {/* Features */}
          <ul className="space-y-3">
            {[
              'Ingestion intelligente PDF / Word / Excel',
              'Matrice de conformité auditable en temps réel',
              'Sécurité SOC2 · ISO 27001 · RGPD',
            ].map((item) => (
              <li key={item} className="flex items-start gap-3 text-sm text-white/80">
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
                {item}
              </li>
            ))}
          </ul>
        </div>

        {/* Bottom — Testimonial + Copyright */}
        <div className="space-y-6">
          {/* Testimonial Card */}
          <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
            <div className="flex gap-1 mb-3" aria-hidden="true">
              {[...Array(5)].map((_, i) => (
                <svg key={i} width="12" height="12" viewBox="0 0 14 14" fill="#C4962A">
                  <path d="M7 1l1.5 3.5L12 5l-2.5 2.5.6 3.5L7 9.5 3.9 11l.6-3.5L2 5l3.5-.5z" />
                </svg>
              ))}
            </div>
            <p className="text-white/80 text-sm leading-relaxed italic mb-4">
              &quot;TenderAI a réduit notre temps de préparation de 80%. On soumet
              maintenant 3× plus d&apos;AOs.&quot;
            </p>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-[#C4962A]/20 flex items-center justify-center text-xs font-bold text-[#C4962A]">
                HB
              </div>
              <div>
                <div className="text-xs font-semibold text-white">Hamed Bousselmi</div>
                <div className="text-xs text-white/40">DSI · STEG Tunisie</div>
              </div>
            </div>
          </div>

          {/* Copyright */}
          <div className="text-xs text-white/30">© 2026 TenderAI</div>
        </div>
      </div>

      {/* RIGHT PANEL — 60% Cream */}
      <div className="flex-1 bg-[#F5F3EE] flex items-center justify-center p-8">
        <div className="max-w-sm w-full">
          {/* Header */}
          <div className="mb-8">
            <h1 className="font-heading text-2xl font-bold text-[#0F1C35] mb-1">Bon retour</h1>
            <p className="text-sm text-[#6B6560]">Connectez-vous à votre espace</p>
          </div>

          {/* Success Banner — Account Created */}
          {showSuccess && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-green-900 mb-0.5">
                  Votre compte a été créé avec succès
                </p>
                <p className="text-xs text-green-700">
                  Connectez-vous pour accéder à votre espace.
                </p>
              </div>
            </div>
          )}

          {/* Form */}
          <form className="space-y-5" onSubmit={handleLoginSubmit}>
            {/* 429 Rate Limit Warning Banner */}
            {rateLimitReset && (
              <div className="w-full px-4 py-3 bg-[#C4962A]/10 border-l-4 border-[#C4962A] rounded text-sm text-[#C4962A] flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                <span>
                  Trop de tentatives. Réessayez dans <strong>{rateLimitCountdown}</strong> secondes.
                </span>
              </div>
            )}

            {/* Error Alert */}
            {error && (
              <div className="p-3 bg-[#B83232]/10 border border-[#B83232]/20 rounded-lg text-xs text-[#B83232] flex items-start gap-2">
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="mt-0.5 flex-shrink-0"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>{error}</span>
              </div>
            )}

            {/* Email Field */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#0F1C35]" htmlFor="email">
                Adresse email
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6B6560]">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                    <polyline points="22,6 12,13 2,6" />
                  </svg>
                </div>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="vous@entreprise.tn"
                  className="w-full pl-10 pr-4 py-3 bg-white border border-[#E5E0D8] rounded-xl text-sm text-[#0F1C35] placeholder:text-[#6B6560]/60
                    focus:outline-none focus:ring-2 focus:ring-[#C4962A]/40 focus:border-[#C4962A] transition-all"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-[#0F1C35]" htmlFor="password">
                  Mot de passe
                </label>
                <Link
                  href="/forgot-password"
                  className="text-xs text-[#C4962A] hover:text-[#d4a93c] font-medium transition-colors"
                >
                  Mot de passe oublié ?
                </Link>
              </div>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6B6560]">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </div>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-3 bg-white border border-[#E5E0D8] rounded-xl text-sm text-[#0F1C35] placeholder:text-[#6B6560]/60
                    focus:outline-none focus:ring-2 focus:ring-[#C4962A]/40 focus:border-[#C4962A] transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B6560] hover:text-[#0F1C35] transition-colors"
                  aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                >
                  {showPassword ? (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || loginDisabled}
              className="w-full py-3 bg-[#C4962A] text-white font-semibold rounded-xl
                hover:bg-[#d4a93c] active:scale-[0.98] transition-all
                focus:outline-none focus:ring-2 focus:ring-[#C4962A]/50 focus:ring-offset-2
                disabled:opacity-60 disabled:cursor-not-allowed
                flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <svg
                  className="animate-spin w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                >
                  <circle className="opacity-25" cx="12" cy="12" r="10" strokeWidth="4" />
                  <path className="opacity-75" d="M4 12a8 8 0 018-8v8z" />
                </svg>
              ) : null}
              <span>{isLoading ? 'Connexion...' : 'Se connecter'}</span>
              {!isLoading && <span aria-hidden="true">→</span>}
            </button>
          </form>

          {/* Signup Link */}
          <p className="text-center text-xs text-[#6B6560] mt-6">
            Pas encore de compte ?{' '}
            <Link
              href="/register"
              className="text-[#C4962A] font-semibold hover:text-[#d4a93c] transition-colors"
            >
              Créer un compte
            </Link>
          </p>

          {/* Security Badge */}
          <p className="text-center text-[10px] text-[#6B6560]/60 flex items-center justify-center gap-1.5 mt-6">
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
            Connexion chiffrée SSL · SOC 2 · ISO 27001
          </p>
        </div>
      </div>
    </div>
  )
}
