import { v4 as uuidv4 } from 'uuid'
import api from '@/lib/api'
import type {
  UserProfileUpdate,
  ChangePasswordRequest,
  ChangePasswordResponse,
  TenantSettings,
  TenantUpdate,
  APIKey,
  APIKeyCreateRequest,
  APIKeyCreateResponse,
  APIKeyRevokeResponse,
  ActiveSession,
  SessionRevokeResponse,
  TOTPSetupResponse,
  TOTPVerifyRequest,
  TOTPDisableRequest,
} from '@/types/settings'

export function useSettings() {
  return {
    // Profile
    updateProfile: (data: UserProfileUpdate) => 
      api.patch('/api/v1/auth/me', data),

    // Password
    changePassword: (data: ChangePasswordRequest) => 
      api.post<ChangePasswordResponse>('/api/v1/auth/change-password', data),

    // Tenant
    getTenantSettings: () => 
      api.get<TenantSettings>('/api/v1/me/tenant'),
    
    updateTenantSettings: (data: TenantUpdate) => 
      api.patch<TenantSettings>('/api/v1/me/tenant', data),
    
    uploadTenantLogo: (file: File) => {
      const form = new FormData()
      form.append('file', file)
      return api.post('/api/v1/me/tenant/logo', form, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Idempotency-Key': uuidv4(),
        },
      })
    },

    // API Keys
    listApiKeys: () => 
      api.get<APIKey[]>('/api/v1/api-keys'),
    
    createApiKey: (data: APIKeyCreateRequest) => 
      api.post<APIKeyCreateResponse>('/api/v1/api-keys', data),
    
    revokeApiKey: (keyId: string) => 
      api.delete<APIKeyRevokeResponse>(`/api/v1/api-keys/${keyId}`),

    // Sessions
    listSessions: () => 
      api.get<ActiveSession[]>('/api/v1/auth/sessions'),
    
    revokeSession: (sessionId: string) => 
      api.delete<SessionRevokeResponse>(`/api/v1/auth/sessions/${sessionId}`),

    // 2FA
    setupTotp: () => 
      api.post<TOTPSetupResponse>('/api/v1/auth/2fa/setup'),
    
    verifyTotp: (data: TOTPVerifyRequest) => 
      api.post('/api/v1/auth/2fa/verify', data),
    
    disableTotp: (data: TOTPDisableRequest) => 
      api.post('/api/v1/auth/2fa/disable', data),
  }
}
