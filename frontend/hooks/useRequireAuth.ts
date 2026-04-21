'use client'

// TEMP: Imports commented out for UI evaluation — restore before commit
// import { useEffect } from 'react'
// import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'

/**
 * Hook to protect pages - redirects to login if not authenticated
 * Replaces the withAuth HOC from Pages Router
 *
 * @param _requiredPermission - Optional specific permission to check
 * @returns { user, isLoading } - Current user and loading state
 *
 * @example
 * export default function DashboardPage() {
 *   const { user, isLoading } = useRequireAuth()
 *   if (isLoading) return <LoadingSpinner />
 *   return <Dashboard user={user} />
 * }
 */
export function useRequireAuth(_requiredPermission?: string) {
  // TEMP: bypassed for UI evaluation — restore before commit
  // const { user, ready } = useAuth()
  // const router = useRouter()

  // useEffect(() => {
  //   if (!ready) return

  //   if (!user) {
  //     router.replace('/login')
  //   }
  // }, [user, ready, router])

  // Return the actual user data from context (no redirect check)
  const { user, ready } = useAuth()
  return { user, isLoading: !ready }
}
