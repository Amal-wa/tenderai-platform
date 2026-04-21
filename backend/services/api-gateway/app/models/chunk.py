# ==============================================================================
# MODEL: CHUNK - 📝 Fragments de documents pour recherche et traitement
# ==============================================================================


from uuid import uuid4
from sqlalchemy import Column, Integer, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from .base import TenantModel


class Chunk(TenantModel):
    """
    Modèle pour les fragments de document (chunks)
    """
    
    __tablename__ = "chunks"
    
    # ==========================================================================
    #  IDENTIFICATION
    # ==========================================================================
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Identifiant unique du chunk"
    )
   
    
    # ==========================================================================
    #  RELATIONS
    # ==========================================================================
    
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Document parent (contenant ce chunk)"
    )
    # CASCADE = Si document supprimé, le chunk est aussi supprimé
    
    # ==========================================================================
    #  CONTENU
    # ==========================================================================
    
    content = Column(
        Text,
        nullable=False,
        comment="Texte extrait du chunk (~500 tokens, ~2000 caractères)"
    )
 
    
    chunk_index = Column(
        Integer,
        nullable=False,
        comment="Position du chunk dans le document (0, 1, 2, ...)"
    )
   
    # ==========================================================================
    # MÉTADONNÉES
    # ==========================================================================
    
    token_count = Column(
        Integer,
        nullable=True,
        comment="Nombre de tokens dans le chunk (pour quotas et LLM)"
    )
    
    
    custom_metadata = Column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict,
        server_default="'{}'::jsonb",
        comment="Custom metadata: encoding, language_detected, source_format"
    )
   
    # ==========================================================================
    #  EMBEDDINGS - Vecteurs pour recherche sémantique
    # ==========================================================================
    
    embedding = Column(
        Vector(dim=1024),
        nullable=True,
        comment="Vecteur d'embedding (1024 dimensions) pour recherche sémantique"
    )
    
    # ==========================================================================
    # SOFT DELETE
    # ==========================================================================
    
    is_deleted = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Soft-delete (suppression logique si parent document supprimé)"
    )
   