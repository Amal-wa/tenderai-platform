/**
 * types/documents.ts — Document and Tender type definitions
 * Mirrors backend DocumentResponse, DocumentStatsResponse from schemas.py
 */

export type DocumentStatus = 'uploaded' | 'processing' | 'completed' | 'error' | 'ready'

export interface DocumentMetadata {
  compliance_score?: number
  budget_eur?: number
  deadline?: string
  ref?: string
  sector?: string
  status_label?: string
  [key: string]: any
}

export interface TenderDocument {
  id: string
  tenant_id: string
  filename: string
  file_size: number | null
  mime_type: string | null
  language: string | null
  status: DocumentStatus
  document_metadata: DocumentMetadata
  uploaded_by: string | null
  created_by?: string | null
  is_deleted?: boolean
  created_at: string
  updated_at: string
  download_url: string | null
}

export interface DocumentsResponse {
  items: TenderDocument[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface DocumentStatsResponse {
  total: number
  completed: number
  processing: number
  avg_score: number | null
  total_budget_eur: number | null
  next_deadline: {
    ref?: string
    deadline?: string
    days_remaining?: number
  } | null
}

export interface DocumentDeleteResponse {
  id: string
  filename: string
  deleted_at: string
  deleted_by: string
  reason?: string | null
  message: string
}

/**
 * Upload response mirrors DocumentResponse
 */
export interface DocumentUploadResponse extends TenderDocument {}
