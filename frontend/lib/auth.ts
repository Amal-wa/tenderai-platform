// =============================================================================
// lib/auth.ts — Token management via httpOnly cookies
//
// ✅ SECURITY UPGRADE: Access tokens are now stored in httpOnly cookies only.
// This protects against XSS attacks — JavaScript cannot access httpOnly cookies.
//
// The browser automatically sends httpOnly cookies on every request via
// axios withCredentials: true. Token rotation is handled server-side.
//
// STRUCTURE D'UN JWT TenderAI (payload décodé) :
// {
//   "sub": "user-uuid",
//   "tenant_id": "tenant-uuid",   ← extrait par le backend pour RLS
//   "role": "analyst",
//   "permissions": ["documents:read", "documents:write"],
//   "exp": 1234567890,
//   "jti": "token-unique-id"       ← pour détecter le replay
// }
// =============================================================================

interface TokenPayload {
  sub: string
  tenant_id: string
  role: string
  permissions: string[]
  exp: number
  jti: string
  [key: string]: unknown
}

// ─────────────────────────────────────────────────────────────────────────
// NO-OP FUNCTIONS FOR BACKWARD COMPATIBILITY
// ─────────────────────────────────────────────────────────────────────────
// These functions are kept to avoid breaking existing imports.
// They are no-ops now because tokens are managed by httpOnly cookies.
// The browser sends cookies automatically on every request.

/**
 * @deprecated: Tokens are now stored in httpOnly cookies, not localStorage
 * No action needed — the backend sets the cookie.
 */
export function saveTokens(_accessToken: string, _refreshToken?: string | null): void {
  // No-op: token is set by backend as httpOnly cookie
}

/**
 * @deprecated: Tokens are in httpOnly cookies, not accessible from JavaScript
 * Returns null because we can't read httpOnly cookies from JS.
 */
export function getAccessToken(): string | null {
  // No-op: Returns null because httpOnly cookies are not readable via JS
  // Axios sends the cookie automatically via withCredentials: true
  return null
}

/**
 * @deprecated: Logout clears cookies server-side, not from JavaScript
 * No action needed on frontend.
 */
export function clearTokens(): void {
  // No-op: logout endpoint deletes httpOnly cookies server-side
}

// ─────────────────────────────────────────────────────────────────────────
// Décode le payload JWT sans vérifier la signature
// (la vérification se fait côté serveur — on lit juste pour l'UI)
// ⚠️ NOTE: No longer used in auth flow since we can't access httpOnly tokens from JS
// Kept for potential future use (e.g., if tokens are displayed in dev tools)
// ─────────────────────────────────────────────────────────────────────────
export function decodeToken(token: string): TokenPayload | null {
  if (!token) return null
  try {
    const payload = token.split('.')[1]
    // atob décode le base64, puis JSON.parse extrait l'objet
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
  } catch {
    return null
  }
}

/**
 * @deprecated: No longer works — we cannot read httpOnly cookies from JavaScript
 * Use /api/v1/auth/me instead to verify authentication status.
 */
export function isTokenValid(): boolean {
  // No-op: cannot check httpOnly cookie expiry from JS
  // Server returns 401 if token is invalid; let the interceptor handle it
  return false
}

/**
 * @deprecated: No longer works — we cannot read httpOnly cookies from JavaScript
 * Use /api/v1/auth/me instead to get tenant_id from server response.
 */
export function getTenantIdFromToken(): string | null {
  // No-op: cannot read httpOnly cookies from JS
  return null
}
