'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronLeft, LogOut } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import ProfileSection from './sections/ProfileSection'
import SecuritySection from './sections/SecuritySection'
import AuthSection from './sections/AuthSection'
import OrganisationSection from './sections/OrganisationSection'
import ApiKeysSection from './sections/ApiKeysSection'

type SectionId = 'profile' | 'security' | 'auth' | 'organisation' | 'apikeys'

interface SectionConfig {
  id: SectionId
  title: string
  subtitle: string
  icon: React.ComponentType<any>
  group: 'account' | 'workspace'
  component: React.ComponentType<{ isDirty: boolean; onDirtyChange: (dirty: boolean) => void }>
  requiredRoles?: string[]
}

const sections: SectionConfig[] = [
  {
    id: 'profile',
    title: 'Profil',
    subtitle: 'Gérez vos informations personnelles',
    icon: () => null,
    group: 'account',
    component: ProfileSection,
  },
  {
    id: 'security',
    title: 'Sécurité',
    subtitle: 'Mot de passe, sessions actives',
    icon: () => null,
    group: 'account',
    component: SecuritySection,
  },
  {
    id: 'auth',
    title: 'Authentification',
    subtitle: '2FA, passkeys, historique de connexion',
    icon: () => null,
    group: 'account',
    component: AuthSection,
  },
  {
    id: 'organisation',
    title: 'Organisation',
    subtitle: 'Workspace, membres et quotas',
    icon: () => null,
    group: 'workspace',
    component: OrganisationSection,
    requiredRoles: ['superadmin', 'admin'],
  },
  {
    id: 'apikeys',
    title: 'Clés API',
    subtitle: 'Accès tiers et permissions scopées',
    icon: () => null,
    group: 'workspace',
    component: ApiKeysSection,
    requiredRoles: ['superadmin', 'admin', 'manager'],
  },
]

export default function SettingsClient() {
  const router = useRouter()
  const { user, logout } = useAuth()
  const [activeSection, setActiveSection] = useState<SectionId>('profile')
  const [isDirty, setIsDirty] = useState(false)
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const currentSection = sections.find(s => s.id === activeSection)
  const Component = currentSection?.component

  const handleSectionChange = (sectionId: SectionId) => {
    if (isDirty) {
      if (!confirm('Modifications non enregistrées — quitter quand même ?')) {
        return
      }
    }
    setActiveSection(sectionId)
    setIsDirty(false)
  }

  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      await logout()
    } finally {
      setIsLoggingOut(false)
    }
  }

  if (!user) return null

  const userInitials = user.full_name
    ?.split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase() || 'U'

  const userRole = typeof user.role === 'string' ? user.role : user.role?.name

  return (
    <div className="flex h-screen bg-[var(--cream)]" style={{ backgroundColor: 'var(--color-cream, #F5F3EE)' }}>
      {/* SIDEBAR */}
      <aside className="w-[232px] flex-shrink-0 border-r flex flex-col overflow-hidden" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
        {/* Header */}
        <div className="p-[14px] border-b flex items-center gap-2 cursor-pointer hover:opacity-80 transition" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }} onClick={() => router.push('/dashboard')}>
          <div className="w-5 h-5 border rounded flex items-center justify-center flex-shrink-0" style={{ borderColor: 'var(--color-border-secondary, #E5E0D8)' }}>
            <ChevronLeft size={10} style={{ color: 'var(--color-text-secondary, #3A3530)' }} />
          </div>
          <span className="text-xs font-medium" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
            Retour au Dashboard
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-6">
          {/* Account Section */}
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider px-2 mb-1" style={{ color: 'var(--color-text-tertiary, #6B6560)', letterSpacing: '0.07em' }}>
              Compte
            </div>
            <div className="space-y-0.5">
              {sections
                .filter(s => s.group === 'account')
                .map(section => (
                  <button
                    key={section.id}
                    onClick={() => handleSectionChange(section.id)}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors relative ${ activeSection === section.id
                      ? 'font-medium'
                      : ''
                    }`}
                    style={{
                      backgroundColor: activeSection === section.id ? 'var(--color-background-primary, #F5F3EE)' : 'transparent',
                      color: activeSection === section.id ? 'var(--color-text-primary, #0F1C35)' : 'var(--color-text-secondary, #3A3530)',
                    }}
                  >
                    <span className="flex-1 text-left text-[13px]">{section.title}</span>
                    {activeSection === section.id && (
                      <div
                        className="w-0.5 h-4 rounded-sm flex-shrink-0"
                        style={{ backgroundColor: 'var(--color-amber, #C4962A)' }}
                      />
                    )}
                  </button>
                ))}
            </div>
          </div>

          {/* Workspace Section */}
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider px-2 mb-1" style={{ color: 'var(--color-text-tertiary, #6B6560)', letterSpacing: '0.07em' }}>
              Workspace
            </div>
            <div className="space-y-0.5">
              {sections
                .filter(s => s.group === 'workspace')
                .map(section => (
                  <button
                    key={section.id}
                    onClick={() => handleSectionChange(section.id)}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors relative ${
                      activeSection === section.id ? 'font-medium' : ''
                    }`}
                    style={{
                      backgroundColor: activeSection === section.id ? 'var(--color-background-primary, #F5F3EE)' : 'transparent',
                      color: activeSection === section.id ? 'var(--color-text-primary, #0F1C35)' : 'var(--color-text-secondary, #3A3530)',
                    }}
                  >
                    <span className="flex-1 text-left text-[13px]">{section.title}</span>
                    {activeSection === section.id && (
                      <div
                        className="w-0.5 h-4 rounded-sm flex-shrink-0"
                        style={{ backgroundColor: 'var(--color-amber, #C4962A)' }}
                      />
                    )}
                  </button>
                ))}
            </div>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-3 border-t flex items-center gap-2.5" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-[10px] font-semibold"
            style={{ backgroundColor: 'var(--navy, #0F1C35)', color: 'var(--color-amber, #C4962A)' }}
          >
            {userInitials}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-semibold truncate" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
              {user.full_name}
            </div>
            <div className="text-[11px] truncate" style={{ color: 'var(--color-text-tertiary, #6B6560)' }}>
              {userRole} · {user.tenant_name}
            </div>
          </div>
          <button
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="p-0.5 hover:opacity-70 transition"
            title="Déconnexion"
          >
            <LogOut size={14} style={{ color: 'var(--color-text-secondary, #3A3530)' }} />
          </button>
        </div>
      </aside>

      {/* MAIN */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-7 py-5 border-b flex items-center justify-between" style={{ borderColor: 'var(--color-border-tertiary, #E5E0D8)' }}>
          <div>
            <h2 className="text-base font-semibold" style={{ color: 'var(--color-text-primary, #0F1C35)' }}>
              {currentSection?.title}
            </h2>
            <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary, #3A3530)' }}>
              {currentSection?.subtitle}
            </p>
          </div>
          {isDirty && (
            <div
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium border"
              style={{
                backgroundColor: 'rgba(196,150,42,0.1)',
                borderColor: 'rgba(196,150,42,0.3)',
                color: 'var(--color-amber, #C4962A)',
              }}
            >
              <div
                className="w-1.5 h-1.5 rounded-full animate-pulse"
                style={{ backgroundColor: 'var(--color-amber, #C4962A)' }}
              />
              Modifications non sauvegardées
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-7">
          {Component ? (
            <Component isDirty={isDirty} onDirtyChange={setIsDirty} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <p style={{ color: 'var(--color-text-secondary, #3A3530)' }}>Chargement...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
