'use client'

import { useAuth } from '@/context/AuthContext'
import {
  hasPermission,
  hasRole,
  canAccess as canAccessModule,
  ROLES,
  type Permission,
  type Role,
} from '@/lib/permissions'

/**
 * Custom hook to access permission-checking functions bound to the current user's role
 */
export function usePermissions() {
  const { user } = useAuth()
  const role = user?.role ?? null

  return {
    /**
     * Check if user has a specific permission
     */
    can: (permission: string): boolean => hasPermission(
      typeof role === 'string' ? role : role?.name ?? null,
      permission as Permission
    ),

    /**
     * Check if user can access a module (has read permission on module)
     */
    canAccess: (module: string): boolean => canAccessModule(
      typeof role === 'string' ? role : role?.name ?? null,
      module
    ),

    /**
     * Check if user meets minimum role hierarchy level
     */
    hasRole: (requiredRole: string): boolean => hasRole(
      typeof role === 'string' ? role : role?.name ?? null,
      requiredRole as Role
    ),

    /**
     * True if user has admin or superadmin role
     */
    isAdmin: hasRole(
      typeof role === 'string' ? role : role?.name ?? null,
      ROLES.ADMIN
    ),

    /**
     * True if user is superadmin
     */
    isSuperAdmin: (typeof role === 'string' ? role : role?.name) === ROLES.SUPERADMIN,

    /**
     * The current user's role
     */
    role: role || null,
  }
}
