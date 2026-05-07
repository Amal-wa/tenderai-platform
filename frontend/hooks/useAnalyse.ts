'use client'

import { useState, useCallback } from 'react'
import type { AnalyseStats, AnalyseRequest, AnalyseResult, AnalyseHistoryItem } from '@/types/analyse'
import type { TenderDocument } from '@/types/documents'

export function useAnalyse() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = useCallback(async (): Promise<AnalyseStats | null> => {
    return null
  }, [])

  const fetchTenders = useCallback(async () => {
    return { items: [] as TenderDocument[], total: 0 }
  }, [])

  const runAnalyse = useCallback(async (_payload: AnalyseRequest): Promise<AnalyseResult | null> => {
    setLoading(true)
    try {
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchHistory = useCallback(async (): Promise<AnalyseHistoryItem[]> => {
    return []
  }, [])

  const fetchAnalyseById = useCallback(async (_id: string): Promise<AnalyseResult | null> => {
    return null
  }, [])

  const exportAnalyse = useCallback(async (_id: string): Promise<void> => {
    window.print()
  }, [])

  const uploadDocument = useCallback(async (file: File, idempotencyKey: string) => {
    setLoading(true)
    try {
      return {
        id: 'uploaded-' + idempotencyKey,
        tenant_id: '',
        document_url: '',
        filename: file.name,
        file_size: file.size,
        mime_type: file.type,
        language: 'FR',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        status: 'ready' as const,
        document_metadata: {},
        uploaded_by: 'user',
        download_url: null,
      }
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    loading,
    error,
    setError,
    fetchStats,
    fetchTenders,
    runAnalyse,
    fetchHistory,
    fetchAnalyseById,
    exportAnalyse,
    uploadDocument,
  }
}
