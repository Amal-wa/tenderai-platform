import { useState, useEffect } from 'react'

export function useAnimatedValue(target: number, delay: number = 600) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    const timeout = setTimeout(() => {
      const step = target / (900 / 16)
      const interval = setInterval(() => {
        setValue(prev => {
          const next = prev + step
          if (next >= target) {
            clearInterval(interval)
            return target
          }
          return next
        })
      }, 16)
      return () => clearInterval(interval)
    }, delay)

    return () => clearTimeout(timeout)
  }, [target, delay])

  return Math.round(value)
}
