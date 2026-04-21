# ==============================================================================
# MODEL: COMPANY ASSET - 📦 Ressources/Actifs de l'entreprise
# ==============================================================================

from uuid import uuid4
from sqlalchemy import Column, String, BigInteger, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from .base import TenantModel


class CompanyAsset(TenantModel):
    """
    Modèle pour les actifs/ressources de l'entreprise
    """
    
    __tablename__ = "company_asset"
    
    # ==========================================================================
    #  IDENTIFICATION
    # ==========================================================================
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Identifiant unique de l'actif"
    )
    
    
    # ==========================================================================
    #  CLASSIFICATION
    # ==========================================================================
    
    kind = Column(
        String(50),
        nullable=False,
        comment="Type d'actif: document, template, policy, code_list, guideline, other"
    )
    
    
    title = Column(
        Text,
        nullable=False,
        comment="Titre affichable de l'actif"
    )
   
    description = Column(
        Text,
        nullable=True,
        comment="Description longue (optionnel)"
    )
    
    # ==========================================================================
    # CONTENU
    # ==========================================================================
    
    content = Column(
        Text,
        nullable=True,
        comment="Contenu texte de l'actif (policy texte, template, JSON data, etc.)"
    )
    
    file_uri = Column(
        Text,
        nullable=True,
        comment="Chemin fichier cloud (S3/MinIO): s3://bucket/path/file.pdf"
    )
    
    # ==========================================================================
    # FILE METADATA
    # ==========================================================================
    
    file_type = Column(
        String(50),
        nullable=True,
        comment="MIME type: application/pdf, text/plain, image/png, etc."
    )
   
    file_size_bytes = Column(
        BigInteger,
        nullable=True,
        comment="Taille du fichier en bytes (pour quota et display)"
    )
   
    # ==========================================================================
    # TAGS & CATEGORIZATION
    # ==========================================================================
    
    tags = Column(
        ARRAY(String),
        nullable=True,
        comment="Tags pour catégorisation et recherche"
    )
    
    # ==========================================================================
    #  CONTRÔLE D'ACCÈS & VISIBILITÉ
    # ==========================================================================
    
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Actif et visible (vs archived/inactive)"
    )
    
    
    is_public = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Public (shared across company) vs private (user only)"
    )
    
    
    # ==========================================================================
    # AUDIT TRAIL
    # ==========================================================================
    
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User qui a créé cet actif"
    )
    # CRÉATION :
    # FK to users.id, nullable pour cas système
    
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Dernier user à modifier cet actif"
    )
   
    # ==========================================================================
    # SOFT DELETE
    # ==========================================================================
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="TIMESTAMP quand l'actif a été supprimé (NULL = actif, non supprimé)"
    )
    
    
    # ==========================================================================
    # MÉTADONNÉES FLEXIBLES
    # ==========================================================================
    
    custom_metadata = Column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="'{}'::jsonb",
        comment="Custom metadata: version, category, source, custom fields"
    )
   