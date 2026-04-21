/**
 * 🔐 AUDIT LOG TYPES — Shape exact du backend
 *
 * Source: app/models/audit_log.py + app/schemas.py (AuditLogResponse)
 * Endpoint: GET /api/v1/{tenant_id}/audit
 * Response: PaginatedResponse<AuditLogResponse>
 */

/**
 * Single audit log entry
 *
 * ✅ Immutable append-only log
 * ✅ Hash chain for integrity verification
 * ✅ Before/after JSONB for diffs
 * ✅ User info joined from users table
 */
export interface AuditLogEntry {
  // Identifiers
  id: number;                         // BigInteger (sequential, immutable)
  tenant_id: string;                  // UUID
  user_id: string | null;             // UUID or null (system-triggered actions)

  // Action Details
  action: string;                     // "create" | "update" | "delete" | "login" | "logout" | "refresh" | "setup" | "verify" | "disable"
  resource_type: string;              // "user" | "role" | "document" | "audit_session" | "api_key" | "totp_device" | "compliance_report"
  resource_id: string | null;         // UUID of affected resource (null for system actions)

  // State Before/After (for diffs)
  old_value: Record<string, any> | null;    // Pre-modification state (UPDATE/DELETE)
  new_value: Record<string, any> | null;    // Post-modification state (CREATE/UPDATE)

  // Outcome
  status: "success" | "failure";      // Operation outcome
  reason: string | null;              // Error message if status="failure"

  // Security Context
  ip_address: string | null;          // IPv4 or IPv6 address
  user_agent: string | null;          // Device/browser identification

  // Timing (timezone-aware ISO-8601)
  timestamp: string;                  // e.g., "2025-01-15T10:32:47.123456+00:00"

  // Hash Chain (Integrity)
  hash: string | null;                // SHA-256 of this entry + previous_hash
  previous_hash: string | null;       // SHA-256 of prior entry (chain link)

  // User Info (joined from users table)
  user_email: string | null;          // Email of user who triggered action (null if system)
  user_name: string | null;           // "{first_name} {last_name}" (null if system)
}

/**
 * Paginated response from list_audit_logs()
 *
 * Endpoint: GET /api/v1/{tenant_id}/audit
 * Query params: ?page=1&page_size=20&resource_type=&action=
 *
 * Example response:
 * ```json
 * {
 *   "items": [
 *     {
 *       "id": 1050,
 *       "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
 *       "user_id": "user-uuid",
 *       "action": "create",
 *       "resource_type": "document",
 *       "resource_id": "doc-uuid",
 *       "old_value": null,
 *       "new_value": { "title": "Q1 Budget", "status": "draft" },
 *       "status": "success",
 *       "reason": null,
 *       "ip_address": "192.0.2.100",
 *       "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
 *       "timestamp": "2025-01-15T10:32:47.123456+00:00",
 *       "hash": "f7d3e9c2...",
 *       "previous_hash": "e6c2d8b1..."
 *     }
 *   ],
 *   "total": 247,
 *   "page": 1,
 *   "page_size": 20,
 *   "pages": 13
 * }
 * ```
 */
export interface AuditLogPaginatedResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

/**
 * API request params for GET /api/v1/{tenant_id}/audit
 *
 * All optional (filters)
 */
export interface AuditLogFilters {
  page?: number;                      // Default: 1 (1-indexed)
  page_size?: number;                 // Default: 20, Max: 100
  resource_type?: string;             // e.g., "document", "user", "api_key"
  action?: string;                    // e.g., "create", "delete", "login"
}

/**
 * Audit log status enum
 */
export type AuditLogStatus = "success" | "failure";

/**
 * Audit action enum (common types)
 *
 * From backend logs:
 * - Authentication: "login", "logout", "login_failed", "refresh"
 * - Security: "security_alert", "verify" (2FA), "setup" (2FA), "disable" (2FA)
 * - CRUD: "create", "update", "delete", "read"
 * - Special: "role.admin_assigned"
 */
export type AuditAction =
  | "login"
  | "logout"
  | "login_failed"
  | "refresh"
  | "security_alert"
  | "verify"
  | "setup"
  | "disable"
  | "create"
  | "update"
  | "delete"
  | "read"
  | "role.admin_assigned"
  | "CREATE"  // API keys
  | "DELETE"  // API keys
  | string;   // Fallback for custom actions

/**
 * Resource type enum (what was affected)
 */
export type AuditResourceType =
  | "user"
  | "role"
  | "document"
  | "api_key"
  | "totp_device"
  | "compliance_report"
  | "tenant"
  | "auth_session"
  | string;   // Fallback

/**
 * Helper: Parse ISO timestamp to Date
 */
export function parseAuditTimestamp(timestamp: string): Date {
  return new Date(timestamp);
}

/**
 * Helper: Format Date to locale string
 */
export function formatAuditTimestamp(timestamp: string, locale: string = "en-US"): string {
  return parseAuditTimestamp(timestamp).toLocaleString(locale);
}

/**
 * Helper: Get display label for action
 */
export function getActionLabel(action: AuditAction): string {
  const labels: Record<string, string> = {
    login: "Login",
    logout: "Logout",
    login_failed: "Failed Login",
    refresh: "Token Refresh",
    security_alert: "Security Alert",
    verify: "2FA Verify",
    setup: "2FA Setup",
    disable: "2FA Disable",
    create: "Create",
    update: "Update",
    delete: "Delete",
    read: "Read",
    "role.admin_assigned": "Admin Assigned",
    CREATE: "Create",
    DELETE: "Delete",
  };
  return labels[action] || action;
}

/**
 * Helper: Get display label for resource type
 */
export function getResourceTypeLabel(resourceType: AuditResourceType): string {
  const labels: Record<string, string> = {
    user: "User",
    role: "Role",
    document: "Document",
    api_key: "API Key",
    totp_device: "2FA Device",
    compliance_report: "Compliance Report",
    tenant: "Tenant",
    auth_session: "Session",
  };
  return labels[resourceType] || resourceType;
}

/**
 * Helper: Get status color for UI
 */
export function getStatusColor(status: AuditLogStatus): "success" | "destructive" {
  return status === "success" ? "success" : "destructive";
}

/**
 * Helper: Format before/after diffs
 *
 * Example:
 * old = { first_name: "Alice", role: "viewer" }
 * new = { first_name: "Alice", role: "admin" }
 * → [{ field: "role", old: "viewer", new: "admin" }]
 */
export interface DiffField {
  field: string;
  old: any;
  new: any;
}

export function diffOldNewValues(
  oldValue: Record<string, any> | null,
  newValue: Record<string, any> | null
): DiffField[] {
  const diffs: DiffField[] = [];

  if (!oldValue && !newValue) return diffs;

  const old = oldValue || {};
  const new_ = newValue || {};
  const allKeys = new Set([...Object.keys(old), ...Object.keys(new_)]);

  allKeys.forEach((key) => {
    const oldVal = old[key];
    const newVal = new_[key];
    if (oldVal !== newVal) {
      diffs.push({ field: key, old: oldVal, new: newVal });
    }
  });

  return diffs;
}
