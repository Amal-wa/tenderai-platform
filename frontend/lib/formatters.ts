/**
 * lib/formatters.ts — Utility functions for formatting display values
 * Supports Arabic and French locales for TenderAI
 */

/**
 * Format currency in Tunisian Dinars (TND)
 * @param value - amount in TND
 * @param locale - 'fr-TN' or 'ar-TN'
 * @returns formatted string "1 200 TND" or "1.200,50 TND"
 */
export function formatTND(value: number | null | undefined, locale: string = 'fr-TN'): string {
  if (value === null || value === undefined) return '—'
  
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'TND',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value)
}

/**
 * Format percentage value
 * @param value - 0-100 or null
 * @returns formatted string "87%" or "—"
 */
export function formatPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return `${Math.round(value)}%`
}

/**
 * Format file size (bytes to human readable)
 * @param bytes - size in bytes
 * @returns formatted string "1.5 MB" or "—"
 */
export function formatStorage(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined) return '—'
  
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

/**
 * Format relative time (e.g., "il y a 2 heures")
 * @param dateString - ISO 8601 date string
 * @returns relative time or locale date
 */
export function timeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (seconds < 60) return "à l'instant"
  if (seconds < 3600) return `il y a ${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `il y a ${Math.floor(seconds / 3600)}h`
  if (seconds < 604800) return `il y a ${Math.floor(seconds / 86400)}j`
  return date.toLocaleDateString('fr-FR')
}

/**
 * Format date as "JJ MMM YYYY" (e.g., "14 avr. 2026")
 * @param dateString - ISO 8601 date string
 * @returns formatted date or "—"
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '—'
  
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return '—'
  }
}

/**
 * Calculate days remaining until deadline
 * @param deadline - ISO 8601 date string
 * @returns number of days remaining or null if in past
 */
export function daysRemaining(deadline: string | null | undefined): number | null {
  if (!deadline) return null
  
  try {
    const deadlineDate = new Date(deadline)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    deadlineDate.setHours(0, 0, 0, 0)
    
    const days = Math.ceil((deadlineDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
    return days >= 0 ? days : null
  } catch {
    return null
  }
}
