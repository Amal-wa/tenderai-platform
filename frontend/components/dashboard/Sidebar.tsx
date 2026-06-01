'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import {
  LayoutDashboard, FileText, BarChart2,
  Users, Settings, LogOut
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import api from '@/lib/api'

interface NavItem {
  label: string
  href: string
  icon: React.ComponentType<{ size?: number | string; className?: string }>
  badge?: number
}

interface NavSection {
  label: string
  items: NavItem[]
}

const navSections: NavSection[] = [
  {
    label: 'PRINCIPAL',
    items: [
      { label: 'Mon tableau de bord', href: '/dashboard',        icon: LayoutDashboard },
      { label: 'Mes Appels d\'offres',href: '/dashboard/tenders',icon: FileText },
      { label: 'Analyse IA',          href: '/dashboard/analyse',icon: BarChart2 },
    ],
  },
  {
    label: 'SYSTÈME',
    items: [
      { label: 'Équipe',         href: '/dashboard/team',          icon: Users },
      { label: 'Paramètres',     href: '/dashboard/settings',      icon: Settings },
    ],
  },
]

function getAvatarInitials(fullName: string | null | undefined): string {
  if (!fullName) return 'U'
  const parts = fullName.trim().split(' ').filter(w => w.length > 0)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return parts[0].slice(0, 2).toUpperCase()
}

function getRoleDisplay(role: string | { id?: string; name: string; [key: string]: any } | null | undefined): string {
  if (!role) return 'Utilisateur'
  return typeof role === 'string' ? role : (role?.name || 'Utilisateur')
}

export default function Sidebar(): React.ReactElement {
  const pathname = usePathname()
  const { user, isLoading, logout } = useAuth()
  const [tenant, setTenant] = useState<{ name: string; logo_url?: string } | null>(null)
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  useEffect(() => {
    api.get('/api/v1/me/tenant')
      .then(res => {
        setTenant({
          name: res.data.name,
          logo_url: res.data.tenant_metadata?.logo_url
        })
      })
      .catch(() => null)
  }, [])

  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      await logout()
    } finally {
      setIsLoggingOut(false)
    }
  }

  return (
    <aside className="w-60 bg-[var(--navy)] min-h-screen flex flex-col sticky top-0 h-screen">
      {/* Logo */}
      <div className="p-4 border-b border-white/[0.06]">
        <div className="flex flex-col items-center gap-3 mb-3">
          {tenant?.logo_url ? (
            <img
              src={tenant.logo_url}
              alt={tenant.name}
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).style.display = 'none'
              }}
              className="h-24 w-auto max-w-[160px] object-contain rounded-lg flex-shrink-0"
            />
          ) : (
            <div className="w-20 h-20 bg-[var(--amber)] rounded-xl flex items-center justify-center flex-shrink-0">
              <span className="font-heading text-lg font-black text-white">
                {tenant?.name
                  ? tenant.name
                    .trim()
                    .split(' ')
                    .filter((n: string) => n.length > 0)
                    .map((n: string) => n[0])
                    .slice(0, 2)
                    .join('')
                    .toUpperCase()
                : 'T'}
              </span>
            </div>
          )}
          <p className="text-xs font-medium text-white/70 text-center">{tenant?.name}</p>
        </div>
      </div>

      {/* Tenant Pill */}
      <div className="mx-4 my-3 bg-[var(--navy-3)] rounded-xl p-3 flex items-center justify-between flex-shrink-0">
        <span className="text-xs font-semibold text-white">{tenant?.name ?? '...'}</span>
        {user?.subscription_plan && !isLoading && (
          <span className="text-[10px] font-bold text-[var(--amber)] bg-[var(--amber-soft)] px-2 py-0.5 rounded-full">
            {user.subscription_plan}
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-4 py-6 space-y-8">
        {navSections.map((section) => (
          <div key={section.label}>
            <p className="text-[9px] font-bold text-white/40 uppercase tracking-wider ps-3 mb-2">
              {section.label}
            </p>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const isActive = item.href === '/dashboard'
                  ? pathname === item.href
                  : pathname === item.href || pathname.startsWith(`${item.href}/`)
                const Icon = item.icon
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-[rgba(196,150,42,0.15)] text-[var(--amber)]'
                          : 'text-white/60 hover:text-white/80'
                      }`}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <Icon size={16} className="flex-shrink-0" />
                      <span>{item.label}</span>
                      {item.badge && (
                        <span className="ms-auto flex h-5 w-5 items-center justify-center rounded-full bg-[var(--danger)] text-[9px] font-bold text-white">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* User Section */}
      <div className="border-t border-white/[0.06] p-4 flex items-center gap-3 flex-shrink-0">
        {isLoading ? (
          <>
            <div className="w-9 h-9 rounded-full bg-white/10 animate-pulse flex-shrink-0" />
            <div className="flex-1 min-w-0 space-y-2">
              <div className="h-3 bg-white/10 rounded animate-pulse w-20" />
              <div className="h-2.5 bg-white/10 rounded animate-pulse w-16" />
            </div>
          </>
        ) : (
          <>
            <div className="w-9 h-9 rounded-full bg-[var(--amber)] flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-white">
                {getAvatarInitials(user?.full_name)}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">
                {user?.full_name ?? 'Utilisateur'}
              </p>
              <p className="text-[10px] text-white/40 truncate">
                {getRoleDisplay(user?.role)}
              </p>
            </div>
          </>
        )}
        <button
          onClick={handleLogout}
          disabled={isLoggingOut || isLoading}
          aria-label="Se déconnecter"
          className="flex-shrink-0 p-1.5 hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <LogOut size={16} className="text-white/60" />
        </button>
      </div>
    </aside>
  )
}
