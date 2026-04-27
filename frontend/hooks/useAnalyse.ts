'use client'

import { useState, useCallback } from 'react'
import type { AnalyseStats, AnalyseRequest, AnalyseResult, AnalyseHistoryItem } from '@/types/analyse'
import type { TenderDocument } from '@/types/documents'

const MOCK_STATS: AnalyseStats = {
  total_analysed: 47,
  avg_conformite: 78,
  hours_saved: 1840,
  success_rate: 68,
  delta_analysed: 12,
  delta_conformite: 3,
  delta_success_rate: 27,
}

const MOCK_TENDERS: TenderDocument[] = [
  {
    id: 'ao-001',
    tenant_id: 'demo-tenant',
    filename: 'AO_Fournitures_Informatiques_2026.pdf',
    file_size: 2400000,
    mime_type: 'application/pdf',
    language: 'FR',
    status: 'ready',
    document_metadata: {},
    uploaded_by: 'system',
    created_at: '2026-04-15T09:00:00Z',
    updated_at: '2026-04-15T09:00:00Z',
    download_url: null,
  },
  {
    id: 'ao-002',
    tenant_id: 'demo-tenant',
    filename: 'Marche_Travaux_Genie_Civil_Lot2.pdf',
    file_size: 5100000,
    mime_type: 'application/pdf',
    language: 'FR',
    status: 'ready',
    document_metadata: {},
    uploaded_by: 'system',
    created_at: '2026-04-18T14:30:00Z',
    updated_at: '2026-04-18T14:30:00Z',
    download_url: null,
  },
  {
    id: 'ao-003',
    tenant_id: 'demo-tenant',
    filename: 'AO_Services_Maintenance_SI.docx',
    file_size: 1800000,
    mime_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    language: 'FR',
    status: 'ready',
    document_metadata: {},
    uploaded_by: 'system',
    created_at: '2026-04-20T11:15:00Z',
    updated_at: '2026-04-20T11:15:00Z',
    download_url: null,
  },
  {
    id: 'ao-004',
    tenant_id: 'demo-tenant',
    filename: 'Consultation_Audit_Securite_2026.pdf',
    file_size: 3200000,
    mime_type: 'application/pdf',
    language: 'FR',
    status: 'ready',
    document_metadata: {},
    uploaded_by: 'system',
    created_at: '2026-04-22T08:45:00Z',
    updated_at: '2026-04-22T08:45:00Z',
    download_url: null,
  },
  {
    id: 'ao-005',
    tenant_id: 'demo-tenant',
    filename: 'AO_Equipements_Medicaux_CHU.pdf',
    file_size: 4700000,
    mime_type: 'application/pdf',
    language: 'FR',
    status: 'ready',
    document_metadata: {},
    uploaded_by: 'system',
    created_at: '2026-04-24T16:00:00Z',
    updated_at: '2026-04-24T16:00:00Z',
    download_url: null,
  },
]

