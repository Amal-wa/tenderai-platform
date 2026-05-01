'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import AuthLeftPanel from '@/components/auth/AuthLeftPanel'
import OTPInput from '@/components/ui/OTPInput'
import TOTPTimer from '@/components/ui/TOTPTimer'
import { extractErrorMessage } from '@/lib/api'
import { verify2FA } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import type { Verify2FARequest } from '@/types/auth'

type Method = 'totp' | 'backup'

export default function TwoFALoginPage(): JSX.Element {
  const router = useRouter()
  const { finalizeLogin } = useAuth()

  // Get partial_token from sessionStorage (passed from login page)
  const [partialToken, setPartialToken] = useState<string | null>(null)
  
  // Session state
  const [remainingSeconds, setRemainingSeconds] = useState<number>(300) // 5 minutes
  const [sessionExpired, setSessionExpired] = useState(false)

  // Input state
  const [method, setMethod] = useState<Method>('totp')
  const [code, setCode] = useState<string>('')
  const [backupCode, setBackupCode] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Attempts
  const [attemptCount, setAttemptCount] = useState<number>(0)
  const maxAttempts = 5

  // Load partialToken from sessionStorage on mount & validate
  useEffect(() => {
    const tokenFromStorage = typeof window !== 'undefined' 
      ? sessionStorage.getItem('partial_token')
      : null
    
    if (!tokenFromStorage) {
      // No partialToken — redirect immediately to /login
      router.push('/login')
    } else {
      setPartialToken(tokenFromStorage)
    }
  }, [router])

  // Session countdown
  useEffect(() => {
    const interval = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          setSessionExpired(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // Redirect on session expiration (clear sessionStorage)
  useEffect(() => {
    if (sessionExpired) {
      setTimeout(() => {
        sessionStorage.removeItem('partial_token')
        router.push('/login?error=session_expired')
      }, 2000)
    }
  }, [sessionExpired, router])

  // Format remaining time
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs.toString().padStart(2, '0')}s`
  }

  const handleVerifyTOTP = async () => {
    if (code.length !== 6) {
      setError('Le code doit contenir 6 chiffres')
      return
    }

    if (attemptCount >= maxAttempts) {
      setError(`Trop de tentatives. Veuillez réessayer dans 5 minutes.`)
      return
    }

    if (!partialToken) {
      setError('Session 2FA invalide. Veuillez réessayer.')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      // Call verify2FA with TOTP code
      const req: Verify2FARequest = { totp_code: code }
      await verify2FA(req, partialToken)

      // Success: tokens are now in httpOnly cookies
      // Clear sessionStorage and fetch user profile to get role
      sessionStorage.removeItem('partial_token')
      await finalizeLogin()
    } catch (err: unknown) {
      const newAttemptCount = attemptCount + 1
      setAttemptCount(newAttemptCount)

      if (newAttemptCount >= maxAttempts) {
        setError(`Trop de tentatives. Redirection vers la connexion...`)
        sessionStorage.removeItem('partial_token')
        setTimeout(() => {
          router.push('/login')
        }, 3000)
      } else {
        const errorMessage = extractErrorMessage(err)
        setError(`${errorMessage} (tentative ${newAttemptCount}/${maxAttempts})`)
      }
      setCode('')
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerifyBackupCode = async () => {
    if (!backupCode.match(/^[A-Z0-9]{4}-[A-Z0-9]{4}$/)) {
      setError('Format: XXXX-XXXX')
      return
    }

    if (attemptCount >= maxAttempts) {
      setError(`Trop de tentatives. Veuillez réessayer dans 5 minutes.`)
      return
    }

    if (!partialToken) {
      setError('Session 2FA invalide. Veuillez réessayer.')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      // Call verify2FA with backup code
      const req: Verify2FARequest = { backup_code: backupCode }
      await verify2FA(req, partialToken)

      // Success: tokens are now in httpOnly cookies
      // Clear sessionStorage and fetch user profile to get role
      sessionStorage.removeItem('partial_token')
      await finalizeLogin()
    } catch (err: unknown) {
      const newAttemptCount = attemptCount + 1
      setAttemptCount(newAttemptCount)

      if (newAttemptCount >= maxAttempts) {
        setError(`Trop de tentatives. Redirection vers la connexion...`)
        sessionStorage.removeItem('partial_token')
        setTimeout(() => {
          router.push('/login')
        }, 3000)
      } else {
        const errorMessage = extractErrorMessage(err)
        setError(`${errorMessage} (tentative ${newAttemptCount}/${maxAttempts})`)
      }
      setBackupCode('')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex">
      {/* LEFT PANEL */}
      <AuthLeftPanel
        headline="Vérification en deux étapes"
        subtext="Entrez le code temporaire de votre authentificateur ou un code de secours."
        features={[
          'Code valide pendant 30 secondes',
          'Session sécurisée de 5 minutes',
          'Chaque code de secours ne peut être utilisé qu\'une fois',
          'Les données ne quittent jamais vos serveurs',
        ]}
        warning={{
          type: 'warning',
          title: 'Session temporaire',
          items: [`Votre session expire dans ${formatTime(remainingSeconds)}`],
        }}
      />

      {/* RIGHT PANEL — 60% Cream */}
      <div className="w-full lg:w-[60%] bg-cream flex flex-col justify-between p-8 lg:p-12 overflow-y-auto">
        <div className="max-w-md mx-auto w-full">
          {/* Session expired notice */}
          {sessionExpired && (
            <div className="mb-6 p-4 bg-danger/10 border border-danger/20 rounded-lg">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-danger flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <div>
                  <p className="font-semibold text-sm text-danger">Session expirée</p>
                  <p className="text-xs text-danger/80 mt-1">Veuillez vous reconnecter.</p>
                </div>
              </div>
            </div>
          )}

          {/* Request timeout alert */}
          {remainingSeconds < 60 && remainingSeconds > 0 && (
            <div className="mb-6 p-3 bg-amber/10 border border-amber/20 rounded-lg flex items-start gap-2">
              <svg className="w-4 h-4 text-amber flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-xs text-amber font-medium">Votre session expire bientôt</span>
            </div>
          )}

          <div>
            <h1 className="text-2xl font-heading font-bold text-navy mb-2">Code de vérification</h1>
            <p className="text-sm text-muted mb-6">Session: {formatTime(remainingSeconds)}</p>
          </div>

          {/* Error alert */}
          {error && (
            <div className="p-3 bg-danger/10 border border-danger/20 rounded-lg text-xs text-danger flex items-start gap-2 mb-6">
              <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 12 12">
                <circle cx="6" cy="6" r="5" fill="currentColor" opacity="0.2" />
                <circle cx="6" cy="3.5" r="0.75" />
                <path d="M6 5.5v2" stroke="currentColor" strokeWidth="0.75" strokeLinecap="round" />
              </svg>
              {error}
            </div>
          )}

          {/* Method toggle */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => {
                setMethod('totp')
                setError(null)
              }}
              className={`flex-1 py-2 px-3 text-xs font-medium rounded-lg transition-all ${
                method === 'totp'
                  ? 'bg-amber text-white'
                  : 'bg-white border border-cream-border text-navy hover:bg-cream'
              }`}
            >
              Code temporaire
            </button>
            <button
              onClick={() => {
                setMethod('backup')
                setError(null)
              }}
              className={`flex-1 py-2 px-3 text-xs font-medium rounded-lg transition-all ${
                method === 'backup'
                  ? 'bg-amber text-white'
                  : 'bg-white border border-cream-border text-navy hover:bg-cream'
              }`}
            >
              Code de secours
            </button>
          </div>

          {/* TOTP input */}
          {method === 'totp' && (
            <div className="space-y-4">
              <div className="flex gap-6 items-center justify-center">
                <TOTPTimer size={56} onExpire={() => setSessionExpired(true)} />
                <div className="flex-1">
                  <OTPInput
                    value={code}
                    onChange={setCode}
                    error={!!error}
                    disabled={isLoading || sessionExpired}
                  />
                </div>
              </div>

              <button
                onClick={handleVerifyTOTP}
                disabled={code.length !== 6 || isLoading || sessionExpired}
                className="w-full py-3 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Vérification...
                  </>
                ) : (
                  'Continuer'
                )}
              </button>
            </div>
          )}

          {/* Backup code input */}
          {method === 'backup' && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-navy mb-2">Code de secours (Format: XXXX-XXXX)</label>
                <input
                  type="text"
                  value={backupCode}
                  onChange={(e) => setBackupCode(e.target.value.toUpperCase())}
                  placeholder="ABCD-1234"
                  className="w-full px-4 py-3 border border-cream-border rounded-lg font-mono text-sm uppercase text-navy placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-amber transition-all"
                  disabled={isLoading || sessionExpired}
                />
              </div>

              <button
                onClick={handleVerifyBackupCode}
                disabled={!backupCode.match(/^[A-Z0-9]{4}-[A-Z0-9]{4}$/) || isLoading || sessionExpired}
                className="w-full py-3 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Vérification...
                  </>
                ) : (
                  'Continuer'
                )}
              </button>
            </div>
          )}

          {/* Need help */}
          <div className="mt-8 text-center">
            <p className="text-xs text-muted">
              Impossible de recevoir le code?{' '}
              <a href="#" className="text-amber hover:text-amber-light font-medium">
                Contacter le support
              </a>
            </p>
          </div>
        </div>

        {/* Session status footer */}
        <div className="mt-8 text-center text-xs text-muted">
          <p>Session sécurisée • Données chiffrées en transit</p>
        </div>
      </div>
    </div>
  )
}
