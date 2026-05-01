'use client'

import { useAuth } from '@/context/AuthContext'

interface UseAdminAccessReturn {
  isLoading: boolean
  user: any
  isAdmin: boolean
  hasAccess: boolean // true when loading is done AND user is admin
}

/**
 * Hook pour vérifier l'accès admin avec protection contre la race condition.
 * 
 * Usage:
 *   const { isReady, hasAccess } = useAdminAccess()
 *   if (!isReady) return <Spinner />
 *   if (!hasAccess) return <AccessDenied />
 *   // render content
 */
export function useAdminAccess(): UseAdminAccessReturn {
  const { user, ready } = useAuth()

  // Helper pour normaliser le rôle (string, objet, ou null)
  const getRoleName = (role: any): string => {
    if (!role) return ''
    if (typeof role === 'string') return role
    if (role && typeof role === 'object' && role.name) return role.name
    return ''
  }

  const roleName = getRoleName(user?.role)
  const isAdmin = roleName === 'admin' || roleName === 'superadmin'
  
  // hasAccess = true quand l'init est FINI et user est admin
  const hasAccess = !!(ready && user && isAdmin)

  return {
    isLoading: !ready,  // For backward compatibility
    user,
    isAdmin,
    hasAccess,
  }
}
