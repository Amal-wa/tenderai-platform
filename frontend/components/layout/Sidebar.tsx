'use client'

import { useRouter, usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { useRef, useState, useEffect } from 'react'
import {
  LayoutDashboard,
  FileText,
  Send,
  ShieldCheck,
  BarChart2,
  Settings,
  Plug,
  HelpCircle,
  ChevronRight,
  Upload,
  type LucideIcon,
} from 'lucide-react'
import TenderAILogo from '@/components/ui/TenderAILogo'
import { cn } from '@/lib/utils'
import { getTenantInfo, updateTenantLogo, extractErrorMessage, type TenantInfo } from '@/lib/api'
import { useAuth } from '@/context/AuthContext'

interface NavItem {
  label: string
  icon: LucideIcon
  href: string
  badge?: string
  badgeVariant?: 'gold' | 'green'
}

const mainNav: NavItem[] = [
  { label: 'Tableau de bord', icon: LayoutDashboard, href: '/dashboard' },
  { label: 'Documents', icon: FileText, href: '/documents', badge: '12', badgeVariant: 'gold' },
  {
    label: 'Propositions',
    icon: Send,
    href: '/propositions',
    badge: '3',
    badgeVariant: 'green',
  },
  { label: 'Conformité', icon: ShieldCheck, href: '/conformite' },
  { label: 'Analytiques', icon: BarChart2, href: '/analytics' },
]

const configNav: NavItem[] = [
  { label: 'Paramètres', icon: Settings, href: '/settings' },
  { label: 'Intégrations', icon: Plug, href: '/integrations' },
  { label: 'Aide', icon: HelpCircle, href: '/help' },
]

export default function Sidebar() {
  const router = useRouter()
  const pathname = usePathname()
  const { user } = useAuth()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [tenantInfo, setTenantInfo] = useState<TenantInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch tenant info on mount
  useEffect(() => {
    async function loadTenantInfo() {
      try {
        setLoading(true)
        const info = await getTenantInfo()
        setTenantInfo(info)
      } catch (err) {
        console.error('Failed to load tenant info:', err)
        setError(extractErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }
    
    loadTenantInfo()
  }, [])

  // Get logo URL from tenant metadata
  const logoUrl = tenantInfo?.tenant_metadata?.logo_url
  const tenantName = tenantInfo?.name || 'Tenant'
  
  // Check if current user is admin or superadmin
  const userRole = user?.role
  const canUploadLogo = userRole === 'admin' || userRole === 'superadmin' || userRole === 'tenant_admin'

  // Handle logo file selection
  const handleLogoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml']
    if (!validTypes.includes(file.type)) {
      setError('Format non valide. Accepté: PNG, JPEG, WebP, SVG')
      return
    }

    // Validate file size (max 2MB)
    const maxSize = 2 * 1024 * 1024 // 2MB
    if (file.size > maxSize) {
      setError('Fichier trop volumineux. Maximum: 2MB')
      return
    }

    try {
      setUploading(true)
      setError(null)
      const response = await updateTenantLogo(file)
      
      // Update local tenant info with new logo URL
      if (tenantInfo) {
        setTenantInfo({
          ...tenantInfo,
          tenant_metadata: {
            ...tenantInfo.tenant_metadata,
            logo_url: response.logo_url
          }
        })
      }
    } catch (err) {
      console.error('Logo upload failed:', err)
      setError(extractErrorMessage(err))
    } finally {
      setUploading(false)
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <aside className="fixed left-0 top-0 h-screen w-[220px] bg-navy flex flex-col z-20">
      {/* Logo */}
      <div className="px-4 pt-4 pb-3 border-b border-white/[0.06]">
        <TenderAILogo size="sm" theme="dark" showText={true} />
      </div>

      {/* Tenant block */}
      <div 
        className="mx-3 mt-3 p-2.5 bg-white/[0.05] border border-white/[0.08] rounded-lg 
          flex items-center gap-2.5 group relative"
      >
        {/* Logo or Avatar */}
        {logoUrl && !loading ? (
          <img 
            src={logoUrl} 
            alt={tenantName}
            className="w-7 h-7 rounded-lg object-contain flex-shrink-0 bg-white/[0.05]"
          />
        ) : (
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0
              text-[10px] font-bold text-white"
            style={{ background: 'linear-gradient(135deg, #C4962A, #9a6e1a)' }}
          >
            {tenantName?.[0]?.toUpperCase() || 'T'}
          </div>
        )}
        
        <div className="min-w-0">
          <div className="text-[12px] font-medium text-white/90 truncate">{tenantName}</div>
          <div className="text-[9px] font-semibold font-mono text-gold bg-gold/[0.15] px-1.5 py-0.5 rounded-full w-fit mt-0.5">
            ◆ {tenantInfo?.subscription_plan || 'Pro'}
          </div>
        </div>

        {/* Logo upload button - visible on hover for admin only */}
        {canUploadLogo && (
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="opacity-0 group-hover:opacity-100 transition-opacity ml-auto flex-shrink-0
              text-white/40 hover:text-white/70 disabled:opacity-50 cursor-pointer"
            title="Changer le logo"
          >
            <Upload className="w-3.5 h-3.5" />
          </motion.button>
        )}

        {/* Hidden file input for logo upload */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp,image/svg+xml"
          onChange={handleLogoChange}
          disabled={uploading}
          className="hidden"
          aria-label="Upload tenant logo"
        />

        {/* Dropdown arrow */}
        <ChevronRight className="w-3.5 h-3.5 text-white/25 ml-auto flex-shrink-0" />
      </div>

      {/* Error message */}
      {error && (
        <div className="mx-3 mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded text-[10px] text-red-300">
          {error}
        </div>
      )}

      {/* Main nav */}
      <div className="mt-4 px-2">
        <p className="px-2 pb-1 text-[9px] font-semibold tracking-[0.1em] uppercase text-white/20">
          Navigation
        </p>
        {mainNav.map((item) => {
          const active = pathname === item.href
          const Icon = item.icon
          return (
            <motion.div
              key={item.href}
              whileHover={{ x: 2 }}
              transition={{ duration: 0.15 }}
              onClick={() => router.push(item.href)}
              className={cn(
                'flex items-center gap-2.5 px-2.5 py-2 rounded-lg mb-0.5 cursor-pointer text-[12.5px] transition-colors',
                active
                  ? 'bg-gold/[0.13] text-gold-2 font-medium'
                  : 'text-white/42 hover:bg-white/[0.055] hover:text-white/80'
              )}
            >
              <Icon className="w-[14px] h-[14px] flex-shrink-0 opacity-80" />
              <span className="flex-1 truncate">{item.label}</span>
              {item.badge && (
                <span
                  className={cn(
                    'text-[9.5px] font-semibold font-mono px-1.5 py-0.5 rounded-full',
                    item.badgeVariant === 'gold' && 'bg-gold/[0.18] text-gold',
                    item.badgeVariant === 'green' && 'bg-green-500/15 text-green-400'
                  )}
                >
                  {item.badge}
                </span>
              )}
            </motion.div>
          )
        })}
      </div>

      {/* Config nav */}
      <div className="mt-3 px-2">
        <p className="px-2 pb-1 text-[9px] font-semibold tracking-[0.1em] uppercase text-white/20">
          Configuration
        </p>
        {configNav.map((item) => {
          const Icon = item.icon
          return (
            <motion.div
              key={item.href}
              whileHover={{ x: 2 }}
              transition={{ duration: 0.15 }}
              onClick={() => router.push(item.href)}
              className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg mb-0.5 cursor-pointer
                text-[12.5px] text-white/35 hover:bg-white/[0.055] hover:text-white/70 transition-colors"
            >
              <Icon className="w-[14px] h-[14px] flex-shrink-0 opacity-70" />
              <span>{item.label}</span>
            </motion.div>
          )
        })}
      </div>

      <div className="flex-1" />

      {/* Status */}
      <div className="mx-3 mb-2 p-2 bg-green-500/[0.06] border border-green-500/[0.11] rounded-lg flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse flex-shrink-0" />
        <span className="text-[10px] font-mono text-white/30 flex-1">
          Tous systèmes opérationnels
        </span>
        <span className="text-[10px] font-semibold font-mono text-green-400">OK</span>
      </div>

      {/* User */}
      <div className="p-2.5 border-t border-white/[0.06] flex items-center gap-2.5">
        <div
          className="w-[30px] h-[30px] rounded-lg flex items-center justify-center flex-shrink-0
            text-[10px] font-bold text-white"
          style={{ background: 'linear-gradient(135deg, #C4962A, #9a6e1a)' }}
        >
          {user?.full_name?.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2) || 'U'}
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-[12px] font-medium text-white/84 truncate">
            {user?.full_name || 'User'}
          </div>
          <div className="text-[9px] font-mono text-gold uppercase">
            {userRole || 'USER'}
          </div>
        </div>
        <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}>
          <Settings className="w-[14px] h-[14px] text-white/25 hover:text-white/50 transition-colors" />
        </motion.button>
      </div>
    </aside>
  )
}
