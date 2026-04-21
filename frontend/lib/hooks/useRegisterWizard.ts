'use client'

import { useState, useEffect } from 'react'
import { RegisterFormData } from '@/lib/validations/register'

interface WizardState {
  step: 1 | 2 | 3 | 4
  data: Partial<RegisterFormData>
  timestamp: number
}

const STORAGE_KEY = 'tenderai_register_draft'
const DRAFT_VALIDITY_MS = 24 * 60 * 60 * 1000 // 24 hours

export function useRegisterWizard() {
  const [state, setState] = useState<WizardState>({
    step: 1,
    data: {},
    timestamp: Date.now(),
  })

  const [isHydrated, setIsHydrated] = useState(false)

  // Hydrate from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return

    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as WizardState
        const age = Date.now() - parsed.timestamp

        if (age < DRAFT_VALIDITY_MS) {
          setState(parsed)
        } else {
          localStorage.removeItem(STORAGE_KEY)
        }
      }
    } catch {
      // Silently ignore corrupted localStorage
    }

    setIsHydrated(true)
  }, [])

  // Persist to localStorage whenever state changes
  useEffect(() => {
    if (!isHydrated || typeof window === 'undefined') return
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  }, [state, isHydrated])

  const next = () => {
    if (state.step < 4) {
      setState((s) => ({ ...s, step: (s.step + 1) as 1 | 2 | 3 | 4 }))
    }
  }

  const back = () => {
    if (state.step > 1) {
      setState((s) => ({ ...s, step: (s.step - 1) as 1 | 2 | 3 | 4 }))
    }
  }

  const goToStep = (step: 1 | 2 | 3 | 4) => {
    setState((s) => ({ ...s, step }))
  }

  const updateData = (partial: Partial<RegisterFormData>) => {
    setState((s) => ({
      ...s,
      data: { ...s.data, ...partial },
      timestamp: Date.now(),
    }))
  }

  const clearDraft = () => {
    if (typeof window === 'undefined') return
    localStorage.removeItem(STORAGE_KEY)
    setState({
      step: 1,
      data: {},
      timestamp: Date.now(),
    })
  }

  return {
    step: state.step,
    data: state.data,
    next,
    back,
    goToStep,
    updateData,
    clearDraft,
    isHydrated,
  }
}
