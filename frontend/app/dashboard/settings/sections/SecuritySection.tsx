'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Monitor, Smartphone, Eye, EyeOff } from 'lucide-react'
import { useSettings } from '@/hooks/useSettings'
import { extractErrorMessage } from '@/lib/api'
import type { ActiveSession } from '@/types/settings'

const passwordSchema = z
  .object({
    current_password: z.string().min(1, 'Requis'),
    new_password: z.string().min(8, 'Minimum 8 caractères').max(128),
    confirm_password: z.string(),
  })
  .refine(d => d.new_password === d.confirm_password, {
    message: 'Les mots de passe ne correspondent pas',
    path: ['confirm_password'],
  })
  .refine(d => d.current_password !== d.new_password, {
    message: 'Le nouveau mot de passe doit être différent',
    path: ['new_password'],
  })

type PasswordFormData = z.infer<typeof passwordSchema>

export default function SecuritySection({ onDirtyChange }: { isDirty: boolean; onDirtyChange: (dirty: boolean) => void }) {
  const { changePassword, listSessions, revokeSession } = useSettings()
  const [showPasswordForm, setShowPasswordForm] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [passwordStrength, setPasswordStrength] = useState(0)
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sessions, setSessions] = useState<ActiveSession[]>([])
  const [loadingSessions, setLoadingSessions] = useState(true)
  const [revoking, setRevoking] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty: formIsDirty },
    watch,
    reset,
  } = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
  })

  const newPassword = watch('new_password')

  useEffect(() => {
    onDirtyChange(formIsDirty && showPasswordForm)
  }, [formIsDirty, showPasswordForm, onDirtyChange])

  useEffect(() => {
    const loadSessions = async () => {
      try {
        const res = await listSessions()
        setSessions(res.data || [])
      } catch {
        setSessions([])
      } finally {
        setLoadingSessions(false)
      }
    }
    loadSessions()
  }, [])

  useEffect(() => {
    const score = calculatePasswordStrength(newPassword)
    setPasswordStrength(score)
  }, [newPassword])

  const calculatePasswordStrength = (pwd: string): number => {
    if (!pwd) return 0
    let score = 0
    if (pwd.length >= 8) score++
    if (pwd.length >= 12) score++
    if (/[A-Z]/.test(pwd) && /[0-9]/.test(pwd)) score++
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) score++
    return Math.min(score, 4)
  }

  const getStrengthColor = (score: number): string => {
    if (score === 0) return '#D1D5DB'
    if (score === 1) return '#EF4444'
    if (score === 2) return '#F59E0B'
    if (score === 3) return '#10B981'
    return '#059669'
  }

  const onPasswordSubmit = async (data: PasswordFormData) => {
    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      await changePassword(data)
      setSuccess('Toutes vos autres sessions ont été déconnectées.')
      setSessions([])
      reset()
      setShowPasswordForm(false)
      onDirtyChange(false)
    } catch (err) {
      const msg = extractErrorMessage(err)
      setError(msg)
    } finally {
      setSaving(false)
    }
  }

  const handleRevokeSession = async (sessionId: string) => {
    setRevoking(sessionId)
    try {
      await revokeSession(sessionId)
      setSessions(sessions.filter(s => s.id !== sessionId))
    } catch (err) {
      console.error(extractErrorMessage(err))
    } finally {
      setRevoking(null)
    }
  }

  const handleRevokeAllSessions = async () => {
    if (!confirm('Êtes-vous sûr ? Vous serez déconnecté de tous vos appareils.')) return
    for (const session of sessions) {
      try {
        await revokeSession(session.id)
      } catch (err) {
        console.error(extractErrorMessage(err))
      }
    }
    setSessions([])
  }

  return (
    <div className="space-y-6">
      {/* Card 1 — Password */}
      <div className="border rounded-lg overflow-hidden" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
        <div className="p-3.5 border-b flex items-center justify-between" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
          <div>
            <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
              Mot de passe
            </div>
            <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
              Dernière modification il y a 42 jours
            </div>
          </div>
          <button
            onClick={() => setShowPasswordForm(!showPasswordForm)}
            className="px-3 py-1 text-xs font-medium border rounded transition hover:opacity-80"
            style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}
          >
            {showPasswordForm ? 'Masquer' : 'Modifier'}
          </button>
        </div>

        {showPasswordForm && (
          <form onSubmit={handleSubmit(onPasswordSubmit)} className="p-5 border-t space-y-4" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
            <div className="grid grid-cols-2 gap-3.5">
              <div>
                <label className="text-xs font-medium block mb-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                  Mot de passe actuel
                </label>
                <div className="relative">
                  <input
                    {...register('current_password')}
                    type={showPassword ? 'text' : 'password'}
                    className="w-full h-8.5 px-2.5 border rounded text-sm focus:outline-none focus:ring-2 pr-8 transition"
                    style={{
                      borderColor: errors.current_password ? 'var(--color-danger, #E24B4A)' : 'var(--color-border-secondary, #E5E0D8)',
                      backgroundColor: 'var(--color-background-secondary, #F5F3EE)',
                      color: 'var(--color-text-primary, #0F1C35)',
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2 top-1/2 -translate-y-1/2"
                  >
                    {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
                {errors.current_password && <p className="text-xs mt-1 text-red-600">{errors.current_password.message}</p>}
              </div>

              <div style={{ visibility: 'hidden' }} />

              <div>
                <label className="text-xs font-medium block mb-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                  Nouveau mot de passe
                </label>
                <div className="relative">
                  <input
                    {...register('new_password')}
                    type={showNewPassword ? 'text' : 'password'}
                    placeholder="Min. 12 caractères"
                    className="w-full h-8.5 px-2.5 border rounded text-sm focus:outline-none focus:ring-2 pr-8 transition"
                    style={{
                      borderColor: errors.new_password ? 'var(--color-danger, #E24B4A)' : 'var(--color-border-secondary, #E5E0D8)',
                      backgroundColor: 'var(--color-background-secondary, #F5F3EE)',
                      color: 'var(--color-text-primary, #0F1C35)',
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute right-2 top-1/2 -translate-y-1/2"
                  >
                    {showNewPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
                {newPassword && (
                  <div className="mt-2 flex gap-1">
                    {[0, 1, 2, 3].map(i => (
                      <div
                        key={i}
                        className="h-1 flex-1 rounded-full transition"
                        style={{
                          backgroundColor: i < passwordStrength ? getStrengthColor(passwordStrength) : '#D1D5DB',
                        }}
                      />
                    ))}
                  </div>
                )}
                {errors.new_password && <p className="text-xs mt-1 text-red-600">{errors.new_password.message}</p>}
              </div>

              <div>
                <label className="text-xs font-medium block mb-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                  Confirmer
                </label>
                <div className="relative">
                  <input
                    {...register('confirm_password')}
                    type={showConfirm ? 'text' : 'password'}
                    placeholder="Répétez le mot de passe"
                    className="w-full h-8.5 px-2.5 border rounded text-sm focus:outline-none focus:ring-2 pr-8 transition"
                    style={{
                      borderColor: errors.confirm_password ? 'var(--color-danger, #E24B4A)' : 'var(--color-border-secondary, #E5E0D8)',
                      backgroundColor: 'var(--color-background-secondary, #F5F3EE)',
                      color: 'var(--color-text-primary, #0F1C35)',
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-2 top-1/2 -translate-y-1/2"
                  >
                    {showConfirm ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
                {errors.confirm_password && <p className="text-xs mt-1 text-red-600">{errors.confirm_password.message}</p>}
              </div>
            </div>

            {success && (
              <div className="p-3 rounded text-xs font-medium" style={{ backgroundColor: 'var(--success-bg, #E1F5EE)', color: 'var(--success, #1D9E75)' }}>
                {success}
              </div>
            )}

            {error && (
              <div className="p-3 rounded text-xs font-medium" style={{ backgroundColor: 'var(--color-danger-bg, #FCEAEA)', color: 'var(--color-danger, #E24B4A)' }}>
                {error}
              </div>
            )}

            <div className="flex justify-end gap-2 pt-3 border-t" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
              <button
                type="button"
                onClick={() => {
                  setShowPasswordForm(false)
                  reset()
                  onDirtyChange(false)
                }}
                className="px-4 py-2 text-xs font-medium rounded border transition hover:bg-[var(--cream-2)]"
                style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 text-xs font-medium rounded text-white transition hover:opacity-90"
                style={{ backgroundColor: 'var(--navy, #0F1C35)' }}
              >
                {saving ? 'Mise à jour...' : 'Mettre à jour'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Card 2 — Active Sessions */}
      <div className="border rounded-lg overflow-hidden" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
        <div className="p-3.5 border-b" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
          <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
            Sessions actives
          </div>
          <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
            Appareils connectés à votre compte
          </div>
        </div>

        <div className="p-5 space-y-3">
          {loadingSessions ? (
            <p className="text-xs" style={{ color: 'var(--color-text-tertiary, #6B6560)' }}>
              Chargement des sessions...
            </p>
          ) : sessions.length === 0 ? (
            <p className="text-xs" style={{ color: 'var(--color-text-tertiary, #6B6560)' }}>
              Aucune session active
            </p>
          ) : (
            sessions.map(session => {
              const isCurrent = session.is_current
              const icon = session.user_agent?.includes('iPhone') || session.user_agent?.includes('Android') ? Smartphone : Monitor
              const Icon = icon
              return (
                <div key={session.id} className="flex items-center gap-3 py-2.5 border-b" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
                  <div
                    className="w-8 h-8 rounded border flex items-center justify-center flex-shrink-0"
                    style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}
                  >
                    <Icon size={16} style={{ color: 'var(--color-text-primary, #0F1C35)' }} />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium flex items-center gap-1.5" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
                      {session.user_agent || 'Appareil inconnu'}
                      {isCurrent && (
                        <span
                          className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
                          style={{
                            backgroundColor: 'rgba(31,122,77,0.1)',
                            color: '#1F7A4D',
                            border: '0.5px solid rgba(31,122,77,0.2)',
                          }}
                        >
                          Actuel
                        </span>
                      )}
                    </div>
                    <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-tertiary, #6B6560)' }}>
                      {session.ip_address || 'IP inconnue'} · Connecté maintenant
                    </div>
                  </div>
                  {!isCurrent && (
                    <button
                      onClick={() => handleRevokeSession(session.id)}
                      disabled={revoking === session.id}
                      className="px-2.5 py-1 text-xs font-medium rounded border transition hover:opacity-80"
                      style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}
                    >
                      {revoking === session.id ? 'Révocation...' : 'Révoquer'}
                    </button>
                  )}
                </div>
              )
            })
          )}
        </div>

        {sessions.length > 0 && (
          <div className="p-3.5 border-t flex justify-end" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
            <button
              onClick={handleRevokeAllSessions}
              className="px-3.5 py-1.5 text-xs font-medium rounded border transition hover:opacity-90"
              style={{
                borderColor: 'var(--color-text-danger, #E24B4A)',
                color: 'var(--color-text-danger, #E24B4A)',
              }}
            >
              Révoquer toutes les sessions
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
