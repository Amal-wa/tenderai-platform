export default function LogosBar(): JSX.Element {
  const logos = [
    'MINISTÈRE DÉFENSE',
    'TUNISIE DIRECTE',
    'IGI GLOBAL',
    'SFAX INDUSTRIES',
    'TECH TUNISIA',
    'STEG',
    'OTC',
    'CNAM',
  ]

  const trustStats = [
    { value: '120+', label: 'équipes actives' },
    { value: '4.9/5', label: 'satisfaction client' },
    { value: '48h', label: 'déploiement moyen' },
    { value: 'SOC2 · ISO 27001', label: 'certifications' },
  ]

  return (
    <div className="bg-white border-y border-cream-border py-10 px-6">
      <div className="max-w-7xl mx-auto">
        <p className="text-center text-xs font-semibold text-muted uppercase tracking-[0.14em] mb-8">
          Utilisé par des équipes en Tunisie et au Maghreb
        </p>
        <div className="flex flex-wrap justify-center items-center gap-4 mb-8">
          {logos.map((logo) => (
            <div
              key={logo}
              className="px-6 py-2.5 border border-cream-border rounded-lg text-xs font-bold text-muted tracking-wide bg-cream hover:border-amber hover:text-navy transition-all duration-200 cursor-default"
            >
              {logo}
            </div>
          ))}
        </div>
        {/* Trust stats row */}
        <div className="flex flex-wrap justify-center gap-8 pt-6 border-t border-cream-border">
          {trustStats.map((item) => (
            <div key={item.label} className="text-center">
              <p className="text-base font-bold text-navy">{item.value}</p>
              <p className="text-xs text-muted mt-0.5">{item.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
