'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { login, extractErrorMessage } from '@/lib/api'
import TenderAILogo from '@/components/ui/TenderAILogo'
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  Loader2,
  ArrowRight,
} from 'lucide-react'

interface LoginFormProps {
  onSuccess: () => void
}

export default function LoginForm({ onSuccess }: LoginFormProps) {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    setError('')

    if (!email || !password) {
      setError('Veuillez remplir tous les champs')
      return
    }

    setIsLoading(true)
    try {
      // Call actual login API
      const response = await login(email, password)

      // Check if 2FA is required
      if (response.requires_2fa && response.partial_token) {
        // Store partial token and redirect to 2FA verification page
        sessionStorage.setItem('partial_token', response.partial_token)
        router.push('/2fa-login')
        return
      }

      // No 2FA required, login successful
      onSuccess()
    } catch (err) {
      const msg = extractErrorMessage(err)
      setError(msg)
      setIsLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
    >
      {/* Mobile Logo */}
      <div className="lg:hidden mb-8">
        <TenderAILogo size="md" theme="dark" />
      </div>

      {/* Header */}
      <h1 className="font-heading font-bold text-2xl text-[#0d1b2e]">
        Bon retour
      </h1>
      <p className="text-sm text-[#6B6560] mt-1">
        Connectez-vous à votre espace
      </p>

      {/* Email Field */}
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

      {/* Password Field */}
      <div className="mt-4">
        <div className="flex justify-between items-center mb-1.5">
          <label
            htmlFor="password"
            className="block text-xs font-semibold text-[#0d1b2e]"
          >
            Mot de passe
          </label>
          <a
            href="/forgot-password"
            className="text-xs text-[#C4962A] hover:text-[#d4a93c] transition-colors"
          >
            Mot de passe oublié ?
          </a>
        </div>
        <div className="relative">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B6560] pointer-events-none" />
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full pl-10 pr-10 py-3 rounded-xl border border-[#E5E0D8] bg-white text-sm text-[#0d1b2e] placeholder:text-[#6B6560]/50 focus:outline-none focus:ring-2 focus:ring-[#C4962A]/25 focus:border-[#C4962A] transition-all duration-200"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B6560] hover:text-[#0d1b2e] transition-colors"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? (
              <EyeOff className="w-4 h-4" />
            ) : (
              <Eye className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2.5 mt-3"
        >
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{error}</span>
        </motion.div>
      )}

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={isLoading || !email || !password}
        className="w-full flex items-center justify-center gap-2 bg-[#C4962A] hover:bg-[#d4a93c] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm py-3.5 rounded-xl transition-all duration-200 shadow-[0_4px_16px_rgba(196,150,42,0.30)] hover:shadow-[0_6px_24px_rgba(196,150,42,0.40)] mt-6"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Connexion...</span>
          </>
        ) : (
          <>
            <span>Se connecter</span>
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>

      {/* Signup Link */}
      <p className="text-xs text-[#6B6560] mt-6 text-center">
        Pas encore de compte ?{' '}
        <a
          href="/register"
          className="text-[#C4962A] font-semibold hover:text-[#d4a93c] transition-colors"
        >
          Créer un compte
        </a>
      </p>
    </motion.div>
  )
}
