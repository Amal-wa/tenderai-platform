# ==============================================================================
# MODEL: PROPOSAL - Propositions générées à partir de documents
# ==============================================================================


from uuid import uuid4
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import TenantModel


class Proposal(TenantModel):
    """
    Modèle pour les propositions générées
    
    """
    
    __tablename__ = "proposals"
    
    # ==========================================================================
    # 🆔 IDENTIFICATION
    # ==========================================================================
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Identifiant unique de la proposition"
    )
    # `tenant_id` vient de TenantModel (hérité)
    # `created_at` et `updated_at` viennent de TenantModel (hérité)
    
    # ==========================================================================
    # RELATIONS
    # ==========================================================================
    
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Document source (parent) dont la proposition est générée"
    )
    # CASCADE = Si document supprimé, la proposition est aussi supprimée
    
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User qui a créé la proposition (NULL si générée automatiquement par système)"
    )
    # SET NULL = Si user supprimé, on garde la trace que qq'un l'a créée
    
    # ==========================================================================
    # CONTENU
    # ==========================================================================
    
    title = Column(
        String(500),
        nullable=False,
        comment="Titre de la proposition (pour affichage dans l'UI)"
    )
    
    content = Column(
        Text,
        nullable=True,
        comment="Contenu texte de la proposition (Markdown ou HTML)"
    )
    
    
    storage_path = Column(
        String(500),
        nullable=True,
        comment="MinIO/S3 path du fichier exporté (PDF, DOCX, etc.)"
    )
    
    
    # ==========================================================================
    # STATUS & VERSIONING
    # ==========================================================================
    
    status = Column(
        String(50),
        nullable=False,
        default="draft",
        comment="Workflow: draft → edited → approved (ou rejected, exported)"
    )
  
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Numéro de version (1, 2, 3... pour suivi des modifications)"
    )
   
    # ==========================================================================
    # MÉTADONNÉES FLEXIBLES
    # ==========================================================================
    
    custom_metadata = Column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        server_default="'{}'::jsonb",
        comment="Custom metadata: llm_model, generation_time_ms, confidence, review_notes"
    )
   
    # ==========================================================================
    # SOFT DELETE
    # ==========================================================================
    
    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Soft-delete (suppression logique, restorable)"
    )
    
