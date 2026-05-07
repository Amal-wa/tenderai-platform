// =============================================================================
// context/AuthContext.tsx — Contexte d'authentification global (TypeScript / App Router)
//
// Pour App Router (Next.js 14+), ce contexte est wrappé dans Providers component
// et marqué 'use client' pour les interactions côté client.
// =============================================================================

'use client'

import { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { login as apiLogin, logout as apiLogout, getMe, extractErrorMessage } from '@/lib/api'
import { clearTokens } from '@/lib/auth'
import type { UserProfile, AuthContextType } from '@/types/auth'

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }): ReactNode {
  const router = useRouter()
  const pathname = usePathname()
  const initRef = useRef(false)

  const [user, setUser] = useState<UserProfile | null>(null)
  const [tenant, setTenant] = useState<{
    id: string
    name: string
    plan: string
    color: string
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [ready, setReady] = useState(false)

  const AUTH_PAGES = ['/', '/login', '/register', '/forgot-password', '/2fa-setup', '/2fa-login']

  // ── Au chargement : recharger le profil si un token existe ─────────────────
  useEffect(() => {
    async function init() {
      try {
        if (initRef.current) {
          setReady(true)
          setIsLoading(false)
          return
        }
        initRef.current = true

        if (AUTH_PAGES.includes(pathname)) {
          setReady(true)
          setIsLoading(false)
          return
        }

        try {
          const profile = await getMe()
          applyProfile(profile)
        } catch {
          clearTokens()
          setUser(null)
        }
      } finally {
        setReady(true)
        setIsLoading(false)
      }
    }
    init()
  }, [pathname])

  // ── Applique le profil reçu de /auth/me ───────────────────────────────────
  function applyProfile(profile: UserProfile) {
    setUser({
      id: profile.id,
      email: profile.email,
      full_name: profile.full_name,
      role: profile.role,
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
    setIsLoading(true)
    setError(null)
    try {
      const loginResp = await apiLogin(email, password)

      if (loginResp.requires_2fa) {
        throw new Error('2FA required — use LoginPageClient flow instead')
      }

      const profile = await getMe()
      applyProfile(profile)

      const route = ['admin', 'superadmin'].includes(profile.role?.toString?.() || '')
        ? '/dashboard/admin'
        : '/dashboard/user'
      router.push(route)
    } catch (err: any) {
      const msg = extractErrorMessage(err)
      setError(msg)
    } finally {
      setLoading(false)
      setIsLoading(false)
    }
  }

  // ── Finalize login after tokens already saved ──────────────────────────────
  // Used by login page when handling 2FA flow or direct token save.
  async function finalizeLogin(redirect: string | null = null): Promise<void> {
    setIsLoading(true)
    try {
      const profile = await getMe()
      applyProfile(profile)

      const targetRoute = redirect || (
        ['admin', 'superadmin'].includes(profile.role?.toString?.() || '')
          ? '/dashboard/admin'
          : '/dashboard/user'
      )
      router.push(targetRoute)
    } catch (err) {
      clearTokens()
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  // ── Logout ────────────────────────────────────────────────────────────────
  async function logout(): Promise<void> {
    setLoading(true)
    try {
      await apiLogout()
    } catch {
    } finally {
      setUser(null)
      setTenant(null)
      initRef.current = false
      setLoading(false)
      router.push('/login')
    }
  }

  // ── Mettre à jour le profil local (après modification) ─────────────────────
  function updateUserProfile(updates: Partial<UserProfile>): void {
    setUser((prev) => (prev ? { ...prev, ...updates } : null))
  }

  const value: AuthContextType = {
    user,
    tenant,
    login,
    logout,
    finalizeLogin,
    loading,
    isLoading,
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
