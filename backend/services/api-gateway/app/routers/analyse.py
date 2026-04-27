# ==============================================================================
# ROUTERS/ANALYSE.PY — Analyse IA Routes
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Optional
from uuid import UUID

from ..database import get_db, set_tenant_context
from ..auth import get_current_user
from ..core.middleware import ensure_tenant_context
from ..models import User, ComplianceReport, Document
from ..schemas import (
    AnalyseStatsResponse, 
    AnalyseRequestSchema,
    AnalyseResultResponse,
    AnalyseHistoryItemResponse,
    PaginatedResponse,
    DocumentResponse
)

router = APIRouter(prefix="/api/v1", tags=["Analyse"])


# ==============================================================================
# GET /api/v1/tenders — Lister les appels d'offres disponibles
# ==============================================================================

@router.get("/tenders", response_model=dict)
async def list_tenders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(ensure_tenant_context),
):
    """
    Liste les appels d'offres (tenders) disponibles pour l'utilisateur.
    Retourne les documents du tenant.
    """
    
    set_tenant_context(db, user.tenant_id)
    
    query = db.query(Document).filter(
        and_(
            Document.tenant_id == user.tenant_id,
            ~Document.is_deleted,
        )
    )
    
    total = query.count()
    offset = (page - 1) * limit
    items = query.order_by(desc(Document.created_at)).offset(offset).limit(limit).all()
    
    return {
        "items": [DocumentResponse.model_validate(d) for d in items],
        "total": total,
        "page": page,
        "page_size": limit,
        "pages": (total + limit - 1) // limit if limit else 1,
    }


# ==============================================================================
# GET /api/v1/analyse/stats — Récupérer les statistiques d'analyse
# ==============================================================================

@router.get("/analyse/stats", response_model=AnalyseStatsResponse)
async def get_analyse_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    __: None = Depends(ensure_tenant_context),
):
    """
    Récupère les statistiques d'analyse du mois/trimestre courant.
    Accessible par: superadmin, admin, manager, analyst
    """
    
    # Récupérer les rapports de conformité de l'utilisateur/tenant
    total_reports = db.query(ComplianceReport).count()
    
    # Statistiques dummy pour le moment
    return AnalyseStatsResponse(
        total_analysed=1,
        avg_conformite=0,
        hours_saved=1840,
        success_rate=0,
        delta_analysed=0,
        delta_conformite=0,
        delta_success_rate=27,  # "Win rate +27pts vs concurrence"
    )


# ==============================================================================
# POST /api/v1/analyse/run — Lancer une analyse
# ==============================================================================

@router.post("/analyse/run", response_model=AnalyseResultResponse)
async def run_analyse(
    payload: AnalyseRequestSchema,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(ensure_tenant_context),
):
    """
    Lance une analyse IA sur un appel d'offres ou document.
    
    Scopes disponibles: ['criteres', 'risques', 'reponse', 'score']
    Types: 'conformite' | 'technique' | 'financier' | 'complet'
    Langues: 'FR' | 'AR' | 'EN'
    """
    
    # Placeholder: returner un résultat dummy
    return AnalyseResultResponse(
        id="dummy-analyse-1",
        score_conformite=0,
        score_technique=0,
        score_risque=0,
        resume="Analyse en cours de développement",
        criteres_manquants=[],
        risques=[],
        reponse_generee="",
        recommandations=[],
        created_at="2026-04-27T00:00:00Z",
    )


# ==============================================================================
# GET /api/v1/analyse/history — Historique d'analyses
# ==============================================================================

@router.get("/analyse/history", response_model=List[AnalyseHistoryItemResponse])
async def get_analyse_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(ensure_tenant_context),
):
    """
    Récupère l'historique des analyses de l'utilisateur.
    """
    
    # Placeholder: returner une liste vide
    return []


# ==============================================================================
# GET /api/v1/analyse/{id} — Récupérer une analyse
# ==============================================================================

@router.get("/analyse/{analyse_id}", response_model=AnalyseResultResponse)
async def get_analyse(
    analyse_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(ensure_tenant_context),
):
    """
    Récupère les résultats d'une analyse spécifique.
    """
    
    # Placeholder
    return AnalyseResultResponse(
        id=analyse_id,
        score_conformite=0,
        score_technique=0,
        score_risque=0,
        resume="Analyse",
        criteres_manquants=[],
        risques=[],
        reponse_generee="",
        recommandations=[],
        created_at="2026-04-27T00:00:00Z",
    )


# ==============================================================================
# GET /api/v1/analyse/{id}/export — Exporter une analyse en PDF
# ==============================================================================

@router.get("/analyse/{analyse_id}/export")
async def export_analyse(
    analyse_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: None = Depends(ensure_tenant_context),
):
    """
    Exporte les résultats d'une analyse en PDF.
    """
    
    # Placeholder: returner un dummy PDF
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Export PDF non encore implémenté"
    )
