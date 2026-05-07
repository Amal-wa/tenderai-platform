'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { forgotPassword, resendPasswordReset, extractErrorMessage } from '@/lib/api'
import { Mail, KeyRound, Info, ArrowLeft } from 'lucide-react'

export default function ForgotPasswordForm() {
  const [step, setStep] = useState<'email' | 'sent'>('email')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000)
      return () => clearTimeout(timer)
    }
    return undefined
  }, [resendCooldown])

  const handleSubmit = async () => {
    if (!email || !email.includes('@')) {
      return
    }

    setIsLoading(true)
    setError('')

    try {
      await forgotPassword(email)
      setStep('sent')
      setResendCooldown(60)
    } catch (err) {
      const msg = extractErrorMessage(err)
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  const handleResend = async () => {
    setIsLoading(true)
    setError('')

    try {
      await resendPasswordReset(email)
      setResendCooldown(60)
    } catch (err) {
      const msg = extractErrorMessage(err)
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AnimatePresence mode="wait">
      {step === 'email' ? (
        <motion.div
          key="email-form"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
        >
          {/* Back Link */}
          <a
            href="/login"
            className="flex items-center gap-1.5 text-xs text-[#6B6560] hover:text-[#0d1b2e] transition-colors mb-8"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Retour à la connexion
          </a>

          {/* Header */}
          <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-[rgba(196,150,42,0.12)] mb-5">
            <KeyRound className="w-6 h-6 text-[#C4962A]" />
          </div>

          <h1 className="font-heading font-bold text-2xl text-[#0d1b2e] mt-5">
            Mot de passe oublié
          </h1>
          <p className="text-sm text-[#6B6560] mt-2 leading-relaxed">
            Entrez votre email. Si un compte existe, vous recevrez un lien de
            réinitialisation valable 15 minutes.
          </p>

          {/* Email Input */}
          <div className="mt-8">
            <label
              htmlFor="email"
              className="block text-xs font-semibold text-[#0d1b2e] mb-1.5"
            >
              Adresse email
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B6560] pointer-events-none" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="vous@entreprise.tn"
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-[#E5E0D8] bg-white text-sm text-[#0d1b2e] placeholder:text-[#6B6560]/50 focus:outline-none focus:ring-2 focus:ring-[#C4962A]/25 focus:border-[#C4962A] transition-all duration-200"
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2.5 mt-3"
            >
              <Info className="w-3.5 h-3.5 shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={isLoading || !email || !email.includes('@')}
            className="w-full flex items-center justify-center gap-2 bg-[#C4962A] hover:bg-[#d4a93c] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm py-3.5 rounded-xl transition-all duration-200 shadow-[0_4px_16px_rgba(196,150,42,0.30)] hover:shadow-[0_6px_24px_rgba(196,150,42,0.40)] mt-6"
          >
            <span>Envoyer le lien de réinitialisation</span>
          </button>
        </motion.div>
      ) : (
        /* Sent State */
        <motion.div
          key="sent-form"
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Success Card */}
          <div className="bg-white border border-[#E5E0D8] rounded-2xl p-8 text-center">
            {/* Icon */}
            <div className="flex items-center justify-center w-16 h-16 rounded-full bg-[#E8F5EE] mx-auto">
              <Mail className="w-8 h-8 text-[#1E7C5A]" />
            </div>

            <h2 className="font-heading font-bold text-2xl text-[#0d1b2e] mt-5">
              Email envoyé !
            </h2>
            <p className="text-sm text-[#6B6560] mt-2">Un lien a été envoyé à</p>
            <p className="text-sm font-semibold text-[#0d1b2e] mt-0.5">{email}</p>

            {/* Info Box */}
            <div className="mt-6 text-left flex gap-3 bg-[rgba(196,150,42,0.08)] border border-[#C4962A]/20 rounded-xl p-4">
              <Info className="w-4 h-4 text-[#C4962A] shrink-0 mt-0.5" />
              <p className="text-xs text-[#0d1b2e]/70 leading-relaxed">
                Le lien expire dans <strong>15 minutes</strong>. Vérifiez aussi
                vos spams et courriers indésirables.
              </p>
            </div>

            {/* Resend Button */}
            <div className="mt-6">
              {resendCooldown > 0 ? (
                <button
                  disabled
                  className="w-full text-sm font-semibold text-[#6B6560] bg-gray-100 py-2.5 rounded-xl opacity-60 cursor-not-allowed"
                >
                  Renvoyer dans {resendCooldown}s
                </button>
              ) : (
                <button
                  onClick={handleResend}
                  disabled={isLoading}
                  className="w-full text-sm font-semibold text-[#C4962A] border border-[#C4962A] bg-white hover:bg-[rgba(196,150,42,0.08)] py-2.5 rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Envoi en cours...' : 'Renvoyer l\'email'}
                </button>
              )}
            </div>

            {/* Back Link */}
            <a
              href="/login"
              className="text-xs text-[#6B6560] hover:text-[#0d1b2e] transition-colors flex justify-center items-center gap-1.5 mt-4"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Retour à la connexion
            </a>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
