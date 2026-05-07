'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { LayoutDashboard, FileText, Shield } from 'lucide-react'

const adminNavItems = [
  { label: 'Dashboard', href: '/dashboard/admin', icon: LayoutDashboard },
  { label: 'Audit & Sécurité', href: '/dashboard/admin/audit', icon: FileText },
]

export default function AdminNav() {
  const pathname = usePathname()
  const { user } = useAuth()

  // Vérifier que l'utilisateur est admin/superadmin
  const userRole = typeof user?.role === 'string' ? user?.role : user?.role?.name
  const isAdmin = userRole === 'admin' || userRole === 'superadmin' || userRole === 'system_admin'

  // Ne pas afficher le nav admin si pas admin
  if (!isAdmin) {
    return null
  }

  return (
    <div className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="px-6 flex items-center gap-2 h-14">
        <Shield className="w-5 h-5 text-amber-600" />
        <span className="text-sm font-semibold text-gray-900">Admin</span>
        <div className="flex gap-1 ml-4 border-l border-gray-200 pl-4">
          {adminNavItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`)
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-amber-50 text-amber-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}
