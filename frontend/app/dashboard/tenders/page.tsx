import TendersClient from './TendersClient'

/**
 * Page server component for /dashboard/tenders
 * Delegates all rendering to TendersClient (use client)
 */
export default function TendersPage() {
  return <TendersClient />
}
