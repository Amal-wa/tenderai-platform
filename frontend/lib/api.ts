// =============================================================================
// lib/api.ts — Client HTTP connecté aux routes backend réelles (TypeScript)
//
// ROUTES UTILISÉES :
//   ├─ AUTH
//   │  ├─ POST /api/v1/auth/login          → authentification
//   │  ├─ POST /api/v1/auth/refresh        → renouveler token
//   │  ├─ POST /api/v1/auth/logout         → déconnexion
//   │  ├─ POST /api/v1/auth/register       → inscription
//   │  └─ GET  /api/v1/auth/me             → profil enrichi
//   ├─ DOCUMENTS
//   │  ├─ GET  /api/v1/me/documents        → liste documents
//   │  ├─ GET  /api/v1/me/documents/stats  → stats dashboard
//   │  ├─ GET  /api/v1/me/documents/:id    → détail document
//   │  ├─ POST /api/v1/me/documents        → créer document
//   │  ├─ PATCH/PUT /api/v1/me/documents/:id → modifier document
//   │  └─ DELETE /api/v1/me/documents/:id  → supprimer document
//   ├─ USERS (admin)
//   │  ├─ GET  /api/v1/{tenant_id}/users
//   │  ├─ POST /api/v1/{tenant_id}/users
//   │  ├─ PATCH /api/v1/{tenant_id}/users/:id
//   │  └─ DELETE /api/v1/{tenant_id}/users/:id
//   ├─ ROLES (admin)
//   │  ├─ GET  /api/v1/{tenant_id}/roles
//   │  ├─ POST /api/v1/{tenant_id}/roles
//   │  └─ PATCH /api/v1/{tenant_id}/roles/:id
//   ├─ AUDIT
//   │  └─ GET  /api/v1/{tenant_id}/audit
//   └─ SESSIONS
//      └─ GET  /api/v1/auth/sessions
//
// SÉCURITÉ — FEATURE 2 :
//   Le tenant_id N'EST JAMAIS envoyé par le frontend dans l'URL ou le body.
//   Il est extrait uniquement du JWT par le backend.
// =============================================================================

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios'
import { clearTokens } from './auth'
import type {
  LoginResponse,
  Verify2FARequest,
  Verify2FAResponse,
  UserProfile as UserProfileType,
} from '@/types/auth'
import type { UserDashboardResponse, AdminDashboardResponse } from '@/types/dashboard'

// Use relative URL to leverage Next.js rewrites proxy (next.config.js)
// This avoids CORS issues and ensures cookies are sent correctly
const BASE_URL = ''

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
  withCredentials: true,  // ✅ CRITICAL: Sends httpOnly cookies automatically on every request
})

interface RefreshResponse {
  token_type: string
  expires_in: number
}

// Module-level cache for tenant_id access from non-auth functions
let cachedUserProfile: UserProfileType | null = null

export function getCachedUserProfile(): UserProfileType | null {
  return cachedUserProfile
}

export function setCachedUserProfile(profile: UserProfileType | null): void {
  cachedUserProfile = profile
}

// ─────────────────────────────────────────────────────────────────────────
// ERROR HANDLING UTILITY
// ─────────────────────────────────────────────────────────────────────────
export function extractErrorMessage(error: unknown): string {
  if (!error) return 'Une erreur inconnue est survenue.'

  const err = error as any

  // Backend error with nested detail object
  if (err?.response?.data?.detail?.message) {
    return err.response.data.detail.message
  }

  // Backend error with detail as string
  if (typeof err?.response?.data?.detail === 'string') {
    return err.response.data.detail
  }

  // Backend error with message field
  if (err?.response?.data?.message) {
    return err.response.data.message
  }

  // Generic error message
  if (err?.message) {
    return err.message
  }

  return 'Une erreur inconnue est survenue.'
}

// ──────────────────────────────────────────────────────────────────────────
// TENANT ID EXTRACTION
// ──────────────────────────────────────────────────────────────────────────
// Since tenant_id is stored in httpOnly cookies, we can only access it via
// the cached profile from /auth/me or the admin endpoints that require it.
export function getTenantIdFromToken(): string | null {
  return cachedUserProfile?.tenant_id ?? null
}

// ── NO REQUEST INTERCEPTOR NEEDED ───────────────────────────────────────────
// With withCredentials: true, the browser automatically sends httpOnly cookies.
// We no longer need to manually inject Bearer tokens.

