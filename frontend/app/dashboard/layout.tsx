'use client'

import type { ReactNode } from 'react'
import { usePathname } from 'next/navigation'
import Sidebar from '@/components/dashboard/Sidebar'

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const isSettings = pathname?.startsWith('/dashboard/settings')

  return (
    <div className="flex min-h-screen bg-[var(--cream)]">
      {!isSettings && <Sidebar />}
      <div className="flex-1 flex flex-col overflow-hidden">
        {children}
      </div>
    </div>
  )
}
