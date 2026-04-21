'use client'

import { useEffect, useState } from 'react'
import { getAdminDashboard, extractErrorMessage } from '@/lib/api'
import AnalyticsDashboard from '@/components/dashboard/admin/AnalyticsDashboard'
import type { AdminDashboardResponse } from '@/types/dashboard'

export default function AdminPage() {
  const [data, setData] = useState<AdminDashboardResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true)
        const dashboardData = await getAdminDashboard()
        setData(dashboardData)
      } catch (err) {
        setError(extractErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
  }, [])

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <p className="font-semibold">Erreur</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    )
  }

  return <AnalyticsDashboard data={data} loading={loading} />
}
