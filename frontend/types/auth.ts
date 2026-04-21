// =============================================================================
// types/auth.ts — Type definitions for authentication flow
// =============================================================================

export interface UserProfile {
  id: string
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

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  requires_2fa: boolean
  partial_token?: string  // Present if requires_2fa === true
  [key: string]: unknown
}

export interface Verify2FARequest {
  totp_code?: string
  backup_code?: string
}

export interface Verify2FAResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface TOTPSetupResponse {
  qr_code: string
  secret: string
  backup_codes: string[]
  message: string
}

export interface TOTPVerifyResponse {
  message: string
  is_enabled: boolean
}

export interface TOTPDisableRequest {
  password: string
}

export interface TOTPDisableResponse {
  message: string
}

export interface ErrorResponse {
  detail?: string
  message?: string
  code?: string
  [key: string]: unknown
}

export interface AuthContextType {
  user: UserProfile | null
  tenant: {
    id: string
    name: string
    plan: string
    color: string
  } | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  finalizeLogin: (redirect?: string | null) => Promise<void>
  loading: boolean
  error: string | null
  setError: (error: string | null) => void
  ready: boolean
  updateUserProfile: (updates: Partial<UserProfile>) => void
}
