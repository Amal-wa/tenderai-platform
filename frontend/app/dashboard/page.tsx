'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'

export default function DashboardRedirect() {
  const router = useRouter()
  
  useEffect(() => {
    api.get('/api/v1/auth/me')
      .then(res => {
        const role = !res.data.role ? 'viewer'
          : typeof res.data.role === 'string' ? res.data.role
          : res.data.role.name ?? 'viewer'
        if (['superadmin', 'admin'].includes(role)) {
          router.replace('/dashboard/admin')
        } else {
          router.replace('/dashboard/user')
        }
      })
      .catch(() => router.replace('/login'))
  }, [router])
  
  return null
}
