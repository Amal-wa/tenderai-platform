'use client'

import { useAuth } from '@/context/AuthContext'
import {
  hasPermission,
  hasRole,
  canAccess as canAccessModule,
  ROLES,
} from '@/lib/permissions'

/**
 * Custom hook to access permission-checking functions bound to the current user's role
 */
export function usePermissions() {
  const { user } = useAuth()
  const role = user?.role

  return {
    /**
     * Check if user has a specific permission
     */
    can: (permission: string): boolean => hasPermission(role || null, permission as any),

    /**
     * Check if user can access a module (has read permission on module)
     */
    canAccess: (module: string): boolean => canAccessModule(role || null, module),

    /**
     * Check if user meets minimum role hierarchy level
     */
    hasRole: (requiredRole: string): boolean => hasRole(role || null, requiredRole as any),

    /**
     * True if user has admin or superadmin role
     */
    isAdmin: hasRole(role || null, ROLES.ADMIN),

    /**
     * True if user is superadmin
     */
    isSuperAdmin: role === ROLES.SUPERADMIN,

    /**
     * The current user's role
     */
    role: role || null,
  }
}
