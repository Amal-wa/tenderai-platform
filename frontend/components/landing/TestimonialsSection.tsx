'use client'

import { motion } from 'framer-motion'
import { Star } from 'lucide-react'

interface TestimonialData {
  quote: string
  author: string
  role: string
  company: string
  sector: string
  initials: string
  avatarBg: string
  avatarText: string
  featured?: boolean
}

interface TestimonialCardProps extends TestimonialData {
  index: number
}

function TestimonialCard({
  quote,
  author,
  role,
  company,
  sector,
  initials,
  avatarBg,
  avatarText,
  featured = false,
  index,
}: TestimonialCardProps) {
  return (
    <motion.div
      whileInView={{ opacity: 1, y: 0 }}
      initial={{ opacity: 0, y: 20 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1 }}
      className={`rounded-2xl p-8 flex flex-col
        ${
          featured
            ? 'bg-[#13203A] border-2 border-[#C4962A]'
            : 'bg-cream border border-cream-border'
        }
        hover:shadow-lg transition-all duration-300`}
    >
      {/* Stars */}
      <div className="flex gap-1 mb-5">
        {[...Array(5)].map((_, j) => (
          <Star
            key={j}
            className="w-4 h-4 fill-amber text-amber"
          />
        ))}
      </div>
      {/* Quote */}
      <p
        className={`text-sm leading-relaxed flex-1 mb-6
          ${featured ? 'text-white/80' : 'text-muted'}`}
      >
        "{quote}"
      </p>
      {/* Author */}
      <div className="flex items-center gap-3">
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm
            ${avatarBg} ${avatarText}`}
        >
          {initials}
        </div>
        <div>
          <p
            className={`font-semibold text-sm
              ${featured ? 'text-white' : 'text-navy'}`}
          >
            {author}
          </p>
          <p
            className={`text-xs
              ${featured ? 'text-white/50' : 'text-muted'}`}
          >
            {role} · {company}
          </p>
        </div>
      </div>
      {/* Sector tag */}
      <div
        className={`mt-4 pt-4 border-t
          ${featured ? 'border-white/10' : 'border-cream-border'}`}
      >
        <span
          className={`text-xs font-medium px-3 py-1 rounded-full
            ${
              featured
                ? 'bg-amber/10 text-amber'
                : 'bg-white border border-cream-border text-muted'
            }`}
        >
          {sector}
        </span>
      </div>
    </motion.div>
  )
}

export default function TestimonialsSection(): JSX.Element {
  const testimonials: TestimonialData[] = [
    {
      quote:
        'TenderAI a transformé notre manière d\'analyser les appels. 90% d\'économie de temps!',
      author: 'Amira Ben Salah',
      role: 'Dir. Marchés publics',
      company: 'STEG',
      sector: 'Énergie',
      initials: 'AB',
      avatarBg: 'bg-[#13203A]',
      avatarText: 'text-amber',
      featured: false,
    },
    {
      quote:
        'Nous avons remporté 3 appels supplémentaires grâce aux analyses de conformité.',
      author: 'Mohamed Khaled',
      role: 'Responsable Soumissions',
      company: 'Tunisie Telecom',
      sector: 'Télécom',
      initials: 'MK',
      avatarBg: 'bg-emerald-600',
      avatarText: 'text-white',
      featured: true,
    },
    {
      quote:
        'La sécurité des données et le support sont au-dessus de nos attentes.',
      author: 'Fatima Zahra',
      role: 'Responsable IT',
      company: 'Groupe Poulina',
      sector: 'IT',
      initials: 'FZ',
      avatarBg: 'bg-purple-600',
      avatarText: 'text-white',
      featured: false,
    },
  ]

  return (
    <section className="bg-white py-24 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-14">
          <p className="text-xs font-bold text-amber uppercase tracking-[0.14em] mb-3">
            TÉMOIGNAGES
          </p>
          <h2 className="text-4xl font-bold text-navy tracking-tight">
            Ce que disent nos clients
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {testimonials.map((t, i) => (
            <TestimonialCard key={t.author} {...t} index={i} />
          ))}
        </div>
      </div>
    </section>
  )
}
