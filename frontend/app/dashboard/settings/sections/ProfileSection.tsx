'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '@/context/AuthContext'
import { useSettings } from '@/hooks/useSettings'
import { extractErrorMessage } from '@/lib/api'

const profileSchema = z.object({
  first_name: z.string().min(2, 'Minimum 2 caractères').max(100),
  last_name: z.string().min(1, 'Requis').max(100),
  email: z.string().email('Email invalide'),
})

type ProfileFormData = z.infer<typeof profileSchema>

export default function ProfileSection({ onDirtyChange }: { isDirty: boolean; onDirtyChange: (dirty: boolean) => void }) {
  const { user, updateUserProfile } = useAuth()
  const { updateProfile } = useSettings()
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [successTimeout, setSuccessTimeout] = useState<NodeJS.Timeout | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty: formIsDirty },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.full_name?.split(' ')[0] || '',
      last_name: user?.full_name?.split(' ').slice(1).join(' ') || '',
      email: user?.email || '',
    },
  })

  useEffect(() => {
    onDirtyChange(formIsDirty)
  }, [formIsDirty, onDirtyChange])

  useEffect(() => {
    return () => {
      if (successTimeout) {
        clearTimeout(successTimeout)
      }
    }
  }, [successTimeout])

  const onSubmit = async (data: ProfileFormData) => {
    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      await updateProfile({
        full_name: `${data.first_name} ${data.last_name}`,
      })

      setSuccess('Profil mis à jour avec succès')
      updateUserProfile({
        full_name: `${data.first_name} ${data.last_name}`,
      })

      const timeout = setTimeout(() => setSuccess(null), 4000)
      setSuccessTimeout(timeout)
      onDirtyChange(false)
    } catch (err) {
      const msg = extractErrorMessage(err)
      setError(msg)
    } finally {
      setSaving(false)
    }
  }

  const userInitials = user?.full_name
    ?.split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase() || 'U'

  const userRole = typeof user?.role === 'string' ? user?.role : user?.role?.name

  return (
    <div className="space-y-6">
      {/* Card 1 — Avatar + Personal Info */}
      <div className="border rounded-lg overflow-hidden" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
        {/* Avatar Block */}
        <div className="p-5 border-b flex items-center gap-4" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
          <div
            className="w-15 h-15 rounded-full flex items-center justify-center flex-shrink-0 relative cursor-pointer group font-semibold text-xl"
            style={{ backgroundColor: 'var(--navy, #0F1C35)', color: 'var(--color-amber, #C4962A)' }}
          >
            {userInitials}
            <div className="absolute inset-0 rounded-full bg-black/45 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-white">
                <path d="M11 3.5 8 1 5 3.5M8 1v9" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 11v2a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
              </svg>
            </div>
          </div>

          <div>
            <div className="font-semibold" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
              {user?.full_name}
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span
                className="text-xs font-medium px-2 py-0.5 rounded-full"
                style={{
                  backgroundColor: 'rgba(196,150,42,0.12)',
                  color: 'var(--color-amber, #C4962A)',
                  border: '0.5px solid rgba(196,150,42,0.25)',
                }}
              >
                {userRole}
              </span>
              <span className="text-xs" style={{ color: 'var(--color-text-tertiary, #6B6560)' }}>
                {user?.tenant_name}
              </span>
            </div>
          </div>


        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3.5">
            <div>
              <label className="text-xs font-medium block mb-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                Prénom
              </label>
              <input
                {...register('first_name')}
                type="text"
                className="w-full h-8.5 px-2.5 border rounded text-sm focus:outline-none focus:ring-2 transition"
                style={{
                  borderColor: errors.first_name ? 'var(--color-danger, #E24B4A)' : 'var(--color-border-secondary, #E5E0D8)',
                  backgroundColor: 'var(--color-background-secondary, #F5F3EE)',
                  color: 'var(--color-text-primary, #0F1C35)',
                }}
              />
              {errors.first_name && <p className="text-xs mt-1 text-red-600">{errors.first_name.message}</p>}
            </div>

            <div>
              <label className="text-xs font-medium block mb-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                Nom de famille
              </label>
              <input
                {...register('last_name')}
                type="text"
                className="w-full h-8.5 px-2.5 border rounded text-sm focus:outline-none focus:ring-2 transition"
                style={{
                  borderColor: errors.last_name ? 'var(--color-danger, #E24B4A)' : 'var(--color-border-secondary, #E5E0D8)',
                  backgroundColor: 'var(--color-background-secondary, #F5F3EE)',
                  color: 'var(--color-text-primary, #0F1C35)',
                }}
              />
              {errors.last_name && <p className="text-xs mt-1 text-red-600">{errors.last_name.message}</p>}
            </div>

            <div className="col-span-2">
              <label className="text-xs font-medium block mb-1" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
                Adresse email
              </label>
              <input
                {...register('email')}
                type="email"
                disabled
                className="w-full h-8.5 px-2.5 border rounded text-sm focus:outline-none focus:ring-2 transition opacity-60"
                style={{
                  borderColor: 'var(--color-border-secondary, #E5E0D8)',
                  backgroundColor: 'var(--color-background-secondary, #F5F3EE)',
                  color: 'var(--color-text-primary, #0F1C35)',
                }}
              />
              <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary, #6B6560)' }}>
                Utilisée pour les notifications et la connexion
              </p>
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

          <div className="flex justify-end gap-2 pt-3 mt-4 border-t" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
            <button
              type="button"
              className="px-4 py-2 text-xs font-medium rounded border transition hover:bg-[var(--cream-2)]"
              style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)', color: 'var(--color-text-secondary, #3A3530)' }}
              onClick={() => onDirtyChange(false)}
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 text-xs font-medium rounded text-white transition hover:opacity-90"
              style={{ backgroundColor: 'var(--navy, #0F1C35)' }}
            >
              {saving ? 'Enregistrement...' : 'Enregistrer les modifications'}
            </button>
          </div>
        </form>
      </div>


    </div>
  )
}
