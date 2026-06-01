'use client'

export const dynamic = 'force-dynamic'

import { Suspense, useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { totpSetup, totpVerify, extractErrorMessage } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'
import AuthLeftPanel from '@/components/auth/AuthLeftPanel'
import StepIndicator from '@/components/ui/StepIndicator'
import OTPInput from '@/components/ui/OTPInput'
import TOTPTimer from '@/components/ui/TOTPTimer'
import { Download, Copy, AlertCircle } from 'lucide-react'

type SetupStep = 'scan' | 'verify' | 'backup'

const steps = [
  { id: 'scan', label: 'Scanner', number: 1 },
  { id: 'verify', label: 'Vérifier', number: 2 },
  { id: 'backup', label: 'Codes secours', number: 3 },
]

export default function TwoFASetupPage(): JSX.Element {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0F1C35]" />}>
      <TwoFASetupInner />
    </Suspense>
  )
}

function TwoFASetupInner(): JSX.Element {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user } = useAuth()

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
        const response = await totpSetup()
        setQrCodeUrl(response.qr_code)
        setSecret(response.secret)
        setBackupCodes(response.backup_codes)
      } catch (err) {
        const msg = extractErrorMessage(err)
        setError(msg || 'Impossible de charger le code QR. Veuillez réessayer.')
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
      await totpVerify(code)
      setCurrentStep('backup')
      setCode('')
    } catch (err) {
      const msg = extractErrorMessage(err)
      setCodeError(msg || 'Code incorrect. Vérifiez l\'heure de votre téléphone.')
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
  const orgName = user?.tenant_name || 'votre organisation'

  const handleFinish = () => {
    const nextParam = searchParams.get('next')
    let redirectPath = '/dashboard'
    
    if (nextParam && (nextParam.startsWith('/dashboard') || nextParam.startsWith('/login'))) {
      redirectPath = nextParam
    }
    
    router.push(redirectPath)
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
        footerNote="Vos données ne quittent jamais vos serveurs"
      />

      {/* RIGHT PANEL — 60% Cream */}
      <div className="w-full lg:w-[60%] bg-cream flex flex-col justify-between p-8 lg:p-12 overflow-y-auto">
        <div className="max-w-md mx-auto w-full">
          {/* Step indicator */}
          <StepIndicator steps={steps} currentStep={currentStep} />

          {/* Error alert */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2 mb-6">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
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
              <div className="flex gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <AlertCircle className="w-5 h-5 flex-shrink-0 text-amber-600 mt-0.5" />
                <p className="text-xs text-amber-800 font-medium">
                  Si vous perdez accès à votre téléphone, ces codes sont votre seul moyen de récupérer votre
                  compte. {orgName} ne peut pas les récupérer pour vous.
                </p>
              </div>

              {/* Action buttons */}
              <div className="flex gap-2">
                <button
                  onClick={downloadBackupCodes}
                  className="flex-1 py-2.5 px-3 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors text-sm flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Télécharger
                </button>
                <button
                  onClick={copyBackupCodes}
                  className="flex-1 py-2.5 px-3 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors text-sm flex items-center justify-center gap-2"
                >
                  <Copy className="w-4 h-4" />
                  Copier
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
