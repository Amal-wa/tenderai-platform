'use client'

import { useState, useEffect } from 'react'

export interface TOTPTimerProps {
  size?: number
  onExpire?: () => void
  compact?: boolean
}

export default function TOTPTimer({
  size = 48,
  onExpire,
  compact = false,
}: TOTPTimerProps): JSX.Element {
  const [timeLeft, setTimeLeft] = useState<number>(() => {
    const now = Math.floor(Date.now() / 1000)
    return 30 - (now % 30)
  })

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        const next = prev - 1
        if (next <= 0) {
          if (onExpire) onExpire()
          return 30 - ((Math.floor(Date.now() / 1000) + 1) % 30)
        }
        return next
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [onExpire])

  const progress = timeLeft / 30
  const circumference = 2 * Math.PI * (size / 2 - 4)
  const offset = circumference * (1 - progress)

  const getColor = () => {
    if (timeLeft <= 5) return '#B83232' // danger
    if (timeLeft <= 10) return '#C4962A' // amber
    return '#1E7C5A' // success
  }

  if (compact) {
    return (
      <div className="text-center">
        <div className="text-xs font-mono text-muted">{timeLeft}s</div>
      </div>
    )
  }

  return (
    <svg width={size} height={size} className="mx-auto" viewBox={`0 0 ${size} ${size}`}>
      {/* Background circle */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={size / 2 - 4}
        fill="none"
        stroke="#E5E0D8"
        strokeWidth="2"
      />
      {/* Progress circle */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={size / 2 - 4}
        fill="none"
        stroke={getColor()}
        strokeWidth="2"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 1s linear, stroke 0.3s ease' }}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      {/* Center text */}
      <text
        x={size / 2}
        y={size / 2}
        textAnchor="middle"
        dominantBaseline="middle"
        className="font-mono font-bold"
        fontSize={size > 60 ? 14 : 12}
        fill={getColor()}
      >
        {timeLeft}s
      </text>
    </svg>
  )
}
