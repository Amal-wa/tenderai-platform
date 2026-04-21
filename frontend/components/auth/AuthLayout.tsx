'use client'

import TenderAILogo from '@/components/ui/TenderAILogo'
import { Check } from 'lucide-react'

interface AuthLayoutProps {
  children: React.ReactNode
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  const bullets = [
    'Analyse NLP automatique des documents',
    'Score de conformité en temps réel',
    'Sécurité SOC2 · ISO 27001',
  ]

  return (
    <div className="min-h-screen flex">
      {/* LEFT PANEL - Hidden on mobile, visible on large screens */}
      <div className="hidden lg:flex lg:w-[45%] bg-[#0d1b2e] flex-col justify-between p-12">
        {/* TOP: Logo */}
        <div>
          <TenderAILogo size="lg" theme="light" />
        </div>

        {/* MIDDLE: Value proposition */}
        <div>
          <h2 className="font-heading font-bold text-3xl text-white leading-tight max-w-xs">
            Gérez vos appels d&apos;offres avec l&apos;intelligence qu&apos;ils méritent
          </h2>

          {/* Bullets */}
          <div className="mt-8 space-y-3">
            {bullets.map((bullet, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <Check className="w-4 h-4 text-[#C4962A] shrink-0" />
                <span className="text-sm text-white/70">{bullet}</span>
              </div>
            ))}
          </div>
        </div>

        {/* BOTTOM: Copyright */}
        <div>
          <p className="text-xs text-white/25">© 2026 TenderAI</p>
        </div>
      </div>

      {/* RIGHT PANEL - Cream background with dot pattern */}
      <div className="flex-1 bg-[#f5f0e8] flex items-center justify-center p-6 lg:p-12 relative">
        {/* Dot pattern background */}
        <svg className="absolute inset-0 w-full h-full opacity-[0.04] pointer-events-none">
          <defs>
            <pattern
              id="auth-dots"
              x="0"
              y="0"
              width="20"
              height="20"
              patternUnits="userSpaceOnUse"
            >
              <circle cx="1" cy="1" r="1" fill="#0d1b2e" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#auth-dots)" />
        </svg>

        {/* Content */}
        <div className="relative z-10 w-full max-w-[420px]">{children}</div>
      </div>
    </div>
  )
}
