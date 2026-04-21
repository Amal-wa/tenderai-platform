'use client'

import React from 'react'

export interface TenderAILogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg'
  theme?: 'light' | 'dark'
  showText?: boolean
  className?: string
}

const sizeMap = {
  xs: 20,
  sm: 28,
  md: 36,
  lg: 52,
}

const sizeTextMap = {
  xs: '12px',
  sm: '14px',
  md: '16px',
  lg: '20px',
}

export default function TenderAILogo({
  size = 'md',
  theme = 'light',
  showText = true,
  className = '',
}: TenderAILogoProps): JSX.Element {
  const pxSize = sizeMap[size]
  const textSize = sizeTextMap[size]
  const textColor = theme === 'dark' ? '#FFFFFF' : '#0F1B35'

  const clipPathId = `doc-clip-${Math.random().toString(36).slice(2, 9)}`

  return (
    <div
      className={`logo-wrap inline-flex items-center gap-2 cursor-pointer select-none hover:opacity-80 transition-opacity ${className}`}
      style={
        {
          '--r': '13px',
        } as React.CSSProperties
      }
    >
      <svg
        className="logo-svg flex-shrink-0"
        viewBox="0 0 32 32"
        xmlns="http://www.w3.org/2000/svg"
        width={pxSize}
        height={pxSize}
      >
        <defs>
          <clipPath id={clipPathId}>
            <rect x="4" y="2" width="18" height="24" rx="2" />
          </clipPath>
        </defs>

        {/* Dashed amber orbit ring */}
        <circle
          cx="16"
          cy="16"
          r="13"
          fill="none"
          stroke="#C4962A"
          strokeWidth="0.6"
          strokeDasharray="2 3"
          opacity="0.35"
        />

        {/* Document body */}
        <rect x="4" y="2" width="18" height="24" rx="2" fill="#0F1B35" />
        <rect
          x="4"
          y="2"
          width="18"
          height="24"
          rx="2"
          fill="none"
          stroke="#C4962A"
          strokeWidth="1"
        />

        {/* Fold corner amber triangle */}
        <path d="M16 2 L22 8 L16 8 Z" fill="#C4962A" opacity="0.55" />
        <line x1="16" y1="2" x2="22" y2="8" stroke="#0F1B35" strokeWidth="0.6" />

        {/* Text lines */}
        <rect x="7" y="11" width="7" height="1.2" rx="0.6" fill="#C4962A" opacity="0.9" />
        <rect
          x="7"
          y="14"
          width="11"
          height="1"
          rx="0.5"
          fill="rgba(255,255,255,0.35)"
        />
        <rect
          x="7"
          y="17"
          width="9"
          height="1"
          rx="0.5"
          fill="rgba(255,255,255,0.28)"
        />
        <rect
          x="7"
          y="20"
          width="8"
          height="1"
          rx="0.5"
          fill="rgba(255,255,255,0.2)"
        />

        {/* Scan line with clipPath */}
        <g clipPath={`url(#${clipPathId})`}>
          <rect
            className="scan-doc"
            x="4"
            y="9"
            width="18"
            height="1"
            fill="#C4962A"
            opacity="0.6"
          />
        </g>

        {/* Lock group with orbit animation on hover */}
        <g className="lock-group" style={{ transformOrigin: '16px 16px' }}>
          <rect
            x="23"
            y="23"
            width="5.5"
            height="4.5"
            rx="1"
            fill="#0F1B35"
            stroke="#C4962A"
            strokeWidth="0.9"
          />
          <path
            d="M24.2 23 Q24.2 21 25.75 21 Q27.3 21 27.3 23"
            fill="none"
            stroke="#C4962A"
            strokeWidth="0.9"
            strokeLinecap="round"
          />
          <circle className="lock-dot" cx="25.75" cy="25.1" r="0.75" fill="#C4962A" />
        </g>
      </svg>

      {showText && (
        <span
          className="logo-text font-heading font-semibold whitespace-nowrap"
          style={{
            fontSize: textSize,
            color: textColor,
            letterSpacing: '0.01em',
            lineHeight: '1',
          }}
        >
          Tender<em style={{ fontStyle: 'normal', color: '#C4962A' }}>AI</em>
        </span>
      )}

      <style jsx>{`
        @keyframes scan-doc {
          0% {
            transform: translateY(0px);
            opacity: 0;
          }
          10% {
            opacity: 0.9;
          }
          90% {
            opacity: 0.9;
          }
          100% {
            transform: translateY(20px);
            opacity: 0;
          }
        }

        .scan-doc {
          animation: scan-doc 2.4s ease-in-out infinite;
        }

        @keyframes lock-idle {
          0%,
          100% {
            opacity: 1;
          }
          50% {
            opacity: 0.6;
          }
        }

        .lock-dot {
          animation: lock-idle 2s ease-in-out infinite;
        }

        @keyframes orbit-anim {
          from {
            transform: rotate(0deg) translateX(var(--r)) rotate(0deg);
          }
          to {
            transform: rotate(360deg) translateX(var(--r)) rotate(-360deg);
          }
        }

        .logo-wrap:hover .lock-group {
          animation: orbit-anim 2.2s linear infinite;
          transform-origin: 16px 16px;
        }
      `}</style>
    </div>
  )
}
