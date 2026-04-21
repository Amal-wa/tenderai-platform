'use client'

import { useState, useEffect, useRef, useCallback, forwardRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Download, Trash2, Upload, TrendingUp, Clock, AlertCircle, ChevronDown,
  Search, FileText, CheckCircle, AlertTriangle,
} from 'lucide-react'
import { getDocuments, getDocument, getDocumentStats, deleteDocument, uploadDocument, extractErrorMessage, downloadDocument } from '@/lib/api'
import { formatTND, formatPct, formatDate, daysRemaining } from '@/lib/formatters'
import type { TenderDocument, DocumentStatsResponse } from '@/types/documents'
import type { UserProfile } from '@/types/auth'

/**
 * TendersClient — Main component for "Mes appels d'offres" page
 * Handles document listing, filtering, uploading, and management
 */
export default function TendersClient() {
  // ─────────────────────────────────────────────────────────────────
  // STATE MANAGEMENT
  // ─────────────────────────────────────────────────────────────────
  const [user, setUser] = useState<UserProfile | null>(null)
  const [documents, setDocuments] = useState<TenderDocument[]>([])
  const [stats, setStats] = useState<DocumentStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Upload state
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [uploadError, setUploadError] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Filters
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'date' | 'score'>('date')

  // Pagination
  const page = 1

  // Delete confirmation
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  // Drag & drop
  const [dragActive, setDragActive] = useState(false)
  const dropZoneRef = useRef<HTMLDivElement>(null)

  // ─────────────────────────────────────────────────────────────────
  // INITIAL DATA LOADING
  // ─────────────────────────────────────────────────────────────────
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError('')

        // Load user from localStorage (set by AuthContext)
        const userStr = localStorage.getItem('user')
        if (userStr) {
          setUser(JSON.parse(userStr))
        }

        // ALWAYS load ALL documents (no filter on first load)
        // This ensures newly uploaded documents are visible even if they're still 'uploaded' status
        const [docsRes, statsRes] = await Promise.all([
          getDocuments({ page: 1 }), // Load ALL, we'll filter client-side
          getDocumentStats(),
        ])

        setDocuments((docsRes as any)?.items || [])
        setStats((statsRes as DocumentStatsResponse) || null)
      } catch (err) {
        setError(extractErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [page])

  // ─────────────────────────────────────────────────────────────────
  // FILTERING & SORTING LOGIC
  // ─────────────────────────────────────────────────────────────────
  const filteredDocuments = documents
    .filter(doc => {
      // Apply status filter client-side
      if (statusFilter !== 'all' && doc.status !== statusFilter) {
        return false
      }
      // Search by filename (case-insensitive)
      if (searchQuery && !doc.filename.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false
      }
      return true
    })
    .sort((a, b) => {
      if (sortBy === 'score') {
        const scoreA = a.document_metadata?.compliance_score ?? 0
        const scoreB = b.document_metadata?.compliance_score ?? 0
        return scoreB - scoreA
      } else {
        // Sort by date DESC (newest first)
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      }
    })

  // ─────────────────────────────────────────────────────────────────
  // UPLOAD HANDLERS
  // ─────────────────────────────────────────────────────────────────
  const handleUpload = useCallback(async (files: FileList) => {
    if (!files.length) return

    const file = files[0]

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/plain',
    ]

    if (!allowedTypes.includes(file.type)) {
      setUploadState('error')
      setUploadError('Format non supporté. Acceptez: PDF, DOCX, XLS, XLSX, TXT')
      setTimeout(() => {
        setUploadState('idle')
        setUploadError('')
      }, 4000)
      return
    }

    // Check file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      setUploadState('error')
      setUploadError('Le fichier dépasse 50 MB')
      setTimeout(() => {
        setUploadState('idle')
        setUploadError('')
      }, 4000)
      return
    }

    try {
      setUploadState('uploading')
      setUploadError('')
      setUploadProgress(0)

      // Upload document
      const response = await uploadDocument(file)
      const newDoc: TenderDocument = response

      // Add to documents list immediately
      setDocuments(prev => [newDoc, ...prev])
      setUploadState('success')
      setUploadProgress(100)

      // Poll for status change
      let attempts = 0
      const maxAttempts = 100 // 5 minutes at 3s intervals

      const pollInterval = setInterval(async () => {
        attempts++
        if (attempts > maxAttempts) {
          clearInterval(pollInterval)
          return
        }

        try {
          const updatedDoc = await getDocument(newDoc.id)
          
          if (updatedDoc && (updatedDoc as TenderDocument).status !== 'uploaded') {
            // Document status changed in backend, update it in the list
            setDocuments(prev => 
              prev.map(d => d.id === newDoc.id ? (updatedDoc as TenderDocument) : d)
            )
            clearInterval(pollInterval)
          }
        } catch (err) {
          console.error('Poll error:', err)
        }
      }, 3000)

      // Reset upload state after brief success
      setTimeout(() => {
        setUploadState('idle')
        setUploadProgress(0)
      }, 2000)

      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err) {
      setUploadState('error')
      setUploadError(extractErrorMessage(err))
      setTimeout(() => {
        setUploadState('idle')
        setUploadError('')
      }, 4000)
    }
  }, [])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files) {
      handleUpload(e.dataTransfer.files)
    }
  }

  // ─────────────────────────────────────────────────────────────────
  // DELETE HANDLER
  // ─────────────────────────────────────────────────────────────────
  const handleDelete = async (docId: string) => {
    try {
      setDeleting(true)
      await deleteDocument(docId)

      // Remove from list
      setDocuments(prev => prev.filter(d => d.id !== docId))
      setDeleteConfirmId(null)

      // Refresh stats
      const statsRes = await getDocumentStats()
      setStats((statsRes as DocumentStatsResponse) || null)
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setDeleting(false)
    }
  }

  // ─────────────────────────────────────────────────────────────────
  // DOWNLOAD HANDLER
  // ─────────────────────────────────────────────────────────────────
  const handleDownload = async (doc: TenderDocument) => {
    try {
      await downloadDocument(doc.id)
    } catch (err) {
      setError(extractErrorMessage(err))
    }
  }

  // ─────────────────────────────────────────────────────────────────
  // RENDER HELPERS
  // ─────────────────────────────────────────────────────────────────
  const isAdmin = user?.role === 'superadmin' || user?.role === 'admin'

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready':
      case 'completed':
        return {
          label: 'Prêt',
          bgColor: 'bg-green-50',
          textColor: 'text-green-700',
          dotColor: 'bg-green-400',
        }
      case 'uploaded':
      case 'processing':
        return {
          label: 'En traitement',
          bgColor: 'bg-amber-50',
          textColor: 'text-amber-700',
          dotColor: 'bg-amber-400',
        }
      case 'error':
        return {
          label: 'Erreur',
          bgColor: 'bg-red-50',
          textColor: 'text-red-700',
          dotColor: 'bg-red-400',
        }
      default:
        return {
          label: status,
          bgColor: 'bg-gray-50',
          textColor: 'text-gray-700',
          dotColor: 'bg-gray-400',
        }
    }
  }

  const getComplianceColor = (score: number | undefined) => {
    if (!score) return 'bg-gray-200'
    if (score >= 80) return 'bg-green-400'
    if (score >= 50) return 'bg-amber-400'
    return 'bg-red-400'
  }

  // ─────────────────────────────────────────────────────────────────
  // RENDERING
  // ─────────────────────────────────────────────────────────────────
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* TOPBAR */}
      <header className="bg-white border-b border-[#E5E0D8] h-14 px-7 sticky top-0 z-20 flex items-center justify-between">
        <div>
          <p className="text-[11px] text-[#9B9590] font-medium">Mon espace</p>
          <h1 className="font-heading text-[17px] font-bold text-[#0F1C35]">Mes Appels d'offres</h1>
        </div>
        <button className="flex items-center gap-2 bg-[#C4962A] text-white text-xs font-bold px-4 py-2 rounded-lg hover:bg-[#d4a93c] transition"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={14} />
          Importer un PDF
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.xlsx,.xls,.txt"
          className="hidden"
          onChange={(e) => handleUpload(e.target.files!)}
        />
      </header>

      {/* MAIN CONTENT */}
      <div className="flex-1 overflow-auto bg-[#F5F3EE] px-7 py-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="space-y-6"
        >
          {/* ERROR BANNER */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center gap-3"
            >
              <AlertCircle size={18} />
              <p className="text-sm">{error}</p>
            </motion.div>
          )}

          {/* KPI CARDS */}
          {stats && (
            <motion.div
              className="grid grid-cols-1 md:grid-cols-4 gap-4"
              initial="hidden"
              animate="visible"
              variants={{
                hidden: {},
                visible: {
                  transition: { staggerChildren: 0.1 },
                },
              }}
            >
              {/* Total AOs */}
              <motion.div
                variants={{
                  hidden: { opacity: 0, y: 10 },
                  visible: { opacity: 1, y: 0 },
                }}
                className="bg-white border border-[#E5E0D8] rounded-[14px] p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-[9px] bg-[#FFF0E5] flex items-center justify-center">
                    <FileText size={18} className="text-[#C4962A]" />
                  </div>
                  <div>
                    <p className="text-[22px] font-extrabold font-heading text-[#0F1C35]">
                      {stats.total}
                    </p>
                    <p className="text-[11px] text-[#6B6560]">Total AOs</p>
                  </div>
                </div>
              </motion.div>

              {/* En cours */}
              <motion.div
                variants={{
                  hidden: { opacity: 0, y: 10 },
                  visible: { opacity: 1, y: 0 },
                }}
                className="bg-white border border-[#E5E0D8] rounded-[14px] p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-[9px] bg-[#FEF3C7] flex items-center justify-center">
                    <Clock size={18} className="text-[#FB923C]" />
                  </div>
                  <div>
                    <p className="text-[22px] font-extrabold font-heading text-[#0F1C35]">
                      {stats.processing}
                    </p>
                    <p className="text-[11px] text-[#6B6560]">En cours</p>
                  </div>
                </div>
              </motion.div>

              {/* Score de conformité */}
              <motion.div
                variants={{
                  hidden: { opacity: 0, y: 10 },
                  visible: { opacity: 1, y: 0 },
                }}
                className="bg-white border border-[#E5E0D8] rounded-[14px] p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-[9px] bg-[#DBEAFE] flex items-center justify-center">
                    <TrendingUp size={18} className="text-[#3B82F6]" />
                  </div>
                  <div>
                    <p className="text-[22px] font-extrabold font-heading text-[#0F1C35]">
                      {formatPct(stats.avg_score)}
                    </p>
                    <p className="text-[11px] text-[#6B6560]">Conformité moy.</p>
                  </div>
                </div>
              </motion.div>

              {/* Budget total */}
              <motion.div
                variants={{
                  hidden: { opacity: 0, y: 10 },
                  visible: { opacity: 1, y: 0 },
                }}
                className="bg-white border border-[#E5E0D8] rounded-[14px] p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-[9px] bg-[#E0E7FF] flex items-center justify-center">
                    <CheckCircle size={18} className="text-[#6366F1]" />
                  </div>
                  <div>
                    <p className="text-[22px] font-extrabold font-heading text-[#0F1C35] truncate">
                      {formatTND(stats.total_budget_eur)}
                    </p>
                    <p className="text-[11px] text-[#6B6560]">Budget total</p>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}

          {/* UPLOAD ZONE */}
          {documents.length === 0 && !loading ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <UploadZone
                dragActive={dragActive}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                ref={dropZoneRef}
                uploadState={uploadState}
                uploadError={uploadError}
                uploadProgress={uploadProgress}
                onFileInputClick={() => fileInputRef.current?.click()}
              />
            </motion.div>
          ) : (
            <>
              {/* UPLOAD ZONE (ABOVE TABLE) */}
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                <UploadZone
                  dragActive={dragActive}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  ref={dropZoneRef}
                  uploadState={uploadState}
                  uploadError={uploadError}
                  uploadProgress={uploadProgress}
                  onFileInputClick={() => fileInputRef.current?.click()}
                  compact
                />
              </motion.div>

              {/* FILTERS & CONTROLS */}
              <div className="flex gap-3 items-center justify-between">
                <div className="flex-1 flex gap-3">
                  {/* Search */}
                  <div className="relative flex-1 max-w-xs">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9B9590]" />
                    <input
                      type="text"
                      placeholder="Rechercher..."
                      className="w-full pl-9 pr-3 py-2 border border-[#E5E0D8] rounded-lg text-sm bg-white placeholder-[#9B9590] focus:outline-none focus:ring-2 focus:ring-[#C4962A]"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>

                  {/* Status Filter */}
                  <div className="relative">
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="pl-3 pr-8 py-2 border border-[#E5E0D8] rounded-lg text-sm bg-white cursor-pointer appearance-none focus:outline-none focus:ring-2 focus:ring-[#C4962A]"
                    >
                      <option value="all">Tous les statuts</option>
                      <option value="uploaded">En traitement</option>
                      <option value="ready">Prêt</option>
                      <option value="error">Erreur</option>
                    </select>
                    <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 text-[#9B9590] pointer-events-none" />
                  </div>

                  {/* Sort */}
                  <div className="relative">
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value as 'date' | 'score')}
                      className="pl-3 pr-8 py-2 border border-[#E5E0D8] rounded-lg text-sm bg-white cursor-pointer appearance-none focus:outline-none focus:ring-2 focus:ring-[#C4962A]"
                    >
                      <option value="date">Par date</option>
                      <option value="score">Par conformité</option>
                    </select>
                    <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 text-[#9B9590] pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* TABLE */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="bg-white border border-[#E5E0D8] rounded-lg overflow-hidden"
              >
                <table className="w-full">
                  <thead className="bg-[#F5F3EE] border-b border-[#E5E0D8]">
                    <tr className="text-xs font-semibold text-[#6B6560] uppercase">
                      <th className="px-4 py-3 text-left">Appel d'offres</th>
                      <th className="px-4 py-3 text-left">Secteur</th>
                      <th className="px-4 py-3 text-left">Statut</th>
                      <th className="px-4 py-3 text-left">Conformité</th>
                      <th className="px-4 py-3 text-left">Échéance</th>
                      <th className="px-4 py-3 text-left">Budget</th>
                      <th className="px-4 py-3 text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E5E0D8]">
                    <AnimatePresence>
                      {filteredDocuments.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="px-4 py-8 text-center text-[#9B9590]">
                            <div className="flex flex-col items-center gap-2">
                              <FileText size={24} className="opacity-50" />
                              <p className="text-sm">Aucun document trouvé</p>
                            </div>
                          </td>
                        </tr>
                      ) : (
                        filteredDocuments.map((doc, idx) => {
                          const status = getStatusBadge(doc.status)
                          const complianceScore = doc.document_metadata?.compliance_score
                          const deadline = doc.document_metadata?.deadline
                          const daysLeft = deadline ? daysRemaining(deadline) : null
                          const isUrgent = daysLeft !== null && daysLeft < 7

                          return (
                            <motion.tr
                              key={doc.id}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, x: -100 }}
                              transition={{ duration: 0.2, delay: idx * 0.05 }}
                              className="hover:bg-[#F9F8F6] transition-colors text-sm"
                            >
                              {/* Filename + Ref */}
                              <td className="px-4 py-3">
                                <div>
                                  <p className="font-semibold text-[#0F1C35]">{doc.filename}</p>
                                  {doc.document_metadata?.ref && (
                                    <p className="text-xs text-[#9B9590]">{doc.document_metadata.ref}</p>
                                  )}
                                </div>
                              </td>

                              {/* Sector */}
                              <td className="px-4 py-3">
                                {doc.document_metadata?.sector ? (
                                  <span className="text-xs font-medium text-[#6B6560] bg-[#F5F3EE] px-2 py-1 rounded">
                                    {doc.document_metadata.sector}
                                  </span>
                                ) : (
                                  <span className="text-xs text-[#9B9590]">—</span>
                                )}
                              </td>

                              {/* Status */}
                              <td className="px-4 py-3">
                                <div className={`inline-flex items-center gap-2 px-2 py-1 rounded-full text-xs font-medium ${status.bgColor} ${status.textColor}`}>
                                  <span className={`w-2 h-2 rounded-full ${status.dotColor}`} />
                                  {status.label}
                                </div>
                              </td>

                              {/* Compliance Score */}
                              <td className="px-4 py-3">
                                {complianceScore !== undefined ? (
                                  <div className="flex items-center gap-2">
                                    <div className="w-16 h-1.5 bg-[#E5E0D8] rounded-full overflow-hidden">
                                      <div
                                        className={`h-full ${getComplianceColor(complianceScore)}`}
                                        style={{ width: `${Math.min(complianceScore, 100)}%` }}
                                      />
                                    </div>
                                    <span className="text-xs font-semibold text-[#0F1C35]">{formatPct(complianceScore)}</span>
                                  </div>
                                ) : (
                                  <span className="text-xs text-[#9B9590]">—</span>
                                )}
                              </td>

                              {/* Deadline */}
                              <td className="px-4 py-3">
                                {deadline ? (
                                  <div>
                                    <p className="text-xs font-medium text-[#0F1C35]">{formatDate(deadline)}</p>
                                    {isUrgent && (
                                      <p className="text-xs font-semibold text-red-600 flex items-center gap-1 mt-1">
                                        <AlertTriangle size={12} />
                                        {daysLeft} j restants
                                      </p>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-xs text-[#9B9590]">—</span>
                                )}
                              </td>

                              {/* Budget */}
                              <td className="px-4 py-3">
                                <p className="text-sm font-semibold text-[#0F1C35]">
                                  {formatTND(doc.document_metadata?.budget_eur)}
                                </p>
                              </td>

                              {/* Actions */}
                              <td className="px-4 py-3">
                                <div className="flex items-center justify-center gap-2">
                                  <button
                                    onClick={() => handleDownload(doc)}
                                    className="p-1.5 hover:bg-[#F5F3EE] rounded-lg transition text-[#6B6560] hover:text-[#0F1C35]"
                                    aria-label="Télécharger"
                                    title="Télécharger"
                                  >
                                    <Download size={16} />
                                  </button>

                                  {isAdmin && (
                                    <div className="relative group">
                                      <button
                                        onClick={() => setDeleteConfirmId(deleteConfirmId === doc.id ? null : doc.id)}
                                        className="p-1.5 hover:bg-red-50 rounded-lg transition text-[#9B9590] hover:text-red-600"
                                        aria-label="Supprimer"
                                        title="Supprimer"
                                      >
                                        <Trash2 size={16} />
                                      </button>

                                      {/* Delete Confirmation Popover */}
                                      {deleteConfirmId === doc.id && (
                                        <motion.div
                                          initial={{ opacity: 0, scale: 0.9 }}
                                          animate={{ opacity: 1, scale: 1 }}
                                          exit={{ opacity: 0, scale: 0.9 }}
                                          className="absolute top-full right-0 mt-2 bg-white border border-[#E5E0D8] rounded-lg shadow-lg z-20 p-3 whitespace-nowrap"
                                        >
                                          <p className="text-xs text-[#6B6560] mb-2">Confirmer la suppression ?</p>
                                          <div className="flex gap-2">
                                            <button
                                              onClick={() => handleDelete(doc.id)}
                                              disabled={deleting}
                                              className="px-2 py-1 bg-red-600 text-white text-xs font-semibold rounded hover:bg-red-700 disabled:opacity-50 transition"
                                            >
                                              {deleting ? 'Suppression...' : 'Supprimer'}
                                            </button>
                                            <button
                                              onClick={() => setDeleteConfirmId(null)}
                                              className="px-2 py-1 bg-[#F5F3EE] text-[#0F1C35] text-xs font-semibold rounded hover:bg-[#EDE9E2] transition"
                                            >
                                              Annuler
                                            </button>
                                          </div>
                                        </motion.div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </td>
                            </motion.tr>
                          )
                        })
                      )}
                    </AnimatePresence>
                  </tbody>
                </table>
              </motion.div>
            </>
          )}
        </motion.div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────
// UPLOAD ZONE COMPONENT
// ─────────────────────────────────────────────────────────────────
interface UploadZoneProps {
  dragActive: boolean
  onDragOver: (e: React.DragEvent) => void
  onDragLeave: (e: React.DragEvent) => void
  onDrop: (e: React.DragEvent) => void
  uploadState: 'idle' | 'uploading' | 'success' | 'error'
  uploadError: string
  uploadProgress: number
  onFileInputClick: () => void
  compact?: boolean
}

const UploadZone = forwardRef<HTMLDivElement, UploadZoneProps>(
  (
    {
      dragActive,
      onDragOver,
      onDragLeave,
      onDrop,
      uploadState,
      uploadError,
      uploadProgress,
      onFileInputClick,
      compact = false,
    },
    ref
  ) => {
    return (
      <motion.div
        ref={ref}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        animate={{
          borderColor: dragActive ? '#C4962A' : '#E5E0D8',
          backgroundColor: dragActive ? '#FFFAF5' : '#FFFFFF',
        }}
        transition={{ duration: 0.2 }}
        className={`border-2 border-dashed rounded-lg transition-all ${
          compact ? 'p-4' : 'p-12'
        } ${uploadState === 'uploading' ? 'cursor-not-allowed opacity-75' : 'cursor-pointer'}`}
      >
        <div className={`text-center ${compact ? 'space-y-2' : 'space-y-4'}`}>
          {uploadState === 'idle' || uploadState === 'success' ? (
            <>
              <Upload className={`mx-auto ${compact ? 'w-6 h-6' : 'w-8 h-8'} text-[#C4962A]`} />
              <div>
                <p
                  className={`font-semibold text-[#0F1C35] ${compact ? 'text-sm' : 'text-base'}`}
                  onClick={onFileInputClick}
                >
                  Glissez votre AO ici ou <span className="text-[#C4962A] cursor-pointer hover:underline">cliquez pour sélectionner</span>
                </p>
                <p className={`text-[#9B9590] ${compact ? 'text-xs' : 'text-sm'}`}>
                  PDF · DOCX · XLS · Texte brut
                </p>
              </div>
            </>
          ) : uploadState === 'uploading' ? (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                className="mx-auto"
              >
                <Upload className={`${compact ? 'w-6 h-6' : 'w-8 h-8'} text-[#C4962A]`} />
              </motion.div>
              <div>
                <p className={`font-semibold text-[#0F1C35] ${compact ? 'text-sm' : 'text-base'}`}>
                  Téléchargement en cours...
                </p>
                <div className={`w-full ${compact ? 'h-1' : 'h-2'} bg-[#E5E0D8] rounded-full mt-2 overflow-hidden`}>
                  <motion.div
                    className="bg-[#C4962A] h-full"
                    animate={{ width: `${uploadProgress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </div>
            </>
          ) : uploadState === 'error' ? (
            <>
              <AlertTriangle className={`mx-auto ${compact ? 'w-6 h-6' : 'w-8 h-8'} text-red-500`} />
              <div>
                <p className={`font-semibold text-red-700 ${compact ? 'text-sm' : 'text-base'}`}>
                  {uploadError || 'Erreur lors du téléchargement'}
                </p>
              </div>
            </>
          ) : (
            <>
              <CheckCircle className={`mx-auto ${compact ? 'w-6 h-6' : 'w-8 h-8'} text-green-500`} />
              <p className={`font-semibold text-green-700 ${compact ? 'text-sm' : 'text-base'}`}>
                Document ajouté avec succès !
              </p>
            </>
          )}
        </div>
      </motion.div>
    )
  }
)

UploadZone.displayName = 'UploadZone'
