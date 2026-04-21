// ──────────────────────────────────────────────────────────────────────────
// Password Strength Calculation
// ──────────────────────────────────────────────────────────────────────────

export interface PasswordStrengthResult {
  score: 0 | 1 | 2 | 3 | 4
  label: string
  color: string
}

export function getPasswordStrength(password: string): PasswordStrengthResult {
  if (!password) {
    return { score: 0, label: '', color: '' }
  }

  let score = 0

  // Criteria
  if (password.length >= 12) score++
  if (password.length >= 16) score++
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++
  if (/[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password)) score++

  // Cap at 4
  score = Math.min(score, 4)

  const config: Record<0 | 1 | 2 | 3 | 4, { label: string; color: string }> = {
    0: { label: '', color: '' },
    1: { label: 'Très faible', color: '#E24B4A' },
    2: { label: 'Faible', color: '#E24B4A' },
    3: { label: 'Fort', color: '#1D9E75' },
    4: { label: 'Très fort', color: '#1D9E75' },
  }

  return {
    score: score as 0 | 1 | 2 | 3 | 4,
    label: config[score as 0 | 1 | 2 | 3 | 4].label,
    color: config[score as 0 | 1 | 2 | 3 | 4].color,
  }
}
