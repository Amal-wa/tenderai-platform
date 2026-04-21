'use client'

interface NpsDonutProps {
  score: number
  label: string
  vsMarket: string
}

export default function NpsDonut({
  score,
  label,
  vsMarket,
}: NpsDonutProps): React.ReactElement {
  const circumference = 2 * Math.PI * 22
  const dashOffset = circumference * (1 - score / 100)

  return (
    <div className="flex items-center gap-4">
      {/* SVG Donut */}
      <svg width="56" height="56" viewBox="0 0 56 56" className="flex-shrink-0">
        {/* Track */}
        <circle
          cx="28"
          cy="28"
          r="22"
          fill="none"
          stroke="var(--cream-2)"
          strokeWidth="6"
        />
        {/* Fill */}
        <circle
          cx="28"
          cy="28"
          r="22"
          fill="none"
          stroke="var(--amber)"
          strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform="rotate(-90 28 28)"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
        {/* Text */}
        <text
          x="28"
          y="32"
          textAnchor="middle"
          fontFamily="var(--font-heading)"
          fontSize="13"
          fontWeight="900"
          fill="var(--navy)"
        >
          +{score}
        </text>
      </svg>

      {/* Right Content */}
      <div className="flex-1">
        <p className="font-heading text-[13px] font-bold text-[var(--success)]">
          {label}
        </p>
        <p className="text-[11px] text-[var(--text-4)] mt-0.5">{vsMarket}</p>

        {/* Sentiment Bars */}
        <div className="flex gap-1 mt-2">
          <div className="w-6 h-1 rounded bg-[var(--success)]" />
          <div className="w-4 h-1 rounded bg-[var(--cream-2)]" />
          <div className="w-3 h-1 rounded bg-[var(--danger)]" />
        </div>

        {/* Labels */}
        <div className="flex gap-2 mt-1 text-[9px] text-[var(--text-4)]">
          <span>Promoteurs</span>
          <span>·</span>
          <span>Neutres</span>
          <span>·</span>
          <span>Détracteurs</span>
        </div>
      </div>
    </div>
  )
}
