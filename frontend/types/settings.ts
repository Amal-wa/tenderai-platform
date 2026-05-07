export interface UserProfileUpdate {
  full_name?: string
  phone?: string
  job_title?: string
  preferred_language?: 'fr' | 'ar' | 'en'
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface ChangePasswordResponse {
  message: string
}

export interface TenantSettings {
  id: string
  name: string
  email: string
  subscription_plan: string
  is_active: boolean
  sector?: string
  country?: string
  org_size?: string
  tenant_metadata: {
    logo_url?: string
    logo_path?: string
    color?: string
    [key: string]: unknown
  }
  created_at: string
  updated_at: string
}

export interface TenantUpdate {
  name?: string
  email?: string
  sector?: string
  country?: string
  tenant_metadata?: Record<string, unknown>
}

export interface APIKey {
  id: string
  name: string
  prefix: string
  permissions: string[]
  expires_at?: string
  last_used_at?: string
  created_at: string
  revoked_at?: string
}

export interface APIKeyCreateRequest {
  name: string
  permissions: string[]
  expires_at?: string
}

export interface APIKeyCreateResponse {
  key: string
  prefix: string
  id: string
  message: string
}

export interface APIKeyRevokeResponse {
  message: string
  key_id: string
  revoked_at: string
}

export interface ActiveSession {
  id: string
  user_id: string
  tenant_id: string
  user_agent?: string
  ip_address?: string
  created_at: string
  expires_at: string
  last_used_at?: string
  revoked_at?: string
  jti?: string
  is_current: boolean
}

export interface SessionRevokeResponse {
  message: string
  session_id: string
  revoked_at: string
}

export interface TOTPSetupResponse {
  qr_code: string
  secret: string
  backup_codes: string[]
  message: string
}

export interface TOTPVerifyRequest {
  code: string
}
