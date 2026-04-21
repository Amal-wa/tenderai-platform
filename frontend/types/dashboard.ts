/**
 * Dashboard Response Types
 * Mirrors backend schemas: AdminDashboardResponse, UserDashboardResponse
 */

export interface KPIData {
  // Admin KPIs
  active_documents?: number
  avg_compliance_score?: number
  total_documents?: number
  win_rate?: number
  // User KPIs
  my_documents?: number
  my_completed?: number
  my_avg_score?: number
}

export interface StatusDistribution {
  pending: number
  processing: number
  completed: number
  failed: number
}

export interface TeamActivityItem {
  user_id: string // UUID
  full_name: string
  action: string // "session.started", "document.created", etc
  resource_type: string // "user", "document", etc
  resource_id?: string // UUID
  timestamp: string // ISO-8601 datetime
}

export interface DocumentResponse {
  id: string // UUID
  filename: string
  document_type: string
  status: string
  document_metadata?: {
    ref?: string
    sector?: string
    compliance_score?: number
    budget_eur?: number
    deadline?: string
    days_remaining?: number
    status_label?: string
    [key: string]: any
  }
  created_at: string
  updated_at: string
  [key: string]: any
}

export interface NotificationResponse {
  id: string // UUID
  message: string
  type: string// "urgent", "info", "warning"
  is_read: boolean
  created_at: string
}

export interface TenantResponse {
  id: string // UUID
  name: string
  email: string
  subscription_plan: string
  is_active: boolean
  tenant_metadata?: {
    logo_url?: string
    logo_path?: string
    [key: string]: any
  }
  created_at: string
  updated_at: string
}

export interface UserResponse {
  id: string // UUID
  email: string
  full_name: string
  role: string | { name: string }
  is_active: boolean
  totp_enabled: boolean
  tenant_id: string
  tenant_name: string
  subscription_plan: string
  tenant_color?: string
}

export interface AdminDashboardResponse {
  tenant: TenantResponse
  user: UserResponse
  kpis: KPIData
  recent_documents: DocumentResponse[]
  status_distribution: StatusDistribution
  team_activity: TeamActivityItem[]
  notifications: NotificationResponse[]
}

export interface LastAnalysisItem {
  document: DocumentResponse
  report: {
    id: string
    compliance_score: number
    [key: string]: any
  }
}

export interface UserDashboardResponse {
  tenant: TenantResponse
  user: UserResponse
  kpis: KPIData
  my_documents: DocumentResponse[]
  upcoming_deadlines: DocumentResponse[]
  last_analysis?: LastAnalysisItem
  notifications: NotificationResponse[]
}