const MOCK_RESULT: AnalyseResult = {
  id: 'analyse-demo-001',
  score_conformite: 82,
  score_technique: 76,
  score_risque: 71,
  resume:
    "L'appel d'offres porte sur la fourniture et l'installation d'équipements informatiques pour le compte d'un organisme public. Le document présente une structure conforme aux exigences réglementaires en vigueur. Les critères d'attribution sont clairement définis avec une pondération technique/prix de 60/40. La date limite de soumission est fixée au 15 mai 2026 avec un délai d'exécution de 90 jours calendaires.",
  criteres_manquants: [
    'Attestation fiscale en cours de validité (moins de 3 mois)',
    'Références de projets similaires réalisés sur les 3 dernières années (minimum 3 références > 500K TND)',
    'Garantie bancaire provisoire équivalente à 1% du montant estimatif',
    'Certificat de capacité technique signé et cacheté',
  ],
  risques: [
    'Délai de réponse court — 14 jours ouvrables seulement, mobilisation immédiate requise',
    'Critère prix fortement pondéré (40%) avec variante basse possible — pression sur les marges',
    'Clause pénalités de retard élevée — 0,5% par jour calendaire de retard plafonné à 10%',
  ],
  reponse_generee:
    'Suite à la lecture attentive de votre appel d\'offres référencé AO/2026/047 portant sur la fourniture d\'équipements informatiques, notre société a le plaisir de soumettre sa candidature. Fort de notre expertise de plus de 10 ans dans le domaine des technologies de l\'information et de notre présence confirmée sur le marché tunisien, nous répondons à l\'ensemble des critères techniques et financiers requis. Notre proposition technique, jointe au présent dossier, détaille notre méthodologie d\'intervention, notre planning d\'exécution ainsi que nos références similaires auprès d\'organismes publics de même envergure. Notre engagement porte sur la qualité des équipements fournis, le respect strict des délais contractuels et un service après-vente réactif garanti 24/7. Nous restons à votre entière disposition pour tout complément d\'information ou pour une présentation de notre offre technique.',
  recommandations: [
    'Préparer l\'attestation fiscale en amont — délai d\'obtention minimum 72h auprès du receveur des finances',
    'Rassembler 3 références projets > 500K TND avec PV de réception définitive signés',
    'Réviser la marge commerciale — la pression prix est élevée, envisager une offre variante économique',
    'Prévoir une garantie bancaire provisoire dès maintenant auprès de votre banque',
  ],
  created_at: new Date().toISOString(),
}

const MOCK_HISTORY: AnalyseHistoryItem[] = [
  {
    id: 'h-001',
    file_name: 'AO_Fournitures_Informatiques_2026.pdf',
    created_at: '2026-04-24T10:30:00Z',
    type: 'complet',
    score_conformite: 82,
    lang: 'FR',
  },
  {
    id: 'h-002',
    file_name: 'Marche_Travaux_Genie_Civil_Lot2.pdf',
    created_at: '2026-04-22T14:15:00Z',
    type: 'conformite',
    score_conformite: 91,
    lang: 'FR',
  },
  {
    id: 'h-003',
    file_name: 'Consultation_Audit_Securite_2026.pdf',
    created_at: '2026-04-20T09:00:00Z',
    type: 'risques',
    score_conformite: 65,
    lang: 'FR',
  },
  {
    id: 'h-004',
    file_name: 'AO_Services_Maintenance_SI.docx',
    created_at: '2026-04-18T16:45:00Z',
    type: 'technique',
    score_conformite: 74,
    lang: 'FR',
  },
]

export function useAnalyse() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = useCallback(async (): Promise<AnalyseStats | null> => {
    await new Promise((r) => setTimeout(r, 600))
    return MOCK_STATS
  }, [])

  const fetchTenders = useCallback(async () => {
    await new Promise((r) => setTimeout(r, 400))
    return { items: MOCK_TENDERS, total: MOCK_TENDERS.length }
  }, [])

  const runAnalyse = useCallback(async (_payload: AnalyseRequest): Promise<AnalyseResult | null> => {
    setLoading(true)
    try {
      await new Promise((r) => setTimeout(r, 2500))
      return MOCK_RESULT
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchHistory = useCallback(async (): Promise<AnalyseHistoryItem[]> => {
    await new Promise((r) => setTimeout(r, 300))
    return MOCK_HISTORY
  }, [])

  const fetchAnalyseById = useCallback(async (_id: string): Promise<AnalyseResult | null> => {
    await new Promise((r) => setTimeout(r, 400))
    return MOCK_RESULT
  }, [])

  const exportAnalyse = useCallback(async (_id: string): Promise<void> => {
    await new Promise((r) => setTimeout(r, 500))
    window.print()
  }, [])

  const uploadDocument = useCallback(async (file: File, idempotencyKey: string) => {
    setLoading(true)
    try {
      await new Promise((r) => setTimeout(r, 800))
      return {
        id: 'uploaded-' + idempotencyKey,
        tenant_id: 'demo-tenant',
        document_url: '/mock/uploads/' + file.name,
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
