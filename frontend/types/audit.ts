/**
 * Audit Log Types
 * Mirrors backend AuditLog model
 */

export type AuditAction = 
  | 'login'
  | 'logout'
  | 'login_failed'
  | 'create'
  | 'read'
  | 'update'
  | 'delete'

export type AuditResourceType =
  | 'user'
  | 'role'
  | 'document'
  | 'chunk'
  | 'compliance_report'
  | 'tenant'
  | 'auth_session'

export type AuditStatus = 'success' | 'failure'

export interface AuditLogEntry {
  id: number
  tenant_id: string
  user_id: string | null
  action: AuditAction
  resource_type: AuditResourceType
  resource_id: string | null
  old_value: Record<string, any> | null
  new_value: Record<string, any> | null
  status: AuditStatus
  reason: string | null
  ip_address: string | null
  user_agent: string | null
  timestamp: string
  hash: string
  previous_hash: string | null
  user_email: string | null
  user_name: string | null
}

export interface AuditLogsResponse {
  total: number
  page: number
  size: number
  items: AuditLogEntry[]
}
