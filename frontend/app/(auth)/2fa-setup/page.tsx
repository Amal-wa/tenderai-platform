'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import AuthLeftPanel from '@/components/auth/AuthLeftPanel'
import StepIndicator from '@/components/ui/StepIndicator'
import OTPInput from '@/components/ui/OTPInput'
import TOTPTimer from '@/components/ui/TOTPTimer'

type SetupStep = 'scan' | 'verify' | 'backup'

const steps = [
  { id: 'scan', label: 'Scanner', number: 1 },
  { id: 'verify', label: 'Vérifier', number: 2 },
  { id: 'backup', label: 'Codes secours', number: 3 },
]

export default function TwoFASetupPage(): JSX.Element {
  const router = useRouter()

  // Wizard state
  const [currentStep, setCurrentStep] = useState<SetupStep>('scan')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Step 1 — Scan
  const [qrCodeUrl, setQrCodeUrl] = useState<string>('')
  const [secret, setSecret] = useState<string>('')

  // Step 2 — Verify
  const [code, setCode] = useState<string>('')
  const [codeError, setCodeError] = useState<string | null>(null)

  // Step 3 — Backup codes
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [backupConfirmed, setBackupConfirmed] = useState(false)

  // Load QR code on mount
  useEffect(() => {
    async function loadQRCode() {
      try {
        setIsLoading(true)
        setError(null)
        // TODO: Call API endpoint to get QR code + secret
        // For now, mock data
        setQrCodeUrl('https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=otpauth://totp/TenderAI:test@example.com?secret=JBSWY3DP5OBTQ43U&issuer=TenderAI')
        setSecret('JBSWY3DP5OBTQ43UJBSWY3DP')
      } catch (err) {
        setError('Impossible de charger le code QR. Veuillez réessayer.')
      } finally {
        setIsLoading(false)
      }
    }
    loadQRCode()
  }, [])

  const handleVerifyCode = async () => {
    if (code.length !== 6) {
      setCodeError('Le code doit contenir 6 chiffres')
      return
    }

    try {
      setCodeError(null)
      setIsLoading(true)
      // TODO: Call API to verify TOTP code and get backup codes
      // For now, mock backup codes
      await new Promise((r) => setTimeout(r, 500))
      setBackupCodes([
        'ABCD-1234',
        'EFGH-5678',
        'IJKL-9012',
        'MNOP-3456',
        'QRST-7890',
        'UVWX-1234',
        'YZAB-5678',
        'CDEF-9012',
        'GHIJ-3456',
        'KLMN-7890',
      ])
      setCurrentStep('backup')
      setCode('')
    } catch (err) {
      setCodeError('Code incorrect. Vérifiez l\'heure de votre téléphone.')
    } finally {
      setIsLoading(false)
    }
  }

  const downloadBackupCodes = () => {
    const content = `TenderAI — Codes de secours\nGénérés le: ${new Date().toLocaleDateString('fr-FR')}\n\n${backupCodes.join('\n')}\n\nChaque code ne peut être utilisé qu'une seule fois.`
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'tenderai-backup-codes.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  const copyBackupCodes = () => {
    navigator.clipboard.writeText(backupCodes.join('\n'))
  }

  // Get org name from AuthContext for dynamic messages
  const orgName = 'votre organisation' // TODO: Import from AuthContext like in other pages

  const handleFinish = async () => {
    try {
      setIsLoading(true)
      // TODO: Call API to finalize 2FA setup
      await new Promise((r) => setTimeout(r, 500))
      router.push('/dashboard')
    } catch (err) {
      setError('Erreur lors de la finalisation. Veuillez réessayer.')
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex">
      {/* LEFT PANEL */}
      <AuthLeftPanel
        headline="Sécurisez votre compte"
        subtext={(orgName) =>
          `L'authentification à deux facteurs protège l'espace ${orgName} contre les accès non autorisés.`
        }
        features={[
          'Compatible Google Authenticator, Authy, 1Password',
          'Code renouvelé toutes les 30 secondes (TOTP RFC 6238)',
          '10 codes de secours générés à l\'activation',
          'Révocation instantanée de session possible',
        ]}
        footerNote="🔒 Vos données ne quittent jamais vos serveurs"
      />

      {/* RIGHT PANEL — 60% Cream */}
      <div className="w-full lg:w-[60%] bg-cream flex flex-col justify-between p-8 lg:p-12 overflow-y-auto">
        <div className="max-w-md mx-auto w-full">
          {/* Step indicator */}
          <StepIndicator steps={steps} currentStep={currentStep} />

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

          {/* STEP 1 — SCAN */}
          {currentStep === 'scan' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-heading font-bold text-navy mb-2">Scannez le QR code</h1>
                <p className="text-sm text-muted">
                  Ouvrez Google Authenticator ou Authy, appuyez sur '+' et scannez ce code.
                </p>
              </div>

              {/* QR Code */}
              <div className="flex justify-center p-6 bg-white border-2 border-cream-border rounded-xl">
                {isLoading ? (
                  <div className="text-sm text-muted">Chargement...</div>
                ) : (
                  <img
                    src={qrCodeUrl}
                    alt="QR code TOTP"
                    className="w-48 h-48"
                  />
                )}
              </div>

              {/* Manual entry fallback */}
              <details className="group">
                <summary className="text-xs text-amber cursor-pointer font-medium hover:text-amber-light">
                  Entrer le code manuellement
                </summary>
                <div className="mt-3 space-y-2 p-3 bg-navy/5 rounded-lg">
                  <code className="font-mono text-xs bg-white px-3 py-2 rounded-lg block text-center tracking-widest text-navy border border-cream-border">
                    {secret}
                  </code>
                  <button
                    onClick={() => navigator.clipboard.writeText(secret)}
                    className="w-full text-xs text-amber font-medium hover:text-amber-light transition-colors"
                  >
                    Copier la clé
                  </button>
                </div>
              </details>

              {/* Next button */}
              <button
                onClick={() => setCurrentStep('verify')}
                disabled={isLoading || !qrCodeUrl}
                className="w-full py-3 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                J'ai scanné le code →
              </button>
            </div>
          )}

          {/* STEP 2 — VERIFY */}
          {currentStep === 'verify' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-heading font-bold text-navy mb-2">Entrez le code de vérification</h1>
                <p className="text-sm text-muted">
                  Saisissez le code à 6 chiffres affiché dans votre application.
                </p>
              </div>

              {/* Timer + OTP Input */}
              <div className="space-y-4">
                <div className="flex gap-6 items-center justify-center">
                  <TOTPTimer size={56} />
                  <div className="flex-1">
                    <OTPInput
                      value={code}
                      onChange={setCode}
                      onComplete={handleVerifyCode}
                      error={!!codeError}
                      disabled={isLoading}
                    />
                  </div>
                </div>
              </div>

              {/* Verify button */}
              <button
                onClick={handleVerifyCode}
                disabled={code.length !== 6 || isLoading}
                className="w-full py-3 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Vérification...
                  </>
                ) : (
                  'Vérifier'
                )}
              </button>

              {/* Back button */}
              <button
                onClick={() => {
                  setCurrentStep('scan')
                  setCode('')
                  setCodeError(null)
                }}
                className="w-full text-xs text-muted hover:text-navy transition-colors text-center"
              >
                ← Retour
              </button>
            </div>
          )}

          {/* STEP 3 — BACKUP CODES */}
          {currentStep === 'backup' && (
            <div className="space-y-6">
              <div>
                <h1 className="text-2xl font-heading font-bold text-navy mb-2">Vos codes de secours</h1>
                <p className="text-sm text-muted">
                  Conservez ces codes en lieu sûr. Chaque code ne peut être utilisé qu'une seule fois.
                </p>
              </div>

              {/* Backup codes grid */}
              <div className="grid grid-cols-2 gap-2 bg-navy/5 rounded-xl p-4">
                {backupCodes.map((code, idx) => (
                  <div
                    key={idx}
                    className="font-mono text-sm text-navy text-center py-2 px-3 bg-white rounded-lg border border-cream-border"
                  >
                    {code}
                  </div>
                ))}
              </div>

              {/* Warning box */}
              <div className="flex gap-3 p-3 bg-amber/10 border border-amber/20 rounded-lg">
                <svg
                  className="w-5 h-5 flex-shrink-0 text-amber mt-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                <p className="text-xs text-amber font-medium">
                  Si vous perdez accès à votre téléphone, ces codes sont votre seul moyen de récupérer votre
                  compte. {orgName} ne peut pas les récupérer pour vous.
                </p>
              </div>

              {/* Action buttons */}
              <div className="flex gap-2">
                <button
                  onClick={downloadBackupCodes}
                  className="flex-1 py-2.5 px-3 bg-white border border-navy text-navy font-medium rounded-lg hover:bg-navy/5 transition-colors text-sm"
                >
                  ⬇ Télécharger
                </button>
                <button
                  onClick={copyBackupCodes}
                  className="flex-1 py-2.5 px-3 bg-white border border-navy text-navy font-medium rounded-lg hover:bg-navy/5 transition-colors text-sm"
                >
                  📋 Copier
                </button>
              </div>

              {/* Confirmation checkbox */}
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={backupConfirmed}
                  onChange={(e) => setBackupConfirmed(e.target.checked)}
                  className="mt-1 accent-amber"
                />
                <span className="text-sm text-navy">
                  J'ai sauvegardé mes codes de secours en lieu sûr
                </span>
              </label>

              {/* Finish button */}
              <button
                onClick={handleFinish}
                disabled={!backupConfirmed || isLoading}
                className="w-full py-3 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Configuration en cours...
                  </>
                ) : (
                  'Terminer la configuration'
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
