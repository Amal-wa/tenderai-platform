'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2, AlertCircle, Copy, Download, CheckCircle } from 'lucide-react'
import AuthLeftPanel from '@/components/auth/AuthLeftPanel'
import api, { extractErrorMessage } from '@/lib/api'
import type { TOTPSetupResponse, TOTPVerifyResponse } from '@/types/auth'

type Step = 'verify' | 'backup'

export default function Setup2FAPage(): JSX.Element {
  const router = useRouter()

  // Step management
  const [currentStep, setCurrentStep] = useState<Step>('verify')

  // Step 1: Load QR code on mount
  const [qrCode, setQrCode] = useState<string>('')
  const [secret, setSecret] = useState<string>('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string>('')

  // Step 2: Verify TOTP code
  const [code, setCode] = useState<string>('')
  const [isVerifying, setIsVerifying] = useState(false)
  const [codeError, setCodeError] = useState<string>('')

  // Step 3: Backup codes
  const [backupConfirmed, setBackupConfirmed] = useState(false)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  // Initialize: fetch 2FA setup on mount
  useEffect(() => {
    loadQRCode()
  }, [])

  const loadQRCode = async () => {
    setIsLoading(true)
    setLoadError('')

    try {
      const response = await api.post<TOTPSetupResponse>('/api/v1/auth/2fa/setup')
      setQrCode(response.data.qr_code)
      setSecret(response.data.secret)
      setBackupCodes(response.data.backup_codes || [])
    } catch (err: unknown) {
      const message = extractErrorMessage(err)
      setLoadError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerifyCode = async () => {
    if (!code || code.length !== 6) {
      setCodeError('Le code doit contenir 6 chiffres')
      return
    }

    setIsVerifying(true)
    setCodeError('')

    try {
      const response = await api.post<TOTPVerifyResponse>('/api/v1/auth/2fa/verify', {
        code,
      })
      if (response.data.is_enabled) {
        setCurrentStep('backup')
      }
    } catch (err: unknown) {
      setCodeError(extractErrorMessage(err))
    } finally {
      setIsVerifying(false)
    }
  }

  const handleCopyBackupCodes = () => {
    navigator.clipboard.writeText(backupCodes.join('\n'))
    setCopiedCode('all')
    setTimeout(() => setCopiedCode(null), 2000)
  }

  const handleDownloadBackupCodes = () => {
    const content = `TenderAI — Codes de secours\nGénérés le: ${new Date().toLocaleDateString('fr-FR')}\n\n${backupCodes.join('\n')}\n\nChaque code ne peut être utilisé qu'une seule fois. Conservez ce fichier en lieu sûr.`
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'tenderai-backup-codes.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleFinish = async () => {
    try {
      const me = await api.get('/api/v1/auth/me')
      const role = !me.data.role ? 'viewer'
        : typeof me.data.role === 'string' ? me.data.role
        : me.data.role.name ?? 'viewer'
      if (['superadmin', 'admin'].includes(role)) {
        router.push('/dashboard/admin')
      } else {
        router.push('/dashboard/user')
      }
    } catch {
      router.push('/login')
    }
  }

  return (
    <div className="min-h-screen w-full flex flex-col">
      {/* Header */}
      <div className="h-1 bg-cream-border" />

      <div className="flex flex-1">
        {/* Left panel */}
        <AuthLeftPanel
          headline="Configurez votre authentification 2FA"
          subtext={
            currentStep === 'verify'
              ? 'Scannez le code QR avec Google Authenticator, Authy ou une autre appli compatible.'
              : 'Sauvegardez vos codes de secours dans un endroit sûr.'
          }
          features={
            currentStep === 'verify'
              ? [
                  'Codes de secours pour l\'accès d\'urgence',
                  'Protection maximale de votre compte',
                  'Compatible avec tous les authentificateurs standards',
                ]
              : [
                  'Codes uniques pour accéder en cas d\'urgence',
                  'À conserver précieusement et en sécurité',
                  'Chaque code ne peut être utilisé qu\'une seule fois',
                ]
          }
        />

        {/* Right panel */}
        <div className="w-full lg:w-[60%] bg-cream flex items-center justify-center p-8 lg:p-12 overflow-y-auto">
          <div className="w-full max-w-md space-y-6">
            {/* Loading state */}
            {isLoading && (
              <div className="text-center space-y-4">
                <Loader2 className="w-12 h-12 animate-spin text-amber mx-auto" />
                <p className="text-muted">Génération du code QR...</p>
              </div>
            )}

            {/* Error state */}
            {loadError && (
              <div className="space-y-4">
                <div className="p-4 bg-danger/10 border border-danger/20 rounded-lg text-xs text-danger flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{loadError}</span>
                </div>
                <button
                  onClick={loadQRCode}
                  className="w-full py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all"
                >
                  Réessayer
                </button>
              </div>
            )}

            {/* Step 1: Verify TOTP */}
            {!isLoading && !loadError && currentStep === 'verify' && (
              <div className="space-y-6">
                {/* Step indicator */}
                <div className="flex items-center gap-2 text-xs text-muted">
                  <div className="w-6 h-6 rounded-full bg-amber text-white flex items-center justify-center text-xs font-semibold">
                    1
                  </div>
                  <span>Étape 1/2 • Vérification</span>
                </div>

                {/* QR Code section */}
                <div className="space-y-3">
                  <h3 className="text-sm font-semibold text-navy">Scannez ce code QR</h3>
                  {qrCode && (
                    <div className="flex justify-center p-4 bg-white border border-cream-border rounded-lg">
                      <img src={qrCode} alt="QR Code" className="w-48 h-48" />
                    </div>
                  )}
                  <p className="text-xs text-muted">
                    Utilisez Google Authenticator, Authy, Microsoft Authenticator ou toute autre appli compatOTP.
                  </p>
                </div>

                {/* Manual key entry */}
                <div className="space-y-2 pt-4 border-t border-cream-border">
                  <label className="block text-xs font-semibold text-navy">
                    Ou entrez cette clé manuellement
                  </label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 px-3 py-2 bg-white border border-cream-border rounded-lg text-sm text-navy font-mono overflow-x-auto">
                      {secret}
                    </code>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(secret)
                        setCopiedCode('secret')
                        setTimeout(() => setCopiedCode(null), 2000)
                      }}
                      className="px-3 py-2 bg-white border border-cream-border hover:border-amber/50 rounded-lg transition-all flex-shrink-0"
                      title="Copier"
                    >
                      {copiedCode === 'secret' ? (
                        <CheckCircle className="w-4 h-4 text-success" />
                      ) : (
                        <Copy className="w-4 h-4 text-muted" />
                      )}
                    </button>
                  </div>
                </div>

                {/* TOTP code input */}
                <div className="space-y-2 pt-4 border-t border-cream-border">
                  <label htmlFor="totp-code" className="block text-xs font-semibold text-navy">
                    Entrez le code 6 chiffres
                  </label>
                  <input
                    id="totp-code"
                    type="text"
                    inputMode="numeric"
                    placeholder="000000"
                    maxLength={6}
                    value={code}
                    onChange={(e) => {
                      setCode(e.target.value.replace(/\D/g, ''))
                      setCodeError('')
                    }}
                    className="w-full px-4 py-3 border border-cream-border rounded-xl text-center text-2xl font-mono focus:outline-none focus:ring-3 focus:ring-amber/20 focus:border-amber transition-all"
                  />
                  {codeError && <p className="text-xs text-danger">{codeError}</p>}
                </div>

                {/* Verify button */}
                <button
                  onClick={handleVerifyCode}
                  disabled={isVerifying || code.length !== 6}
                  className="w-full py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isVerifying ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Vérification...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      Vérifier et continuer
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Step 2: Backup codes */}
            {!isLoading && !loadError && currentStep === 'backup' && (
              <div className="space-y-6">
                {/* Step indicator */}
                <div className="flex items-center gap-2 text-xs text-muted">
                  <div className="w-6 h-6 rounded-full bg-success text-white flex items-center justify-center text-xs font-semibold">
                    ✓
                  </div>
                  <span>Étape 2/2 • Codes de secours</span>
                </div>

                {/* Success message */}
                <div className="p-4 bg-success/10 border border-success/20 rounded-lg flex items-start gap-2">
                  <CheckCircle className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-navy">
                    <p className="font-semibold">Code vérifié avec succès!</p>
                    <p className="text-xs text-muted mt-1">Maintenant, sauvegardez vos codes de secours.</p>
                  </div>
                </div>

                {/* Backup codes list */}
                <div className="space-y-3 pt-4 border-t border-cream-border">
                  <div className="flex items-start gap-2 p-3 bg-warning/10 border border-warning/20 rounded-lg">
                    <AlertCircle className="w-4 h-4 text-warning flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-warning">
                      <strong>Important:</strong> Sauvegardez ces 10 codes dans un endroit sûr. Vous en aurez besoin si vous perdez accès à votre authentificateur.
                    </p>
                  </div>

                  {/* Backup codes grid */}
                  <div className="grid grid-cols-2 gap-2 bg-white border border-cream-border rounded-lg p-4">
                    {backupCodes.map((backupCode, idx) => (
                      <div
                        key={idx}
                        className="px-3 py-2 bg-cream border border-cream-border rounded text-sm font-mono text-navy"
                      >
                        {backupCode}
                      </div>
                    ))}
                  </div>

                  {/* Copy/Download buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={handleCopyBackupCodes}
                      className="flex-1 py-2.5 px-3 bg-white border border-cream-border hover:border-amber/50 rounded-lg transition-all flex items-center justify-center gap-2 text-sm font-medium text-navy"
                    >
                      {copiedCode === 'all' ? <CheckCircle className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
                      {copiedCode === 'all' ? 'Copié!' : 'Copier tous'}
                    </button>
                    <button
                      onClick={handleDownloadBackupCodes}
                      className="flex-1 py-2.5 px-3 bg-white border border-cream-border hover:border-amber/50 rounded-lg transition-all flex items-center justify-center gap-2 text-sm font-medium text-navy"
                    >
                      <Download className="w-4 h-4" />
                      Télécharger
                    </button>
                  </div>
                </div>

                {/* Confirmation checkbox */}
                <div className="flex items-center gap-3 p-3 bg-cream border border-cream-border rounded-lg">
                  <input
                    type="checkbox"
                    id="backup-confirmed"
                    checked={backupConfirmed}
                    onChange={(e) => setBackupConfirmed(e.target.checked)}
                    className="w-4 h-4 rounded border-cream-border text-amber focus:ring-amber cursor-pointer"
                  />
                  <label htmlFor="backup-confirmed" className="text-xs text-navy cursor-pointer flex-1">
                    J'ai sauvegardé mes codes de secours en lieu sûr
                  </label>
                </div>

                {/* Finish button */}
                <button
                  onClick={handleFinish}
                  disabled={!backupConfirmed}
                  className="w-full py-3.5 bg-amber text-white font-semibold rounded-xl hover:bg-amber-light transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  Terminer la configuration
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
