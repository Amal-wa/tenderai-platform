# ==============================================================================
# MODEL: DOCUMENT - 📄 Appels d'offres (RFP) et documents d'entreprise
# ==============================================================================

from uuid import uuid4
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import TenantModel  # ⚠️ TenantModel car chaque document appartient à un tenant
from .enums import DocumentStatus


class Document(TenantModel):  # 🏗️ Hérite de TenantModel → aura tenant_id, created_at, updated_at
    """
    Modèle Document - Appels d'offres (RFP) et documents d'entreprise
    """
    
    __tablename__ = "documents"  # 📊 Table PostgreSQL
    
    # ==========================================================================
    # 🆔 IDENTIFICATION
    # ==========================================================================
    
    id = Column(
        UUID(as_uuid=True),                 # Type UUID
        primary_key=True,                   # Clé primaire
        default=uuid4,                      # Génération automatique
        comment="Document UUID"
    )
    
    # `tenant_id` est fourni par `TenantModel` (hérité) — utilisé pour RLS et isolation
    
    # ==========================================================================
    #  TRACKING - Qui a fait quoi ?
    # ==========================================================================
    # Tracking granulaire pour audit et traçabilité
    
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),    #  Lien vers users
                                                         # SET NULL = si user supprimé → uploaded_by = NULL
        nullable=True,                                   # OPTIONNEL (peut être NULL)
        comment="User qui a uploadé le document"
    )
    
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User créateur (peut être différent d'uploader si admin)"
    )
    
    
    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Dernier user à modifier le document"
    )
    
    
    # ==========================================================================
    #  FILE INFO - Informations sur le fichier
    # ==========================================================================
    
    filename = Column(
        String(255),                        # Limité à 255 caractères
        nullable=False,                     # OBLIGATOIRE (doit avoir un nom)
        comment="Nom original du fichier (appel_d_offre_2026.pdf)"
    )
   
    
    storage_path = Column(
        String(500),                        # Chemin long (S3/MinIO paths peuvent être longs)
        nullable=False,                     # OBLIGATOIRE (doit être stocké quelque part)
        comment="S3/cloud path (ne pas exposer directement au client)"
    )
   
    
    file_size = Column(
        Integer,                            # Type entier (nombre de bytes)
        nullable=True,                     
        comment="Taille en bytes (pour quotas, affichage)"
    )
   
    
    mime_type = Column(
        String(100),
        nullable=True,                     
        comment="MIME type: application/pdf, text/plain, text/html"
    )
  
    
    language = Column(
        String(10),
        nullable=True,                      # ✅ OPTIONNEL (détecté automatiquement)
        comment="ISO 639-1: fr, en, ar (pour NLP/stemming)"
    )
    
    file_hash = Column(
        String(64),                         # SHA256 = 64 caractères hex
        nullable=True,                      
        comment="SHA256 hash du fichier (détection doublons, intégrité)"
    )
    
    # ==========================================================================
    #  PROCESSING - État du traitement
    # ==========================================================================
    
    status = Column(
        String(50),
        nullable=False,                     # OBLIGATOIRE (doit avoir un statut)
        default=DocumentStatus.UPLOADED,    #  Par défaut = uploadé
        comment="Workflow: uploaded → processing → ready (ou error)"
    )
   
    # ==========================================================================
    #  FLEXIBLE CONFIG - Métadonnées personnalisées
    # ==========================================================================
    
    document_metadata = Column(
        "metadata",                        # Nom de la colonne dans la table
        JSONB,                              # Type JSON PostgreSQL (binaire, indexable)
        nullable=False,                     # Ne peut pas être NULL
        default={},                         # Dictionnaire vide par défaut
        server_default="'{}'::jsonb",       # Valeur par défaut au niveau DB
        comment="Custom metadata: encoding, original_size, processing_notes"
    )
   
    
    # ==========================================================================
    #  SOFT DELETE - Suppression logique
    # ==========================================================================
    
    is_deleted = Column(
        Boolean,
        nullable=False,                     # OBLIGATOIRE
        default=False,                      #  Par défaut = non supprimé
        comment="Soft-delete pattern (restorable)"
    )
    
    purge_after = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Datetime après lequel le fichier peut être purgé de MinIO (30j après soft-delete)"
    )
    
    
    purged_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Timestamp quand le fichier a été supprimé de MinIO (hard delete)"
    )
  
    
    # ==========================================================================
    #  RELATIONSHIPS - Relations avec les autres tables
    # ==========================================================================
    
    tenant = relationship(
        "Tenant",                           #  Relation vers le Tenant
        back_populates="documents",         # Bidirectionnel : tenant.documents
        foreign_keys="[Document.tenant_id]" #  String reference pour éviter NameError
    )
    #  Usage : document.tenant → Récupère le tenant propriétaire
    
    uploaded_by_user = relationship(
        "User",                             #  Relation vers le User qui a uploadé
        back_populates="uploaded_documents", # Bidirectionnel : user.uploaded_documents
        foreign_keys="[Document.uploaded_by]" #  String reference
    )
    #  Usage : document.uploaded_by_user → Récupère l'utilisateur qui a uploadé
   
 
