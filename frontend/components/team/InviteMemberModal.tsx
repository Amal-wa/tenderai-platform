'use client'

import { useState, useRef, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Loader2 } from 'lucide-react'
import { extractErrorMessage } from '@/lib/api'
import { showToast } from '@/lib/toast'
import { useAuth } from '@/context/AuthContext'
import type { InviteMemberModalProps, InviteMemberPayload, InviteRole } from '@/types/team'
import { ROLE_DESCRIPTIONS, INVITE_ROLES } from '@/types/team'

/**
 * Generate a UUIDv4 string without external dependencies
 */
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

const inviteFormSchema = z.object({
  email: z.string().email('Email invalide').min(1, 'Champ requis'),
  role: z.enum(['admin', 'manager', 'analyst', 'contributor', 'viewer']),
  message: z.string().max(300, 'Maximum 300 caractères').optional().nullable(),
})

type InviteFormData = z.infer<typeof inviteFormSchema>

export default function InviteMemberModal({
  isOpen,
  onClose,
  onSuccess,
}: InviteMemberModalProps): JSX.Element {
  const authContext = useAuth()
  const user = authContext?.user || null
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [retryCountdown, setRetryCountdown] = useState(0)
  const idempotencyKeyRef = useRef<string>('')
  const messageCharCount = useRef(0)

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<InviteFormData>({
    resolver: zodResolver(inviteFormSchema),
    mode: 'onBlur',
    defaultValues: {
      email: '',
      role: 'contributor',
      message: '',
    },
  })

  const selectedRole = watch('role') as InviteRole
  const messageValue = watch('message')

  // Update character count
  useEffect(() => {
    messageCharCount.current = messageValue?.length || 0
  }, [messageValue])

  // Generate idempotency key on modal open
  useEffect(() => {
    if (isOpen && !idempotencyKeyRef.current) {
      idempotencyKeyRef.current = generateUUID()
    }
  }, [isOpen])

  // Countdown timer for 429 errors
  useEffect(() => {
    if (retryCountdown <= 0) return
    const timer = setTimeout(() => setRetryCountdown(retryCountdown - 1), 1000)
    return () => clearTimeout(timer)
  }, [retryCountdown])

  const handleClose = (): void => {
    reset()
    setSubmitError('')
    setRetryCountdown(0)
    idempotencyKeyRef.current = ''
    onClose()
  }

  const onSubmit = async (data: InviteFormData): Promise<void> => {
    setIsSubmitting(true)
    setSubmitError('')

    try {
      const apiInstance = (await import('@/lib/api')).default
      
      if (!apiInstance) {
        throw new Error('API not available')
      }

      const payload: InviteMemberPayload = {
        email: data.email,
        role: data.role as InviteRole,
        message: data.message || undefined,
      }

      const headers = {
        'Idempotency-Key': idempotencyKeyRef.current,
      }

      await apiInstance.post('/api/v1/admin/users/invite', payload, { headers })

      showToast(`Invitation envoyée à ${data.email}`, 'success')
      handleClose()
      onSuccess(data.email)
    } catch (error: any) {
      if (error?.response?.status === 429) {
        const resetTime = error.response?.headers?.['x-ratelimit-reset']
        const retryAfter = parseInt(resetTime) || 60

        setRetryCountdown(retryAfter)
        setSubmitError(`Trop de tentatives. Réessayez dans ${retryAfter}s`)
      } else {
        const errorMsg = extractErrorMessage(error)
        setSubmitError(errorMsg || 'Erreur lors de l\'envoi de l\'invitation')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  // Don't render if not authenticated or not admin
  const userRole = typeof user?.role === 'string' ? user?.role : user?.role?.name
  if (!user || (userRole !== 'admin' && userRole !== 'superadmin')) {
    return <></>
  }

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            key="overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="fixed inset-0 z-50 bg-black/50"
            style={{ backgroundColor: 'rgba(15, 28, 53, 0.5)' }}
          />

          {/* Modal Panel */}
          <motion.div
            key="modal"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div
              className="w-full max-w-[480px] rounded-lg border"
              style={{
                backgroundColor: 'var(--color-background-primary, #F5F3EE)',
                borderColor: 'var(--color-border-tertiary, #E5E0D8)',
                borderWidth: '0.5px',
              }}
            >
              {/* Header */}
              <div className="flex items-start justify-between border-b p-6" style={{ borderBottomColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
                <div>
                  <h2 className="text-base font-heading font-semibold" style={{ color: 'var(--navy, #0F1C35)' }}>
                    Inviter un membre
                  </h2>
                  <p className="mt-1 text-xs text-gray-500">
                    Un email d'invitation sera envoyé. Le lien expire dans 48h.
                  </p>
                </div>
                <button
                  onClick={handleClose}
                  className="inline-flex items-center justify-center rounded-md p-1 transition-colors hover:bg-gray-100"
                >
                  <X size={20} style={{ color: 'var(--navy, #0F1C35)' }} />
                </button>
              </div>

              {/* Form Content */}
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 p-6">
                {/* Email Field */}
                <div>
                  <label className="block text-xs font-medium" style={{ color: 'var(--color-text-secondary, #6B6560)' }}>
                    Adresse email
                  </label>
                  <input
                    type="email"
                    placeholder="prenom.nom@organisation.tn"
                    {...register('email')}
                    className="mt-2 w-full rounded-md border px-3 py-2 text-sm outline-none transition-colors focus:ring-2"
                    style={{
                      borderColor: errors.email ? '#E24B4A' : 'var(--color-border-tertiary, #E5E0D8)',
                    }}
                  />
                  {errors.email && (
                    <p className="mt-1 text-xs font-medium" style={{ color: '#E24B4A' }}>
                      {errors.email.message}
                    </p>
                  )}
                </div>

                {/* Role Field */}
                <div>
                  <label className="block text-xs font-medium" style={{ color: 'var(--color-text-secondary, #6B6560)' }}>
                    Rôle attribué
                  </label>
                  <select
                    {...register('role')}
                    className="mt-2 w-full rounded-md border px-3 py-2 text-sm outline-none transition-colors focus:ring-2"
                    style={{
                      borderColor: 'var(--color-border-tertiary, #E5E0D8)',
                      color: 'var(--navy, #0F1C35)',
                    }}
                  >
                    {INVITE_ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role.charAt(0).toUpperCase() + role.slice(1)}
                      </option>
                    ))}
                  </select>
                  {selectedRole && (
                    <p className="mt-2 text-xs text-gray-600">
                      {ROLE_DESCRIPTIONS[selectedRole]}
                    </p>
                  )}
                </div>

                {/* Message Field */}
                <div>
                  <label className="block text-xs font-medium" style={{ color: 'var(--color-text-secondary, #6B6560)' }}>
                    Message personnalisé (optionnel)
                  </label>
                  <textarea
                    placeholder="Ex : Bonjour, rejoignez notre espace TenderAI pour collaborer sur nos appels d'offres."
                    {...register('message')}
                    rows={3}
                    className="mt-2 w-full rounded-md border px-3 py-2 text-sm outline-none transition-colors focus:ring-2 resize-none"
                    style={{
                      borderColor: 'var(--color-border-tertiary, #E5E0D8)',
                      color: 'var(--navy, #0F1C35)',
                    }}
                  />
                  <div className="mt-1 flex justify-end text-xs text-gray-500">
                    {messageCharCount.current}/300
                  </div>
                </div>

                {/* Error Message */}
                {submitError && (
                  <div className="rounded-md border p-3" style={{ borderColor: '#E24B4A', backgroundColor: '#FCEAEA' }}>
                    <p className="text-xs font-medium" style={{ color: '#E24B4A' }}>
                      {submitError}
                    </p>
                  </div>
                )}
              </form>

              {/* Footer */}
              <div className="flex gap-3 border-t p-6" style={{ borderTopColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
                <button
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="flex-1 rounded-md border px-4 py-2 text-sm font-semibold transition-colors disabled:opacity-50"
                  style={{
                    borderColor: 'var(--color-border-tertiary, #E5E0D8)',
                    color: 'var(--navy, #0F1C35)',
                  }}
                >
                  Annuler
                </button>
                <button
                  onClick={handleSubmit(onSubmit)}
                  disabled={isSubmitting || retryCountdown > 0}
                  className="flex-1 inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition-colors disabled:opacity-50"
                  style={{
                    backgroundColor: isSubmitting || retryCountdown > 0 ? '#C4962A99' : 'var(--navy, #0F1C35)',
                    color: 'white',
                  }}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Envoi...
                    </>
                  ) : (
                    'Envoyer l\'invitation'
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
