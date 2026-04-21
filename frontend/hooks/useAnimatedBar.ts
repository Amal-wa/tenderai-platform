import { useState, useEffect } from 'react'

export function useAnimatedBar(width: number, delay: number = 700) {
  const [w, setW] = useState(0)

  useEffect(() => {
    const t = setTimeout(() => setW(width), delay)
    return () => clearTimeout(t)
  }, [width, delay])

  return w
}
