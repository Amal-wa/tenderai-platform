'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useSettings } from '@/hooks/useSettings'
import api, { extractErrorMessage } from '@/lib/api'
import type { TOTPSetupResponse } from '@/types/settings'
import type { UserProfile } from '@/types/auth'

export default function AuthSection({ onDirtyChange: _onDirtyChange }: { isDirty: boolean; onDirtyChange: (dirty: boolean) => void }) {
  const { user, updateUserProfile } = useAuth()
  const { disableTotp, setupTotp, verifyTotp } = useSettings()

  const [isDisabling, setIsDisabling] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [isRegenerating, setIsRegenerating] = useState(false)
  const [isSettingUp, setIsSettingUp] = useState(false)
  const [showDisableModal, setShowDisableModal] = useState(false)
  const [disablePassword, setDisablePassword] = useState('')
  const [newBackupCodes, setNewBackupCodes] = useState<string[]>([])
  const [showNewCodes, setShowNewCodes] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const [showSetup2FAModal, setShowSetup2FAModal] = useState(false)
  const [setupQRCode, setSetupQRCode] = useState<string | null>(null)
  const [setupSecret, setSetupSecret] = useState<string | null>(null)
  const [verificationCode, setVerificationCode] = useState('')
  const [setupError, setSetupError] = useState<string | null>(null)

  useEffect(() => {
    if (showSetup2FAModal) {
      setIsSettingUp(true)
      setSetupError(null)
      setSetupQRCode(null)
      setSetupSecret(null)
      setVerificationCode('')

      const initialize2FASetup = async () => {
        try {
          const response = await setupTotp()
          const setupData = response.data as TOTPSetupResponse
          setSetupQRCode(setupData.qr_code)
          setSetupSecret(setupData.secret)
        } catch (err) {
          setSetupError(extractErrorMessage(err))
        } finally {
          setIsSettingUp(false)
        }
      }

      initialize2FASetup()
    }
  }, [showSetup2FAModal])

  const handleDisable2FA = async () => {
    if (!disablePassword.trim()) {
      setError('Veuillez entrer votre mot de passe')
      return
    }

    setIsDisabling(true)
    setError(null)

    try {
      await disableTotp({ password: disablePassword })
      setShowDisableModal(false)
      setDisablePassword('')
      const response = await api.get('/api/v1/auth/me')
      const profile = response.data as UserProfile
      updateUserProfile({ totp_enabled: profile.totp_enabled })
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setIsDisabling(false)
    }
  }

  const handleRegenerateBackupCodes = async () => {
    setIsRegenerating(true)
    setError(null)

    try {
      const response = await api.post<{ backup_codes: string[]; message: string }>(
        '/api/v1/auth/2fa/regenerate-backup-codes'
      )
      setNewBackupCodes(response.data.backup_codes)
      setShowNewCodes(true)
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleSetup2FAClick = () => {
    setError(null)
    setShowSetup2FAModal(true)
    setSetupError(null)
    setVerificationCode('')
  }

  const handleVerify2FA = async () => {
    if (!verificationCode.trim()) {
      setSetupError('Veuillez entrer le code TOTP')
      return
    }

    setIsVerifying(true)
    setSetupError(null)

    try {
      await verifyTotp({ code: verificationCode })
      setShowSetup2FAModal(false)
      setVerificationCode('')
      setSetupQRCode(null)
      setSetupSecret(null)
      const response = await api.get('/api/v1/auth/me')
      const profile = response.data as UserProfile
      updateUserProfile({ totp_enabled: profile.totp_enabled })
    } catch (err) {
      setSetupError(extractErrorMessage(err))
    } finally {
      setIsVerifying(false)
    }
  }

  const closeSetup2FAModal = () => {
    setShowSetup2FAModal(false)
    setVerificationCode('')
    setSetupQRCode(null)
    setSetupSecret(null)
    setSetupError(null)
  }

  return (
    <div className="space-y-6">
      {/* Card 1 — 2FA TOTP */}
      <div className="border rounded-lg overflow-hidden" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
        <div className="p-3.5 border-b flex items-center justify-between" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
          <div>
            <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
              Authentification à deux facteurs (2FA)
            </div>
            <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
              TOTP RFC 6238 — Google Authenticator / Authy
            </div>
          </div>
          <span
            className="text-[11px] font-semibold px-2 py-1 rounded-full flex items-center gap-1"
            style={{
              backgroundColor: user?.totp_enabled ? 'rgba(31,122,77,0.1)' : 'rgba(107,101,96,0.08)',
              color: user?.totp_enabled ? '#1F7A4D' : 'var(--color-text-tertiary, #6B6560)',
              border: `0.5px solid ${user?.totp_enabled ? 'rgba(31,122,77,0.2)' : 'var(--color-border-secondary, #E5E0D8)'}`,
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'currentColor' }} />
            {user?.totp_enabled ? 'Activée' : 'Désactivée'}
          </span>
        </div>

        <div className="p-5 space-y-4">
          <div className="py-3 border-b flex items-center justify-between" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
            <div>
              <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
                2FA TOTP
              </div>
              <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                Application d'authentification (Google Authenticator, Authy)
              </div>
            </div>
            <div className="w-8 h-4 rounded-full relative flex-shrink-0" style={{ backgroundColor: user?.totp_enabled ? 'var(--color-amber, #C4962A)' : 'var(--color-border-secondary, #E5E0D8)' }}>
              <div
                className="w-3 h-3 rounded-full absolute top-0.5 transition-all"
                style={{
                  backgroundColor: 'white',
                  left: user?.totp_enabled ? '18px' : '2px',
                }}
              />
            </div>
          </div>

          <div className="py-3 border-b flex items-center justify-between" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
            <div>
              <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
                Codes de secours
              </div>
              <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                10 codes à usage unique générés — Consultez vos codes dans votre gestionnaire
              </div>
            </div>
            <button
              onClick={handleRegenerateBackupCodes}
              disabled={isRegenerating || !user?.totp_enabled}
              className="px-3 py-1 text-xs font-medium border rounded transition hover:opacity-80 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}
            >
              {isRegenerating ? 'Chargement...' : 'Regénérer'}
            </button>
          </div>

          <div className="flex justify-start gap-2 pt-2">
            {user?.totp_enabled ? (
              <button
                onClick={() => {
                  setError(null)
                  setShowDisableModal(true)
                }}
                disabled={isDisabling}
                className="px-3.5 py-1.5 text-xs font-medium rounded border transition hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{
                  borderColor: 'var(--color-text-danger, #E24B4A)',
                  color: 'var(--color-text-danger, #E24B4A)',
                }}
              >
                Désactiver la 2FA
              </button>
            ) : (
              <button
                onClick={handleSetup2FAClick}
                disabled={isSettingUp}
                className="px-3.5 py-1.5 text-xs font-medium rounded text-white transition hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ backgroundColor: 'var(--navy, #0F1C35)' }}
              >
                Activer la 2FA
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Card 2 — Passkeys */}
      <div className="border rounded-lg overflow-hidden" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
        <div className="p-3.5 border-b" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
          <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
            Clés de connexion (Passkeys)
          </div>
          <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
            Connexion sans mot de passe via biométrie ou clé matérielle
          </div>
        </div>

        <div className="p-12 text-center">
          <div className="inline-block mb-3 opacity-30">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <path d="M16 4C11.6 4 8 7.6 8 12c0 3.1 1.7 5.8 4.2 7.2L10 28h12l-2.2-8.8C22.3 17.8 24 15.1 24 12c0-4.4-3.6-8-8-8Z" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </div>
          <div className="text-sm font-medium" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
            Aucune passkey configurée
          </div>
          <div className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary, #6B6560)' }}>
            Ajoutez une clé biométrique ou FIDO2 pour vous connecter plus rapidement
          </div>
          <button
            className="mt-4 px-4 py-2 text-xs font-medium rounded text-white transition hover:opacity-90"
            style={{ backgroundColor: 'var(--navy, #0F1C35)' }}
            onClick={() => alert('Fonctionnalité à venir')}
          >
            + Ajouter une passkey
          </button>
        </div>
      </div>

      {/* Modal — Disable 2FA */}
      {showDisableModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full shadow-lg">
            <div className="p-6 border-b" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
              <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
                Désactiver l'authentification 2FA
              </h2>
              <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                Veuillez entrer votre mot de passe pour confirmer
              </p>
            </div>

            <div className="p-6 space-y-4">
              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium mb-2" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
                  Mot de passe
                </label>
                <input
                  type="password"
                  value={disablePassword}
                  onChange={(e) => setDisablePassword(e.target.value)}
                  placeholder="Entrez votre mot de passe"
                  disabled={isDisabling}
                  className="w-full px-3 py-2 border rounded-lg text-sm outline-none transition"
                  style={{
                    borderColor: 'var(--color-border-secondary, #E5E0D8)',
                    color: 'var(--color-text-primary, #0F1C35)',
                  }}
                />
              </div>
            </div>

            <div className="p-6 border-t flex gap-2" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
              <button
                onClick={() => {
                  setShowDisableModal(false)
                  setDisablePassword('')
                  setError(null)
                }}
                disabled={isDisabling}
                className="flex-1 px-3 py-2 text-xs font-medium rounded border transition disabled:opacity-50"
                style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}
              >
                Annuler
              </button>
              <button
                onClick={handleDisable2FA}
                disabled={isDisabling || !disablePassword.trim()}
                className="flex-1 px-3 py-2 text-xs font-medium rounded text-white transition disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ backgroundColor: 'var(--color-text-danger, #E24B4A)' }}
              >
                {isDisabling ? 'Chargement...' : 'Désactiver'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal — New Backup Codes */}
      {showNewCodes && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full shadow-lg max-h-screen overflow-y-auto">
            <div className="p-6 border-b sticky top-0 bg-white" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
              <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
                Nouveaux codes de secours
              </h2>
              <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                Sauvegardez ces codes dans un endroit sûr. Ils ne seront plus visibles après fermeture.
              </p>
            </div>

            <div className="p-6 space-y-3">
              {newBackupCodes.map((code, idx) => (
                <div
                  key={idx}
                  className="px-3 py-2 rounded-lg font-mono text-sm text-center"
                  style={{ backgroundColor: 'var(--color-background-secondary, #F5F3EE)', color: 'var(--color-text-primary, #0F1C35)' }}
                >
                  {code}
                </div>
              ))}
            </div>

            <div className="p-6 border-t flex gap-2" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
              <button
                onClick={() => {
                  setShowNewCodes(false)
                  setNewBackupCodes([])
                }}
                className="flex-1 px-3 py-2 text-xs font-medium rounded text-white transition"
                style={{ backgroundColor: 'var(--navy, #0F1C35)' }}
              >
                J'ai sauvegardé les codes
              </button>
              <button
                onClick={() => navigator.clipboard.writeText(newBackupCodes.join('\n'))}
                className="flex-1 px-3 py-2 text-xs font-medium rounded border transition hover:opacity-80"
                style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}
              >
                Copier
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal — Setup 2FA */}
      {showSetup2FAModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full shadow-lg max-h-screen overflow-y-auto">
            <div className="p-6 border-b" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
              <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
                Activer l'authentification 2FA
              </h2>
              <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                {isSettingUp && !setupQRCode ? 'Génération du QR code...' : 'Scannez ce code QR avec Google Authenticator ou Authy'}
              </p>
            </div>

            <div className="p-6 space-y-4">
              {setupError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                  {setupError}
                </div>
              )}

              {isSettingUp && !setupQRCode ? (
                <div className="flex justify-center items-center py-8">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-4 border-gray-300 border-t-amber-500 rounded-full animate-spin" style={{ borderTopColor: 'var(--color-amber, #C4962A)' }} />
                    <p className="text-sm" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                      Génération du QR code...
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  {setupQRCode && (
                    <div className="flex justify-center">
                      <img src={setupQRCode.startsWith('data:') ? setupQRCode : `data:image/png;base64,${setupQRCode}`} alt="QR Code 2FA" className="w-48 h-48" />
                    </div>
                  )}

                  {setupSecret && (
                    <div>
                      <p className="text-xs font-medium mb-2" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                        Ou saisissez ce code manuellement :
                      </p>
                      <div
                        className="p-3 rounded-lg font-mono text-sm text-center break-words"
                        style={{ backgroundColor: 'var(--color-background-secondary, #F5F3EE)', color: 'var(--color-text-primary, #0F1C35)' }}
                      >
                        {setupSecret.replace(/(.{4})/g, '$1 ').trim()}
                      </div>
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-medium mb-2" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
                      Entrez le code à 6 chiffres
                    </label>
                    <input
                      type="text"
                      value={verificationCode}
                      onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      placeholder="000000"
                      disabled={isVerifying}
                      maxLength={6}
                      className="w-full px-3 py-2 border rounded-lg text-sm outline-none transition text-center font-mono text-lg tracking-widest"
                      style={{
                        borderColor: 'var(--color-border-secondary, #E5E0D8)',
                        color: 'var(--color-text-primary, #0F1C35)',
                      }}
                    />
                  </div>
                </>
              )}
            </div>

            <div className="p-6 border-t flex gap-2" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
              <button
                onClick={closeSetup2FAModal}
                disabled={isVerifying}
                className="flex-1 px-3 py-2 text-xs font-medium rounded border transition disabled:opacity-50"
                style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}
              >
                Annuler
              </button>
              <button
                onClick={handleVerify2FA}
                disabled={isVerifying || verificationCode.length !== 6 || !setupQRCode}
                className="flex-1 px-3 py-2 text-xs font-medium rounded text-white transition disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ backgroundColor: 'var(--navy, #0F1C35)' }}
              >
                {isVerifying ? 'Vérification...' : 'Vérifier et activer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
