'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import {
  ShieldCheck,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
} from 'lucide-react'

interface TotpFormProps {
  onBack: () => void
}

export default function TotpForm({ onBack }: TotpFormProps) {
  const router = useRouter()
  const [digits, setDigits] = useState<string[]>(Array(6).fill(''))
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isSuccess, setIsSuccess] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  // Countdown timer for resend
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
      return () => clearTimeout(timer)
    }
    return undefined
  }, [countdown])

  const handleChange = (index: number, value: string) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return

    const newDigits = [...digits]
    newDigits[index] = value
    setDigits(newDigits)
    setError('')

    // Move to next input if digit entered
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault()
    const pasted = e.clipboardData
      .getData('text')
      .replace(/\D/g, '')
      .slice(0, 6)

    if (pasted.length === 6) {
      setDigits(pasted.split(''))
      inputRefs.current[5]?.focus()
    }
  }

  const handleVerify = async () => {
    setIsLoading(true)
    setError('')

    try {
      // TODO: Replace with actual API call
      await new Promise((r) => setTimeout(r, 1200))

      const code = digits.join('')

      // Mock validation - only accept "000000" for demo
      if (code === '000000') {
        setIsSuccess(true)
        setIsLoading(false)

        // Redirect after success animation
        setTimeout(() => {
          router.push('/dashboard')
        }, 1500)
      } else {
        setError('Code incorrect. Vérifiez votre application.')
        setIsLoading(false)

        // Shake animation: focus first input and clear digits
        shake()
        setDigits(Array(6).fill(''))
        inputRefs.current[0]?.focus()
      }
    } catch (err) {
      setError('Erreur lors de la vérification. Veuillez réessayer.')
      setIsLoading(false)
    }
  }

  const shake = () => {
    // Apply shake class to each input
    inputRefs.current.forEach((input) => {
      if (input) {
        input.classList.remove('shake')
        // Trigger reflow
        void input.offsetWidth
        input.classList.add('shake')
      }
    })
  }

  const handleResend = () => {
    setCountdown(30)
    setDigits(Array(6).fill(''))
    setError('')
    inputRefs.current[0]?.focus()
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      transition={{ duration: 0.3 }}
    >
      <AnimatePresence mode="wait">
        {!isSuccess ? (
          <div key="totp-form">
            {/* Header */}
            <div className="flex items-center justify-center w-12 h-12 rounded-2xl bg-[rgba(196,150,42,0.12)] mb-5 mx-auto">
              <ShieldCheck className="w-6 h-6 text-[#C4962A]" />
            </div>

            <h1 className="font-heading font-bold text-2xl text-[#0d1b2e]">
              Vérification en deux étapes
            </h1>
            <p className="text-sm text-[#6B6560] mt-2 leading-relaxed">
              Entrez le code à 6 chiffres de votre application d&apos;authentification
                pour sécuriser votre compte.
            </p>

            {/* 6-Digit Inputs */}
            <div className="flex gap-2.5 justify-center mt-8">
              {digits.map((digit, i) => (
                <input
                  key={i}
                  ref={(el) => {
                    inputRefs.current[i] = el
                  }}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleChange(i, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(i, e)}
                  onPaste={i === 0 ? handlePaste : undefined}
                  aria-label={`Chiffre ${i + 1} du code`}
                  className={`w-12 h-14 text-center text-xl font-bold text-[#0d1b2e] border-2 rounded-xl bg-white focus:outline-none focus:ring-2 transition-all duration-150 ${
                    digit
                      ? 'border-[#C4962A]/60 focus:border-[#C4962A] focus:ring-[#C4962A]/20'
                      : 'border-[#E5E0D8] focus:border-[#C4962A] focus:ring-[#C4962A]/20'
                  } ${error ? 'border-red-300' : ''}`}
                />
              ))}
            </div>

            {/* Progress Dots */}
            <div className="flex justify-center gap-1.5 mt-4">
              {digits.map((d, i) => (
                <div
                  key={i}
                  className={`w-1.5 h-1.5 rounded-full transition-colors ${
                    d ? 'bg-[#C4962A]' : 'bg-[#E5E0D8]'
                  }`}
                />
              ))}
            </div>

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2.5 mt-4"
              >
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>{error}</span>
              </motion.div>
            )}

            {/* Verify Button */}
            <button
              onClick={handleVerify}
              disabled={digits.join('').length < 6 || isLoading}
              className="w-full flex items-center justify-center gap-2 bg-[#C4962A] hover:bg-[#d4a93c] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm py-3.5 rounded-xl transition-all duration-200 shadow-[0_4px_16px_rgba(196,150,42,0.30)] hover:shadow-[0_6px_24px_rgba(196,150,42,0.40)] mt-6"
            >
              <span>Vérifier le code</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            {/* Resend Section */}
            <div className="mt-4 text-center">
              {countdown > 0 ? (
                <p className="text-xs text-[#6B6560]">
                  Renvoyer le code dans{' '}
                  <span className="font-semibold text-[#0d1b2e]">{countdown}s</span>
                </p>
              ) : (
                <button
                  onClick={handleResend}
                  className="text-xs text-[#C4962A] font-semibold hover:text-[#d4a93c] transition-colors"
                >
                  Renvoyer le code
                </button>
              )}
            </div>

            {/* Back Link */}
            <div className="mt-6 flex justify-center">
              <button
                onClick={onBack}
                className="flex items-center gap-1.5 text-xs text-[#6B6560] hover:text-[#0d1b2e] transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Retour à la connexion
              </button>
            </div>
          </div>
        ) : (
          /* Success State */
          <motion.div
            key="success"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-center"
          >
            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-[#E8F5EE] mx-auto">
              <CheckCircle className="w-12 h-12 text-[#1E7C5A]" />
            </div>
            <p className="font-heading font-bold text-lg text-[#0d1b2e] mt-4">
              Authentification réussie !
            </p>
            <p className="text-xs text-[#6B6560] mt-2">Redirection en cours…</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
