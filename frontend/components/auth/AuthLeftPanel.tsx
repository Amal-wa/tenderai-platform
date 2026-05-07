'use client'

import { ReactNode } from 'react'
import TenderAILogo from '@/components/ui/TenderAILogo'
import { useAuth } from '@/context/AuthContext'

export interface AuthLeftPanelProps {
  headline: ReactNode
  subtext: string | ((orgName: string) => string)
  features?: string[]
  warning?: {
    type: 'warning' | 'danger'
    title: string
    items: string[]
  }
  footerNote?: string
  inviteBadge?: {
    orgName: string
    email: string
  }
}

export default function AuthLeftPanel({
  headline,
  subtext,
  features,
  warning,
  footerNote,
  inviteBadge,
}: AuthLeftPanelProps): JSX.Element {
  const { tenant } = useAuth()

  const orgName = tenant?.name || 'votre organisation'
  const displaySubtext = typeof subtext === 'function' ? subtext(orgName) : subtext

  return (
    <div className="hidden lg:flex lg:w-[40%] bg-navy flex-col justify-between p-12 overflow-y-auto">
      {/* Top — Logo */}
      <div>
        <TenderAILogo size="lg" theme="dark" showText={true} />
      </div>

      {/* Middle — Headline + Content */}
      <div className="flex flex-col gap-8 my-8">
        {/* Invite badge (for invitation mode) */}
        {inviteBadge && (
          <div className="bg-white/10 border border-white/20 rounded-2xl p-5 mb-4">
            <div className="text-xs text-white/50 uppercase tracking-wide mb-2">Invitation reçue de</div>
            <div className="text-white font-semibold">{inviteBadge.orgName}</div>
            <div className="text-amber text-xs mt-1">{inviteBadge.email}</div>
          </div>
        )}

        {/* Headline */}
        <div>
          <h2 className="font-heading text-3xl font-bold text-white leading-tight mb-4">
            {headline}
          </h2>
          <p className="text-white/60 text-sm leading-relaxed">{displaySubtext}</p>
        </div>

        {/* Warning Box */}
        {warning && (
          <div
            className={`p-4 rounded-lg border flex gap-3 ${
              warning.type === 'danger'
                ? 'bg-danger/10 border-danger/20'
                : 'bg-amber/10 border-amber/20'
            }`}
          >
            <svg
              className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                warning.type === 'danger' ? 'text-danger' : 'text-amber'
              }`}
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <p className={`text-sm font-semibold mb-2 ${warning.type === 'danger' ? 'text-danger' : 'text-amber'}`}>
                {warning.title}
              </p>
              <ul className={`space-y-1 text-xs ${warning.type === 'danger' ? 'text-danger/80' : 'text-amber/80'}`}>
                {warning.items.map((item, idx) => (
                  <li key={idx} className="flex gap-2">
                    <span className="flex-shrink-0">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Features List */}
        {features && (
          <ul className="space-y-3">
            {features.map((item) => (
              <li key={item} className="flex items-start gap-3 text-sm text-white/80">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  className="mt-0.5 flex-shrink-0"
                  aria-hidden="true"
                >
                  <circle cx="8" cy="8" r="7" fill="rgba(196,150,42,0.2)" />
                  <path
                    d="M5 8l2.5 2.5L11 5"
                    stroke="#C4962A"
                    strokeWidth="1.3"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                {item}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      {footerNote && (
        <div className="pt-8 border-t border-white/10">
          <p className="text-xs text-white/40">{footerNote}</p>
        </div>
      )}
    </div>
  )
}
