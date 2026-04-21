'use client'

import { useRouter } from 'next/navigation'
import DashboardMockup from './DashboardMockup'

export default function HeroSection(): JSX.Element {
  const router = useRouter()

  return (
    <section className="relative bg-cream py-24 px-12">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-[44%_56%] gap-10 items-center">
          {/* Left: Hero text */}
          <div className="animate-fade-up">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-amber/10 border border-amber/30 px-3.5 py-1.5 rounded-full mb-6 animate-fade-up">
              <span className="w-1.5 h-1.5 rounded-full bg-amber animate-pulse"></span>
              <span className="text-xs font-semibold text-amber">Nouveau — Analyse NLP des appels d'offres</span>
            </div>

            {/* Title */}
            <h1 className="font-heading text-5xl font-bold leading-tight text-navy mb-5 animate-fade-up">
              Remportez plus d'appels d'offres
              <br />
              <em className="italic text-amber">grâce à l'IA.</em>
            </h1>

            {/* Subtitle */}
            <p className="text-lg text-gray-500 max-w-sm mb-9 leading-relaxed animate-fade-up">
              Automatisez l'analyse, la conformité et le suivi de vos marchés
              publics. Gagnez du temps, remportez plus d'appels.
            </p>

            {/* CTA Buttons */}
            <div className="flex gap-3 flex-wrap mb-9 animate-fade-up">
              <button
                onClick={() => router.push('/register')}
                className="flex items-center gap-2 px-7 py-3.5 bg-amber text-white rounded-xl font-heading font-semibold hover:bg-amber-light transition-all transform hover:-translate-y-0.5 shadow-lg shadow-amber/35 cursor-pointer"
              >
                Commencer maintenant
                <span>→</span>
              </button>
              <button
                onClick={() => router.push('/register')}
                className="flex items-center gap-2 px-6 py-3.5 bg-white border border-cream-border rounded-xl font-medium text-navy hover:border-navy hover:shadow-lg transition-all cursor-pointer"
              >
                <span>▶</span> Regarder démo
              </button>
            </div>

            {/* Trust bar */}
            <div className="flex items-center gap-5 animate-fade-up">
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <div className="w-4 h-4 rounded-full bg-green-100 flex items-center justify-center text-green-700">
                  ✓
                </div>
                <span>Conforme RGPD</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <div className="w-4 h-4 rounded-full bg-green-100 flex items-center justify-center text-green-700">
                  ✓
                </div>
                <span>Support 24/7</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <div className="w-4 h-4 rounded-full bg-green-100 flex items-center justify-center text-green-700">
                  ✓
                </div>
                <span>Essai gratuit</span>
              </div>
            </div>
          </div>

          {/* Right: Dashboard mockup */}
          <div className="animate-fade-right">
            <DashboardMockup />
          </div>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="flex justify-center pt-0 pb-0">
        <div className="animate-bounce">
          <svg
            className="w-6 h-6 text-amber"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M7 10l5 5 5-5z" />
          </svg>
        </div>
      </div>

      <style jsx>{`
        @keyframes fade-up {
          from {
            opacity: 0;
            transform: translateY(1rem);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes fade-right {
          from {
            opacity: 0;
            transform: translateX(2.5rem);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .animate-fade-up {
          animation: fade-up 0.6s ease forwards;
        }

        .animate-fade-up:nth-child(2) {
          animation-delay: 0.1s;
        }

        .animate-fade-up:nth-child(3) {
          animation-delay: 0.2s;
        }

        .animate-fade-up:nth-child(4) {
          animation-delay: 0.3s;
        }

        .animate-fade-up:nth-child(5) {
          animation-delay: 0.4s;
        }

        .animate-fade-right {
          animation: fade-right 0.8s 0.3s ease forwards;
        }
      `}</style>
    </section>
  )
}
