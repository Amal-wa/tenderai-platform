'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Loader2, CheckCircle, AlertCircle, Mail, ArrowRight } from 'lucide-react'
import AuthLeftPanel from '@/components/auth/AuthLeftPanel'
import api, { extractErrorMessage } from '@/lib/api'

export default function VerifyEmailPage(): JSX.Element {
  const router = useRouter()
  const searchParams = useSearchParams()
  const email = searchParams.get('email') || ''
  const token = searchParams.get('token')

  const [status, setStatus] = useState<'verifying' | 'success' | 'error' | 'idle'>('idle')
  const [isResending, setIsResending] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string>('')
  const [successMessage, setSuccessMessage] = useState<string>('')
  const [nextStep, setNextStep] = useState<string>('/register/setup-2fa')

  // Auto-verify if token in URL
  useEffect(() => {
    if (token) {
      verifyEmailWithToken()
    }
  }, [token])

  const verifyEmailWithToken = async () => {
    setStatus('verifying')
    setErrorMessage('')

    try {
      const response = await api.get(`/api/v1/auth/verify-email?token=${token}`)

      setSuccessMessage(response.data.message || 'Votre email est maintenant vérifié!')
      
      const redirectPath = response.data.next_step || '/register/setup-2fa'
      setNextStep(redirectPath)
      setStatus('success')

      setTimeout(() => {
        router.push(redirectPath)
      }, 3000)
    } catch (error: unknown) {
      setErrorMessage(extractErrorMessage(error))
      setStatus('error')
    }
  }

  const handleResendEmail = async () => {
    setIsResending(true)
    setErrorMessage('')

    try {
      const response = await api.post('/api/v1/auth/resend-verification', { email })

      setSuccessMessage(response.data.message || 'Un nouveau lien a été envoyé à votre email.')
    } catch (error: unknown) {
      setErrorMessage(extractErrorMessage(error))
    } finally {
      setIsResending(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex flex-col">
      {/* Header avec logo */}
      <div className="h-1 bg-cream-border" />

      <div className="flex flex-1">
        {/* Left panel */}
        <AuthLeftPanel
          headline="Vérifiez votre email"
          subtext="Un lien de vérification a été envoyé. Cliquez le lien pour continuer."
          features={[
            'Email sécurisé avec lien valide 24 heures',
            'Aucune données personnelles stockées',
            'Configuration 2FA après vérification',
          ]}
        />

        {/* Right panel */}
        <div className="w-full lg:w-[60%] bg-cream flex items-center justify-center p-8 lg:p-12 overflow-y-auto">
          <div className="w-full max-w-md">
            {/* Status display */}
            {status === 'verifying' && (
              <div className="text-center space-y-4">
                <Loader2 className="w-12 h-12 animate-spin text-amber mx-auto" />
                <p className="text-muted">Vérification en cours...</p>
              </div>
            )}

            {status === 'success' && (
              <div className="space-y-6">
                <div className="text-center">
                  <CheckCircle className="w-16 h-16 text-success mx-auto mb-4" />
                  <h2 className="text-xl font-bold text-navy mb-2">Email vérifié!</h2>
                  <p className="text-muted text-sm">{successMessage}</p>
                </div>

                <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
                  <p className="text-xs text-success">
                    Redirection vers la configuration 2FA dans quelques secondes...
                  </p>
                </div>

                <button
                  onClick={() => router.push(nextStep)}
                  className="w-full py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all flex items-center justify-center gap-2"
                >
                  Continuer vers 2FA
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            )}

            {status === 'error' && (
              <div className="space-y-6">
                <div className="p-4 bg-danger/10 border border-danger/20 rounded-lg text-xs text-danger flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{errorMessage}</span>
                </div>

                <div className="space-y-3">
                  <p className="text-sm text-muted">
                    Vous n'avez pas reçu le lien? Nous pouvons le renvoyer.
                  </p>

                  <button
                    onClick={handleResendEmail}
                    disabled={isResending}
                    className="w-full py-3.5 bg-white text-navy font-semibold rounded-xl border border-cream-border hover:border-amber/50 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isResending ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Envoi en cours...
                      </>
                    ) : (
                      <>
                        <Mail className="w-4 h-4" />
                        Renvoyer le lien
                      </>
                    )}
                  </button>

                  <button
                    onClick={() => router.push('/login')}
                    className="w-full py-3.5 bg-amber/10 text-navy font-semibold rounded-xl border border-amber/20 hover:bg-amber/20 transition-all"
                  >
                    Retourner à la connexion
                  </button>
                </div>
              </div>
            )}

            {status === 'idle' && !token && (
              <div className="space-y-6">
                <div className="p-4 bg-warning/10 border border-warning/20 rounded-lg">
                  <p className="text-xs text-warning">
                    Un email avec un lien de vérification a été envoyé à <strong>{email}</strong>
                  </p>
                </div>

                <div className="space-y-3">
                  <p className="text-sm text-muted text-center">
                    Cliquez le lien dans l'email pour continuer ou demandez un nouveau lien.
                  </p>

                  <button
                    onClick={handleResendEmail}
                    disabled={isResending}
                    className="w-full py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isResending ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Envoi en cours...
                      </>
                    ) : (
                      <>
                        <Mail className="w-4 h-4" />
                        Renvoyer le lien
                      </>
                    )}
                  </button>
                </div>

                {successMessage && (
                  <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
                    <p className="text-xs text-success">{successMessage}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
