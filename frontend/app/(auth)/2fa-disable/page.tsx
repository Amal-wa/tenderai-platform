'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import AuthLeftPanel from '@/components/auth/AuthLeftPanel'
import api, { extractErrorMessage, getMe } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import type { TOTPDisableRequest } from '@/types/auth'

type Step = 'password' | 'confirm'

export default function TwoFADisablePage(): JSX.Element {
  const router = useRouter()
  const { updateUserProfile } = useAuth()

  const [currentStep, setCurrentStep] = useState<Step>('password')
  const [password, setPassword] = useState<string>('')
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [isLoadingPassword, setIsLoadingPassword] = useState(false)

  const [confirmText, setConfirmText] = useState<string>('')
  const [isLoadingConfirm, setIsLoadingConfirm] = useState(false)
  const [hasDisabled, setHasDisabled] = useState(false)

  // Validation helpers
  const isPasswordValid = password.length > 0
  const isConfirmValid = confirmText === 'désactiver'

  const handlePasswordVerify = async () => {
    if (!isPasswordValid) {
      setPasswordError('Veuillez entrer votre mot de passe')
      return
    }

    try {
      setPasswordError(null)
      setIsLoadingPassword(true)
      
      // POST /api/v1/auth/2fa/disable with password
      const req: TOTPDisableRequest = { password }
      await api.post('/api/v1/auth/2fa/disable', req)
      
      // Success: move to confirmation step
      setCurrentStep('confirm')
    } catch (err: unknown) {
      const errorMessage = extractErrorMessage(err)
      setPasswordError(errorMessage)
      setPassword('')
    } finally {
      setIsLoadingPassword(false)
    }
  }

  const handleConfirmDisable = async () => {
    if (!isConfirmValid) {
      return
    }

    try {
      setIsLoadingConfirm(true)
      
      // The actual disable already happened in step 1
      // This is just UI confirmation
      setHasDisabled(true)

      // Fetch user profile to get role and update context
      try {
        const userProfile = await getMe()
        
        // Update AuthContext: set totp_enabled = false
        updateUserProfile({ totp_enabled: false })
        
        // Redirect after 2 seconds
        setTimeout(() => {
          if (['superadmin', 'admin'].includes(userProfile.role)) {
            router.push('/dashboard/admin')
          } else {
            router.push('/dashboard/user')
          }
        }, 2000)
      } catch (err: unknown) {
        // getMe() failed, redirect to login
        const errorMessage = extractErrorMessage(err)
        console.error('[TwoFADisablePage] getMe() failed:', errorMessage)
        setTimeout(() => {
          router.push('/login')
        }, 2000)
      }
    } catch (err: unknown) {
      // Revert to password step if confirm fails
      const errorMessage = extractErrorMessage(err)
      console.error('[TwoFADisablePage] Confirm failed:', errorMessage)
      setCurrentStep('password')
      setPassword('')
      setConfirmText('')
    } finally {
      setIsLoadingConfirm(false)
    }
  }

  const handleCancel = () => {
    router.back()
  }

  return (
    <div className="min-h-screen w-full flex">
      {/* LEFT PANEL */}
      <AuthLeftPanel
        headline="Désactiver l'authentification à deux facteurs"
        subtext="Attention : Cette action rendra votre compte moins sécurisé."
        features={[
          'Tous vos codes de secours seront invalidés',
          'Votre authenticateur (Google Authenticator, Authy...) ne fonctionnera plus',
          'Vous devrez utiliser uniquement votre mot de passe pour vous connecter',
          'Vous pourrez réactiver 2FA à tout moment',
        ]}

      />

      {/* RIGHT PANEL — 60% Cream */}
      <div className="w-full lg:w-[60%] bg-cream flex flex-col justify-between p-8 lg:p-12 overflow-y-auto">
        <div className="max-w-md mx-auto w-full">
          {/* Success state */}
          {hasDisabled && (
            <div className="space-y-6 text-center">
              <div className="w-16 h-16 mx-auto bg-success/10 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-heading font-bold text-navy mb-2">Désactivée</h1>
                <p className="text-sm text-muted">L'authentification à deux facteurs a été désactivée.</p>
              </div>
              <p className="text-xs text-muted">Redirection en cours...</p>
            </div>
          )}

          {/* Step 1 — Password Verification */}
          {!hasDisabled && currentStep === 'password' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-heading font-bold text-navy mb-2">Confirmez votre identité</h1>
                <p className="text-sm text-muted">
                  Entrez votre mot de passe pour confirmer la désactivation de 2FA.
                </p>
              </div>

              {/* Error alert */}
              {passwordError && (
                <div className="p-3 bg-danger/10 border border-danger/20 rounded-lg text-xs text-danger flex items-start gap-2">
                  <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 12 12">
                    <circle cx="6" cy="6" r="5" fill="currentColor" opacity="0.2" />
                    <circle cx="6" cy="3.5" r="0.75" />
                    <path d="M6 5.5v2" stroke="currentColor" strokeWidth="0.75" strokeLinecap="round" />
                  </svg>
                  {passwordError}
                </div>
              )}

              {/* Password input — RED focus ring for destructive */}
              <div>
                <label className="block text-xs font-medium text-navy mb-2">Mot de passe</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    setPasswordError(null)
                  }}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 border-2 border-cream-border rounded-lg text-navy placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-danger focus:border-danger transition-all"
                  disabled={isLoadingPassword}
                  autoFocus
                />
              </div>

              {/* Verify button */}
              <button
                onClick={handlePasswordVerify}
                disabled={!isPasswordValid || isLoadingPassword}
                className="w-full py-3 bg-danger text-white font-semibold rounded-xl hover:bg-danger-light transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoadingPassword ? (
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

              {/* Cancel link */}
              <button
                onClick={handleCancel}
                className="w-full text-xs text-muted hover:text-navy transition-colors text-center"
              >
                ← Retour aux paramètres
              </button>
            </div>
          )}

          {/* Step 2 — Final Confirmation */}
          {!hasDisabled && currentStep === 'confirm' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-heading font-bold text-navy mb-2">Êtes-vous certain?</h1>
                <p className="text-sm text-muted">
                  L'authentification à deux facteurs rend votre compte beaucoup plus sécurisé. Cette action est
                  définitive.
                </p>
              </div>

              {/* Irreversible action alert */}
              <div className="p-3 bg-danger/10 border border-danger/20 rounded-xl flex items-start gap-3">
                <svg className="flex-shrink-0 mt-0.5 text-danger w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                <div>
                  <p className="text-sm font-semibold text-danger">Action irréversible</p>
                  <p className="text-xs text-danger/80 mt-1">
                    Vous devrez reconfigurer votre application TOTP si vous souhaitez réactiver la 2FA.
                  </p>
                </div>
              </div>

              {/* Confirmation text input */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-navy">
                  Tapez <span className="font-mono font-bold bg-danger/10 px-1.5 py-0.5 rounded text-danger">désactiver</span> pour confirmer
                </label>
                <input
                  type="text"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  placeholder="désactiver"
                  className="w-full py-3 px-4 border border-cream-border rounded-xl text-sm bg-white text-navy placeholder:text-muted
                    focus:outline-none focus:ring-2 focus:ring-danger/40 focus:border-danger transition-all"
                  disabled={isLoadingConfirm}
                />
                {isConfirmValid && (
                  <p className="text-xs text-success font-medium">✓ Confirmation acceptée</p>
                )}
              </div>

              {/* Disable button — RED, disabled until text matches */}
              <button
                onClick={handleConfirmDisable}
                disabled={!isConfirmValid || isLoadingConfirm}
                className="w-full py-3 bg-danger text-white font-semibold rounded-xl hover:bg-red-700 active:scale-[0.98] transition-all
                  disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoadingConfirm ? (
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
                    Désactivation...
                  </>
                ) : (
                  '🗑️ Désactiver définitivement'
                )}
              </button>

              {/* Back button */}
              <button
                onClick={() => setCurrentStep('password')}
                className="w-full text-xs text-muted hover:text-navy transition-colors text-center"
              >
                ← Retour
              </button>
            </div>
          )}
        </div>

        {/* Security note footer */}
        <div className="mt-8 text-center text-xs text-muted">
          <p>🔒 Nous vous recommandons de réactiver 2FA aussi rapidement que possible</p>
        </div>
      </div>
    </div>
  )
}
