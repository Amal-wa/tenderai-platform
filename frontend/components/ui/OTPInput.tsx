'use client'

import { useRef, useCallback, useEffect } from 'react'

interface OTPInputProps {
  value: string
  onChange: (value: string) => void
  onComplete?: (value: string) => void
  error?: boolean
  disabled?: boolean
}

export default function OTPInput({
  value,
  onChange,
  onComplete,
  error,
  disabled,
}: OTPInputProps): JSX.Element {
  const inputRefs = useRef<HTMLInputElement[]>([])
  const mountedRef = useRef(false)

  const registerRef = useCallback(
    (el: HTMLInputElement | null, index: number) => {
      if (el) inputRefs.current[index] = el
    },
    []
  )

  // Guard against onComplete firing on initial render
  useEffect(() => {
    mountedRef.current = true
  }, [])

  const focusNext = (index: number) => {
    const next = inputRefs.current[index + 1]
    if (next) {
      next.focus()
      next.select()
    }
  }

  const focusPrev = (index: number) => {
    const prev = inputRefs.current[index - 1]
    if (prev) {
      prev.focus()
      prev.select()
    }
  }

  const handleChange = (index: number, raw: string) => {
    const digit = raw.replace(/\D/g, '').slice(-1)
    const chars = value.padEnd(6, ' ').split('')
    chars[index] = digit || ' '
    const next = chars.join('')
    onChange(next)

    if (digit) {
      if (index < 5) {
        focusNext(index)
      } else {
        // last digit — trigger complete (only if mounted, not on initial render)
        const full = next.replace(/\s/g, '')
        if (full.length === 6 && mountedRef.current) onComplete?.(full)
      }
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace') {
      e.preventDefault()
      const chars = value.padEnd(6, ' ').split('')
      if (chars[index].trim()) {
        // clear current
        chars[index] = ' '
        onChange(chars.join(''))
      } else {
        // already empty → go back
        if (index > 0) {
          focusPrev(index)
          const prev = [...chars]
          prev[index - 1] = ' '
          onChange(prev.join(''))
        }
      }
    }
    if (e.key === 'ArrowLeft' && index > 0) focusPrev(index)
    if (e.key === 'ArrowRight' && index < 5) focusNext(index)
  }

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    const padded = pasted.padEnd(6, ' ')
    onChange(padded)
    const lastIndex = Math.min(pasted.length, 5)
    inputRefs.current[lastIndex]?.focus()
    if (pasted.length === 6 && mountedRef.current) onComplete?.(pasted)
  }

  const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.select()
  }

  const digits = value.padEnd(6, ' ').split('').slice(0, 6)

  return (
    <div className="flex items-center gap-2 justify-center" role="group" aria-label="Code à 6 chiffres">
      {digits.map((digit, i) => (
        <div key={i} className="flex items-center gap-2">
          {i === 3 && (
            <div className="w-3 h-px bg-cream-border flex-shrink-0" aria-hidden="true" />
          )}
          <input
            ref={(el) => registerRef(el, i)}
            type="text"
            inputMode="numeric"
            pattern="[0-9]"
            maxLength={1}
            value={digit.trim()}
            onChange={(e) => handleChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            onPaste={handlePaste}
            onFocus={handleFocus}
            disabled={disabled}
            aria-label={`Chiffre ${i + 1} sur 6`}
            className={`
              w-12 h-14 text-center text-2xl font-heading font-bold
              rounded-xl border-2 transition-all bg-white text-navy
              focus:outline-none focus:ring-2
              ${
                error
                  ? 'border-danger focus:border-danger focus:ring-danger/30'
                  : 'border-cream-border focus:border-amber focus:ring-amber/30'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
              caret-transparent
            `}
          />
        </div>
      ))}
    </div>
  )
}
