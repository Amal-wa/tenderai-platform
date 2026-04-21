'use client'

import { useRouter } from 'next/navigation'

export default function CtaSection(): JSX.Element {
  const router = useRouter()

  return (
    <section className="bg-[#0d1b2e] py-20 px-12 text-center">
      <div className="max-w-2xl mx-auto">
        <h2 className="font-heading text-4xl font-bold text-white leading-tight mb-4">
          Prêt à transformer vos <br />
          appels d'
          <span className="text-amber-light">offres</span>&nbsp;?
        </h2>

        <p className="text-lg text-white/60 mx-auto mb-8 leading-relaxed">
          Rejoignez les équipes qui gagnent du temps et remportent plus de marchés
          publics grâce à l'intelligence artificielle.
        </p>

        <div className="flex gap-4 justify-center flex-wrap">
          <button
            onClick={() => router.push('/register')}
            className="px-9 py-4 bg-amber text-white rounded-xl font-heading text-base font-semibold hover:bg-amber-light transition-colors cursor-pointer"
          >
            Essayer gratuitement
          </button>
          <button
            onClick={() => router.push('/contact')}
            className="px-9 py-4 bg-transparent border border-white/25 text-white rounded-xl font-medium hover:border-white/50 hover:text-white transition-all cursor-pointer"
          >
            Planifier une démo
          </button>
        </div>
      </div>
    </section>
  )
}