// 🔍 DEBUG: Request interceptor to trace outgoing requests
api.interceptors.request.use((config) => {
  if (config.url?.includes('/auth/login')) {
    console.log('[request-interceptor] 📤 POST to /api/v1/auth/login')
    console.log('[request-interceptor] method:', config.method)
    console.log('[request-interceptor] url:', config.url)
    console.log('[request-interceptor] baseURL:', config.baseURL)
    console.log('[request-interceptor] full URL would be:', `${config.baseURL}${config.url}`)
  }
  return config
}, (error) => {
  console.error('[request-interceptor] ❌ request config error:', error)
  return Promise.reject(error)
})

// ── RESPONSE INTERCEPTOR ────────────────────────────────────────────────────
// On 429: reject immediately (no retry, preserve headers for client countdown)
// On 5xx: log X-Request-ID in dev
// On 401: attempt silent token refresh via cookie, then retry
let isRefreshing = false
let refreshQueue: Array<() => void> = []

api.interceptors.response.use(
  (response) => {
    // 🔍 DEBUG: Log successful responses
    if (response.config.url?.includes('/auth/login')) {
      console.log('[interceptor] ✅ login response received:', response.status)
    }
    return response
  },
  async (error: AxiosError) => {
    // 🔍 DEBUG: Log error immediately on entry
    console.log('[interceptor] 🔴 ERROR interceptor triggered')
    console.log('[interceptor] error.response?.status:', error.response?.status)
    console.log('[interceptor] error.config?.url:', error.config?.url)
    console.log('[interceptor] error.config?.method:', error.config?.method)
    console.log('[interceptor] error.message:', error.message)
    
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }
    const status = error.response?.status

    // 422: Log full validation error details
    if (status === 422) {
      console.error('[422 detail]', JSON.stringify(error.response?.data))
      return Promise.reject(error)
    }

    // 429: Do NOT retry, do NOT refresh — reject immediately
    // Preserve the error so the client can read X-RateLimit-Reset
    if (status === 429) {
      return Promise.reject(error)
    }

    // 5xx: Log X-Request-ID in development
    if (process.env.NODE_ENV === 'development' && status && status >= 500) {
      const requestId = error.response?.headers?.['x-request-id']
      console.error(`[${status}] X-Request-ID: ${requestId}`)
    }

    // Don't intercept anything except 401s
    // Skip refresh endpoint itself to avoid infinite loops
    if (
      status !== 401 ||
      originalRequest._retry ||
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/login')
    ) {
      return Promise.reject(error)
    }

    // If refresh is already in progress, queue this request
    if (isRefreshing) {
      return new Promise((resolve) => {
        refreshQueue.push(() => resolve(api(originalRequest)))
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      // POST to refresh endpoint
      // Both access_token and refresh_token cookies are sent automatically (withCredentials)
      // Backend returns new tokens as httpOnly cookies (not in response body)
      await api.post<RefreshResponse>('/api/v1/auth/refresh')

      // New access_token cookie is now set by the backend
      // Retry the original request — it will use the new cookie
      refreshQueue.forEach((cb) => cb())
      refreshQueue = []

      return api(originalRequest)
    } catch (refreshError) {
      refreshQueue = []
      clearTokens()  // No-op now, but kept for consistency
      
      // Redirect to login on refresh failure
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

// =============================================================================
// AUTH
// =============================================================================

export async function login(email: string, password: string): Promise<LoginResponse> {
  // POST /api/v1/auth/login
  // Backend sets access_token and refresh_token as httpOnly cookies
  // Returns { requires_2fa: boolean, partial_token?: string }
  console.log('[api.login] making POST request to /api/v1/auth/login')
  console.log('[api.login] Axios instance baseURL:', api.defaults.baseURL)
  console.log('[api.login] Axios instance withCredentials:', api.defaults.withCredentials)
  
  const { data } = await api.post<LoginResponse>('/api/v1/auth/login', {
    email,
    password,
  })
  
  // Sanitize response before logging (remove sensitive tokens)
  const sanitized = { ...data }
  if (sanitized.partial_token) sanitized.partial_token = '[REDACTED]'
  if (sanitized.access_token) sanitized.access_token = '[REDACTED]'
  if (sanitized.refresh_token) sanitized.refresh_token = '[REDACTED]'
  console.log('[api.login] ✅ response received:', sanitized)
  
  return data
}

export async function verify2FA(
  req: Verify2FARequest,
  partialToken: string
): Promise<Verify2FAResponse> {
  // POST /api/v1/auth/2fa/login
  // body: { partial_token, code?, backup_code? }
  // Backend sets access_token and refresh_token as httpOnly cookies
  // Only include optional fields if they have values (avoid sending null)
  const body: any = { partial_token: partialToken }
  if (req.totp_code) body.code = req.totp_code
  if (req.backup_code) body.backup_code = req.backup_code
  
  const { data } = await api.post<Verify2FAResponse>(
    '/api/v1/auth/2fa/login',
    body
  )
  return data
}

export async function logout(): Promise<void> {
  try {
    // POST /auth/logout
    // Backend deletes httpOnly cookies and revokes session in DB
    await api.post('/api/v1/auth/logout')
  } finally {
    clearTokens()  // No-op now, but kept for consistency
  }
}

export async function register(
  email: string,
  password: string,
  full_name: string
): Promise<void> {
  // POST /auth/register
  // Backend sets access_token and refresh_token as httpOnly cookies
  await api.post('/api/v1/auth/register', {
    email,
    password,
    full_name,
  })
}

export interface RegisterUserPayload {
  first_name: string
  last_name: string
  email: string
  password: string
  org_name: string
  sector: string
  country: string
  org_size: string
  portals: string[]
  plan: 'fondements' | 'avancee' | 'entreprise'
  billing: 'monthly' | 'annual'
}

export interface RegisterResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user_id: string
  tenant_id: string
  email: string
  tenant_name: string
  trial_ends_at: string
  email_verified: boolean
}

export async function registerUser(payload: RegisterUserPayload): Promise<RegisterResponse> {
  const { data } = await api.post<RegisterResponse>('/api/v1/auth/register', payload)
  return data
}

export async function getMe(): Promise<UserProfileType> {
  const { data } = await api.get<UserProfileType>('/api/v1/auth/me')
  // Cache for tenant_id access in admin functions
  setCachedUserProfile(data)
  return data
}

export async function getSessions(): Promise<unknown> {
  const { data } = await api.get('/api/v1/auth/sessions')
  return data
}

// =============================================================================
// DOCUMENTS
// =============================================================================

export async function getDocuments(params: Record<string, unknown> = {}): Promise<unknown> {
  const { data } = await api.get('/api/v1/me/documents', { params })
  return data
}

export async function getDocumentStats(): Promise<unknown> {
  const { data } = await api.get('/api/v1/me/documents/stats')
  return data
}

export async function getDocument(id: string): Promise<unknown> {
  const { data } = await api.get(`/api/v1/me/documents/${id}`)
  return data
}

export async function createDocument(payload: Record<string, unknown>): Promise<unknown> {
  const { data } = await api.post('/api/v1/me/documents', payload)
  return data
}

export async function updateDocument(
  id: string,
  payload: Record<string, unknown>
): Promise<unknown> {
  const { data } = await api.patch(`/api/v1/me/documents/${id}`, payload)
  return data
}

export async function deleteDocument(id: string, reason?: string | null): Promise<unknown> {
  const body = reason ? { reason } : {}
  const { data } = await api.delete(`/api/v1/me/documents/${id}`, {
    data: body,
  })
  return data
}

// =============================================================================
// DASHBOARD
// =============================================================================

export async function getDashboard(): Promise<UserDashboardResponse> {
  // GET /api/v1/me/dashboard/user
  const { data } = await api.get<UserDashboardResponse>('/api/v1/me/dashboard/user')
  return data
}

export async function getAdminDashboard(): Promise<AdminDashboardResponse> {
  // GET /api/v1/me/dashboard/admin
  const { data } = await api.get<AdminDashboardResponse>('/api/v1/me/dashboard/admin')
  return data
}

// =============================================================================
// USERS (Admin)
// =============================================================================

export async function getUsers(params: Record<string, unknown> = {}): Promise<unknown> {
  const tenantId = getTenantIdFromToken()
  if (!tenantId) throw new Error('Tenant ID not found in token')
  const { data } = await api.get(`/api/v1/${tenantId}/users`, { params })
  return data
}

export async function createUser(payload: Record<string, unknown>): Promise<unknown> {
  const tenantId = getTenantIdFromToken()
  if (!tenantId) throw new Error('Tenant ID not found in token')
  const { data } = await api.post(`/api/v1/${tenantId}/users`, payload)
  return data
}

export async function updateUser(
  id: string,
  payload: Record<string, unknown>
): Promise<unknown> {
  const tenantId = getTenantIdFromToken()
  if (!tenantId) throw new Error('Tenant ID not found in token')
  const { data } = await api.patch(`/api/v1/${tenantId}/users/${id}`, payload)
  return data
}

export async function deleteUser(id: string): Promise<void> {
  const tenantId = getTenantIdFromToken()
  if (!tenantId) throw new Error('Tenant ID not found in token')
  await api.delete(`/api/v1/${tenantId}/users/${id}`)
}

// =============================================================================
// ROLES (Admin)
// =============================================================================

export async function getRoles(params: Record<string, unknown> = {}): Promise<unknown> {
  const tenantId = getTenantIdFromToken()
  if (!tenantId) throw new Error('Tenant ID not found in token')
  const { data } = await api.get(`/api/v1/${tenantId}/roles`, { params })
  return data
}

export async function createRole(payload: Record<string, unknown>): Promise<unknown> {
  const tenantId = getTenantIdFromToken()
  if (!tenantId) throw new Error('Tenant ID not found in token')
  const { data } = await api.post(`/api/v1/${tenantId}/roles`, payload)
  return data
}

export async function updateRole(
  id: string,
  payload: Record<string, unknown>
): Promise<unknown> {
  const tenantId = getTenantIdFromToken()
  if (!tenantId) throw new Error('Tenant ID not found in token')
  const { data } = await api.patch(`/api/v1/${tenantId}/roles/${id}`, payload)
  return data
}

// =============================================================================
// AUDIT
// =============================================================================

export async function getAuditLogs(params: Record<string, unknown> = {}): Promise<unknown> {
  const tenantId = getTenantIdFromToken()
  if (!tenantId) throw new Error('Tenant ID not found in token')
  const { data } = await api.get(`/api/v1/${tenantId}/audit`, { params })
  return data
}

// =============================================================================
// TENANT SETTINGS
// =============================================================================

export interface TenantMetadata {
  logo_url?: string
  logo_path?: string
  [key: string]: unknown
}

export interface TenantInfo {
  id: string
  name: string
  email: string
  subscription_plan: string
  is_active: boolean
  tenant_metadata: TenantMetadata
  created_at: string
  updated_at: string
}

export async function getTenantInfo(): Promise<TenantInfo> {
  // GET /api/v1/me/tenant
  // Returns current user's tenant with logo metadata
  const { data } = await api.get<TenantInfo>('/api/v1/me/tenant')
  return data
}

export interface UploadTenantLogoResponse {
  logo_url: string
  message: string
}

export async function updateTenantLogo(file: File): Promise<UploadTenantLogoResponse> {
  // POST /api/v1/me/tenant/logo (multipart/form-data)
  // Accepts: PNG, JPEG, WebP, SVG only; max 2MB
  // Returns: { logo_url: presigned_url, message: "Logo mis à jour" }
  const formData = new FormData()
  formData.append('file', file)
  
  const { data } = await api.post<UploadTenantLogoResponse>(
    '/api/v1/me/tenant/logo',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' }
    }
  )
  return data
}

// =============================================================================
// DOCUMENT UPLOAD
// =============================================================================

/**
 * Upload a document with idempotency guarantee
 * @param file - File to upload (PDF, DOCX, XLS, XLSX, TXT)
 * @param reference - Optional reference number (AO-2026-001)
 * @param deadline - Optional deadline (ISO 8601)
 * @param budget_eur - Optional budget in EUR
 * @returns DocumentResponse with status='uploaded'
 */
export async function uploadDocument(
  file: File,
  reference?: string,
  deadline?: string,
  budget_eur?: number
): Promise<any> {
  // Generate unique idempotency key per upload (crypto.randomUUID is native browser API)
  const idempotencyKey = crypto.randomUUID()
  
  const formData = new FormData()
  formData.append('file', file)
  if (reference) formData.append('reference', reference)
  if (deadline) formData.append('deadline', deadline)
  if (budget_eur !== undefined) formData.append('budget_eur', budget_eur.toString())
  
  const { data } = await api.post(
    '/api/v1/me/documents/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Idempotency-Key': idempotencyKey,
      },
    }
  )
  return data
}

/**
 * Download document by generating a presigned URL or fetching the file
 * @param docId - Document UUID
 * @returns Promise that triggers browser download
 */
export async function downloadDocument(docId: string): Promise<void> {
  try {
    const response = await api.get(`/api/v1/me/documents/${docId}/download`, {
      responseType: 'blob',
    })
    
    // Create blob download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `document-${docId}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.parentNode?.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Download failed:', error)
    throw error
  }
}

export default api
