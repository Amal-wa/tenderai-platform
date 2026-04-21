'use client'

import Link from 'next/link'
import TenderAILogo from '@/components/ui/TenderAILogo'

export default function Navbar(): JSX.Element {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md border-b border-cream-border h-[62px] bg-cream/85">
      <div className="h-full px-12 flex items-center justify-between max-w-7xl mx-auto w-full">
        {/* Logo */}
        <div className="flex-shrink-0">
          <TenderAILogo size="lg" theme="light" showText={true} />
        </div>

        {/* Nav Links */}
        <div className="hidden md:flex gap-9">
          <a
            href="#features"
            className="text-sm font-medium text-gray-400 hover:text-amber transition-colors"
          >
            Fonctionnalités
          </a>
          <a
            href="#pricing"
            className="text-sm font-medium text-gray-400 hover:text-amber transition-colors"
          >
            Tarifs
          </a>
          <a
            href="#"
            className="text-sm font-medium text-gray-400 hover:text-amber transition-colors"
          >
            Documentation
          </a>
          <a
            href="#"
            className="text-sm font-medium text-gray-400 hover:text-amber transition-colors"
          >
            À propos
          </a>
        </div>

        {/* CTA Buttons */}
        <div className="flex gap-2 items-center">
          <Link
            href="/login"
            className="px-4 py-2 border border-cream-border rounded-lg text-sm font-medium text-gray-600 hover:border-navy hover:text-navy transition-all"
          >
            Se connecter
          </Link>
          <Link
            href="/register"
            className="px-5 py-2 bg-amber text-white rounded-lg text-sm font-semibold hover:bg-amber-light transition-colors shadow-lg shadow-amber/35"
          >
            Essai gratuit →
          </Link>
        </div>
      </div>

      <style jsx>{`
        @media (max-width: 768px) {
          nav {
            padding: 0 1.5rem;
          }
        }
      `}</style>
    </nav>
  )
}
