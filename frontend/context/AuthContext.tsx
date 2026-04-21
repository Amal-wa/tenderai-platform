// =============================================================================
// context/AuthContext.tsx — Contexte d'authentification global (TypeScript / App Router)
//
// Pour App Router (Next.js 14+), ce contexte est wrappé dans Providers component
// et marqué 'use client' pour les interactions côté client.
// =============================================================================

'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { login as apiLogin, logout as apiLogout, getMe, extractErrorMessage } from '@/lib/api'
import { clearTokens } from '@/lib/auth'
import type { UserProfile } from '@/types/auth'

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

const AuthContext = createContext<AuthContextType | null>(null)

// ── Module-level guard against React StrictMode double-mount ──────────────────
// In React 18 StrictMode (dev only), components are unmounted and remounted to test
// cleanup handlers. A useRef inside a component would be reset on remount, so we use
// a module-level variable that persists across component remounts.
// (In production, this has no effect as StrictMode is disabled)
let appAuthInitialized = false

export function AuthProvider({ children }: { children: ReactNode }): ReactNode {
  const router = useRouter()
  const pathname = usePathname()

  const [user, setUser] = useState<UserProfile | null>(null)
  const [tenant, setTenant] = useState<{
    id: string
    name: string
    plan: string
    color: string
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [ready, setReady] = useState(false) // true quand l'init est terminée

  const AUTH_PAGES = ['/', '/login', '/register', '/forgot-password', '/2fa-setup', '/2fa-login', '/2fa-disable']

  // ── Au chargement : recharger le profil si un token existe ─────────────────
  useEffect(() => {
    async function init() {
      // ✅ STRICTMODE FIX: Check module-level flag (survives remounts)
      if (appAuthInitialized) {
        setReady(true)
        return
      }
      appAuthInitialized = true

      // Skip getMe() on auth pages and landing page — no session expected there
      if (AUTH_PAGES.includes(pathname)) {
        setReady(true)
        return
      }

      try {
        // Attempt to fetch profile — if 401, interceptor will redirect to /login
        const profile = await getMe()
        applyProfile(profile)
      } catch {
        // L'interceptor dans api.ts gère déjà la redirection vers /login si le refresh échoue.
        clearTokens()
      }
      setReady(true)
    }
    init()
  }, [pathname])

  // ── Applique le profil reçu de /auth/me ───────────────────────────────────
  function applyProfile(profile: UserProfile) {
    // Normaliser le rôle : extraire le nom s'il vient sous forme d'objet
    const normalizedRole = (typeof profile.role === 'object' && profile.role?.name) 
      ? profile.role.name 
      : (profile.role as string) || ''

    setUser({
      id: profile.id,
      email: profile.email,
      full_name: profile.full_name,
      role: normalizedRole,
      is_active: profile.is_active,
      totp_enabled: profile.totp_enabled ?? false,
      tenant_id: profile.tenant_id,
      tenant_name: profile.tenant_name,
      subscription_plan: profile.subscription_plan,
    })
    setTenant({
      id: profile.tenant_id,
      name: profile.tenant_name,
      plan: profile.subscription_plan,
      color: profile.tenant_color || '#C4962A',
    })
  }

  // ── Login ─────────────────────────────────────────────────────────────────
  // ⚠️ Note: This function is NOT used by the 2FA flow. LoginPageClient handles
  // the login + verify2FA directly. This is kept for simple login without 2FA.
  async function login(email: string, password: string): Promise<void> {
    setLoading(true)
    setError(null)
    try {
      // 1. POST /api/v1/auth/login
      // Backend sets cookies directly; no tokens returned in response
      const loginResp = await apiLogin(email, password)

      // If requires_2fa, LoginPageClient handles it — this function shouldn't be called
      if (loginResp.requires_2fa) {
        throw new Error('2FA required — use LoginPageClient flow instead')
      }

      // 2. Charger le profil enrichi
      const profile = await getMe()
      applyProfile(profile)

      // 3. Rediriger vers le dashboard avec rôle-based routing
      const route = ['admin', 'superadmin'].includes(profile.role?.toString?.() || '')
        ? '/dashboard/admin'
        : '/dashboard/user'
      router.push(route)
    } catch (err: any) {
      const msg = extractErrorMessage(err)
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  // ── Finalize login after tokens already saved ──────────────────────────────
  // Used by login page when handling 2FA flow or direct token save.
  async function finalizeLogin(redirect: string | null = null): Promise<void> {
    try {
      const profile = await getMe()
      applyProfile(profile)

      // Determine route based on role if no redirect specified
      const targetRoute = redirect || (
        ['admin', 'superadmin'].includes(profile.role?.toString?.() || '')
          ? '/dashboard/admin'
          : '/dashboard/user'
      )
      router.push(targetRoute)
    } catch (err) {
      clearTokens()
      throw err
    }
  }

  // ── Logout ────────────────────────────────────────────────────────────────
  async function logout(): Promise<void> {
    setLoading(true)
    try {
      await apiLogout() // révoque la session côté serveur
    } catch {
      // On déconnecte quand même côté client
    } finally {
      setUser(null)
      setTenant(null)
      setLoading(false)
      router.push('/login')
    }
  }

  // ── Mettre à jour le profil local (après modification) ─────────────────────
  function updateUserProfile(updates: Partial<UserProfile>): void {
    setUser((prev) => (prev ? { ...prev, ...updates } : null))
  }

  // Ne pas afficher les pages avant que l'init soit terminée
  if (!ready) return null

  const value: AuthContextType = {
    user,
    tenant,
    login,
    logout,
    finalizeLogin,
    loading,
    error,
    setError,
    ready,
    updateUserProfile,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth doit être utilisé dans AuthProvider')
  return ctx
}
