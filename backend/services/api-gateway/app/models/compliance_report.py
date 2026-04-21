# ==============================================================================
# MODEL: COMPLIANCE REPORT -  Rapports de conformité
# ==============================================================================

from uuid import uuid4
from sqlalchemy import Column, String, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import TenantModel


class ComplianceReport(TenantModel):
    """
    Modèle pour les rapports de conformité
    """
    
    __tablename__ = "compliance_reports"
    
    # ==========================================================================
    #  IDENTIFICATION
    # ==========================================================================
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Identifiant unique du rapport de conformité"
    )
    # `tenant_id` vient de TenantModel (hérité)
    # `created_at` et `updated_at` viennent de TenantModel (hérité)
    
    # ==========================================================================
    #  RELATIONS
    # ==========================================================================
    
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Document analysé (parent)"
    )
    # CASCADE = Si document supprimé, le rapport est aussi supprimé
    
    # ==========================================================================
    #  RÉSULTATS DE CONFORMITÉ
    # ==========================================================================
    
    summary = Column(
        JSONB,
        nullable=True,
        default=dict,
        server_default="'{}'::jsonb",
        comment="Résumé des résultats: total_checks, passed, failed, warnings"
    )
    
    
    findings = Column(
        JSONB,
        nullable=True,
        default=list,
        server_default="'[]'::jsonb",
        comment="Array de findings détaillées (violations, warnings, etc.)"
    )
   
    
    compliance_score = Column(
        Float,
        nullable=True,
        comment="Score de conformité (0.0 = non-conforme, 100.0 = conforme)"
    )
    
    
    status = Column(
        String(50),
        nullable=False,
        default="pending",
        comment="Workflow: pending → completed (ou error)"
    )
    
    
    generated_by = Column(
        String(100),
        nullable=True,
        comment="Système/Engine qui a généré le rapport (ex: 'compliance_engine_v2.1')"
    )
   
    # ==========================================================================
    #  MÉTADONNÉES FLEXIBLES
    # ==========================================================================
    
    custom_metadata = Column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        server_default="'{}'::jsonb",
        comment="Custom metadata: engine_version, rules_version, processing_time_ms"
    )
   
