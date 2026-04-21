/**
 * Role hierarchy: superadmin > admin > manager > analyst > contributor > viewer
 */
export const ROLES = {
  SUPERADMIN: 'superadmin',
  ADMIN: 'admin',
  MANAGER: 'manager',
  ANALYST: 'analyst',
  CONTRIBUTOR: 'contributor',
  VIEWER: 'viewer',
} as const

/**
 * All available permissions in the system (module:action format)
 */
export const PERMISSIONS = {
  DOCUMENTS_READ: 'documents:read',
  DOCUMENTS_WRITE: 'documents:write',
  DOCUMENTS_DELETE: 'documents:delete',
  USERS_READ: 'users:read',
  USERS_WRITE: 'users:write',
  USERS_DELETE: 'users:delete',
  TENANTS_READ: 'tenants:read',
  TENANTS_WRITE: 'tenants:write',
  REPORTS_READ: 'reports:read',
  REPORTS_WRITE: 'reports:write',
  AUDIT_READ: 'audit:read',
  ADMIN_ACCESS: 'admin:access',
  ADMIN_USERS: 'admin:users',
  ADMIN_SETTINGS: 'admin:settings',
} as const

type Role = (typeof ROLES)[keyof typeof ROLES]
type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS]

/**
 * Role-to-permissions mapping
 */
export const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  [ROLES.SUPERADMIN]: Object.values(PERMISSIONS),
  [ROLES.ADMIN]: [
    PERMISSIONS.DOCUMENTS_READ,
    PERMISSIONS.DOCUMENTS_WRITE,
    PERMISSIONS.DOCUMENTS_DELETE,
    PERMISSIONS.USERS_READ,
    PERMISSIONS.USERS_WRITE,
    PERMISSIONS.USERS_DELETE,
    PERMISSIONS.TENANTS_READ,
    PERMISSIONS.TENANTS_WRITE,
    PERMISSIONS.REPORTS_READ,
    PERMISSIONS.REPORTS_WRITE,
    PERMISSIONS.AUDIT_READ,
    PERMISSIONS.ADMIN_ACCESS,
    PERMISSIONS.ADMIN_USERS,
    // NOTE: admin:settings excluded for admin role
  ],
  [ROLES.MANAGER]: [
    PERMISSIONS.DOCUMENTS_READ,
    PERMISSIONS.DOCUMENTS_WRITE,
    PERMISSIONS.DOCUMENTS_DELETE,
    PERMISSIONS.USERS_READ,
    PERMISSIONS.REPORTS_READ,
    PERMISSIONS.REPORTS_WRITE,
    PERMISSIONS.AUDIT_READ,
  ],
  [ROLES.ANALYST]: [
    PERMISSIONS.DOCUMENTS_READ,
    PERMISSIONS.DOCUMENTS_WRITE,
    PERMISSIONS.REPORTS_READ,
  ],
  [ROLES.CONTRIBUTOR]: [PERMISSIONS.DOCUMENTS_READ, PERMISSIONS.DOCUMENTS_WRITE],
  [ROLES.VIEWER]: [PERMISSIONS.DOCUMENTS_READ, PERMISSIONS.REPORTS_READ],
}

/**
 * Check if a user with the given role has a specific permission
 * @param {string} userRole - The user's role (e.g., 'admin', 'viewer')
 * @param {string} permission - The permission to check (e.g., 'documents:read')
 * @returns {boolean} True if the user has the permission
 */
export function hasPermission(userRole: string | null, permission: Permission): boolean {
  if (!userRole) return false
  const permissions = ROLE_PERMISSIONS[userRole as Role] || []
  return permissions.includes(permission)
}

/**
 * Check if a user's role meets the minimum required role (hierarchy-based)
 * @param {string} userRole - The user's role
 * @param {string} requiredRole - The minimum required role
 * @returns {boolean} True if user role >= required role in hierarchy
 */
export function hasRole(userRole: string | null, requiredRole: Role): boolean {
  if (!userRole || !requiredRole) return false
  const roleHierarchy: Role[] = [
    ROLES.VIEWER,
    ROLES.CONTRIBUTOR,
    ROLES.ANALYST,
    ROLES.MANAGER,
    ROLES.ADMIN,
    ROLES.SUPERADMIN,
  ]
  const userIndex = roleHierarchy.indexOf(userRole as Role)
  const requiredIndex = roleHierarchy.indexOf(requiredRole)
  return userIndex >= requiredIndex
}

/**
 * Check if a user has at least one of the specified permissions
 * @param {string} userRole - The user's role
 * @param {string[]} permissions - Array of permissions to check
 * @returns {boolean} True if user has any of the listed permissions
 */
export function hasAnyPermission(
  userRole: string | null,
  permissions: Permission[] = []
): boolean {
  if (!userRole || !Array.isArray(permissions) || permissions.length === 0) {
    return false
  }
  return permissions.some((permission) => hasPermission(userRole, permission as Permission))
}

/**
 * Check if a user has all of the specified permissions
 * @param {string} userRole - The user's role
 * @param {string[]} permissions - Array of permissions to check
 * @returns {boolean} True if user has all of the listed permissions
 */
export function hasAllPermissions(
  userRole: string | null,
  permissions: Permission[] = []
): boolean {
  if (!userRole || !Array.isArray(permissions) || permissions.length === 0) {
    return false
  }
  return permissions.every((permission) => hasPermission(userRole, permission as Permission))
}

/**
 * Shorthand: Check if user can access a module (has at least read permission)
 * @param {string} userRole - The user's role
 * @param {string} module - The module name (documents|users|tenants|reports|audit|admin)
 * @returns {boolean} True if user has read access to the module
 */
export function canAccess(userRole: string | null, module: string): boolean {
  if (!userRole || !module) return false
  const readPermission = `${module}:read` as Permission
  return hasPermission(userRole, readPermission)
}
