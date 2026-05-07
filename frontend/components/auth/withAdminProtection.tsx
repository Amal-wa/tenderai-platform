'use client'

import { useAuth } from '@/context/AuthContext'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

/**
 * HOC pour protéger les pages admin
 * Vérifie que l'utilisateur est admin ou superadmin
 */
export function withAdminProtection<P extends object>(
  Component: React.ComponentType<P>
) {
  return function ProtectedComponent(props: P) {
    const { user, isLoading } = useAuth()
    const router = useRouter()

    useEffect(() => {
      if (!isLoading && user) {
        const userRole = typeof user.role === 'string' ? user.role : user.role?.name
        const isAdmin = userRole === 'admin' || userRole === 'superadmin' || userRole === 'system_admin'

        if (!isAdmin) {
          router.replace('/dashboard')
        }
      }
    }, [user, isLoading, router])

    if (isLoading) {
      return (
        <div className="flex-1 flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600 mb-4"></div>
            <p className="text-gray-600 text-sm">Vérification des permissions...</p>
          </div>
        </div>
      )
    }

    const userRole = typeof user?.role === 'string' ? user.role : user?.role?.name
    const isAdmin = userRole === 'admin' || userRole === 'superadmin' || userRole === 'system_admin'

    if (!isAdmin) {
      return (
        <div className="flex-1 flex items-center justify-center bg-gray-50">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md text-center">
            <p className="font-semibold text-red-900 mb-2">Accès refusé</p>
            <p className="text-sm text-red-800">Seuls les administrateurs peuvent accéder à cette page.</p>
          </div>
        </div>
      )
    }

    return <Component {...props} />
  }
}
