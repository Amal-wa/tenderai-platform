# ==============================================================================
# MODEL: API KEY — Clés API pour authentification service-to-service
# ==============================================================================

from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from .base import TenantModel

class APIKey(TenantModel):
    """
    Modèle pour les clés API (authentification service-to-service)
   
    """
    
    __tablename__ = "api_keys"
    
    # ==========================================================================
    # 🆔 IDENTIFICATION
    # ==========================================================================
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Identifiant unique de la clé"
    )
    
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User qui a créé cette clé"
    )
    
    # ==========================================================================
    #  METADATA — Information affichée au client
    # ==========================================================================
    
    name = Column(
        String(255),
        nullable=False,
        comment="Nom ami (ex: 'Mon script Python', 'Webhook Zapier')"
    )
    
    # ==========================================================================
    #  SÉCURITÉ — Données de la clé (jamais complètes)
    # ==========================================================================
    
    key_prefix = Column(
        String(12),
        nullable=False,
        comment="Prefix de la clé affiché (ex: 'sk_live_abc1') — 12 caractères du début"
    )
    
    key_hash = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="Hash Argon2id de la clé complète (jamais stocker la clé)"
    )
    
    # ==========================================================================
    #  PERMISSIONS & SCOPES
    # ==========================================================================
    
    permissions = Column(
        ARRAY(String),
        nullable=False,
        server_default='{}',
        comment="Array de scopes : [\"documents:read\", \"proposals:generate\"]"
    )
    
    # ==========================================================================
    #  TIMELINE — État et utilisation
    # ==========================================================================
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Expiration optionnelle (NULL = jamais)"
    )
    
    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="NULL = active, non-NULL = révoquée à ce moment"
    )
    
    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Dernier usage (pour détection d'inactivité)"
    )
    #  created_at et updated_at viennent de TenantModel
    
    # ==========================================================================
    #  RELATIONSHIPS
    # ==========================================================================
    
    user = relationship(
        "User",
        foreign_keys=[user_id]
    )
    
    # ==========================================================================
    #  TABLE METADATA & INDEXES
    # ==========================================================================
    
    __table_args__ = (
        Index('idx_api_keys_tenant_id', 'tenant_id'),
        Index('idx_api_keys_user_id', 'user_id'),
        Index('idx_api_keys_key_prefix', 'key_prefix'),
        Index('idx_api_keys_key_hash', 'key_hash'),
        Index('idx_api_keys_status', 'revoked_at', 'expires_at'),
        Index('idx_api_keys_tenant_status', 'tenant_id', 'revoked_at'),
        Index('idx_api_keys_last_used_at', 'last_used_at'),
    )
    
    # ==========================================================================
    #  UTILITY METHODS
    # ==========================================================================
    
    def is_active(self) -> bool:
        """Vérifier si la clé est active (non révoquée et non expirée)"""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        # Révoquée ?
        if self.revoked_at is not None:
            return False
        
        # Expirée ?
        if self.expires_at is not None and self.expires_at < now:
            return False
        
        return True
    
    def is_revoked(self) -> bool:
        """Vérifier si la clé a été révoquée"""
        return self.revoked_at is not None
    
    def is_expired(self) -> bool:
        """Vérifier si la clé a expiré"""
        if self.expires_at is None:
            return False
        
        from datetime import timezone
        return self.expires_at < datetime.now(timezone.utc)
