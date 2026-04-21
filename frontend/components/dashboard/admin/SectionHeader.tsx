'use client'

interface SectionHeaderProps {
  label: string
  color: 'amber' | 'green' | 'blue' | 'purple' | 'amber-dark'
}

function getDotColor(color: string): string {
  switch (color) {
    case 'amber':
      return 'bg-[var(--amber)]'
    case 'green':
      return 'bg-[var(--success)]'
    case 'blue':
      return 'bg-[var(--info)]'
    case 'purple':
      return 'bg-[#7F77DD]'
    case 'amber-dark':
      return 'bg-[var(--navy)]'
    default:
      return 'bg-[var(--amber)]'
  }
}

export default function SectionHeader({
  label,
  color,
}: SectionHeaderProps): React.ReactElement {
  const pillBg = color === 'amber-dark' ? 'bg-[var(--amber)] text-[var(--navy)]' : 'bg-[var(--navy)] text-white/70'

  return (
    <div className="flex items-center gap-3 mb-4 mt-6">
      <div
        className={`${pillBg} font-heading text-[10px] font-bold uppercase tracking-widest px-3 py-1.5 rounded-full flex items-center gap-1.5 flex-shrink-0`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${getDotColor(color)}`} />
        {label}
      </div>
      <div className="flex-1 h-px bg-gradient-to-r from-[var(--cream-3)] to-transparent" />
    </div>
  )
}
