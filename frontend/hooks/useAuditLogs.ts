import { useEffect, useState } from 'react'
import { getAuditLogs, extractErrorMessage, type GetAuditLogsParams, type AuditLogsResponse } from '@/lib/api'

export type { GetAuditLogsParams }

interface UseAuditLogsReturn {
  logs: AuditLogsResponse['items']
  total: number
  page: number
  totalPages: number
  isLoading: boolean
  error: string | null
  refetch: (params: GetAuditLogsParams) => Promise<void>
}

export function useAuditLogs(params: GetAuditLogsParams): UseAuditLogsReturn {
  const [response, setResponse] = useState<AuditLogsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refetch = async (newParams: GetAuditLogsParams) => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await getAuditLogs(newParams)
      setResponse(data)
    } catch (err) {
      const errorMessage = extractErrorMessage(err)
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    refetch(params)
  }, [params.page, params.pageSize, params.action, params.resourceType, params.since, params.until, params.search])

  return {
    logs: response?.items || [],
    total: response?.total || 0,
    page: response?.page || params.page,
    totalPages: response?.pages || 1,
    isLoading,
    error,
    refetch,
  }
}
