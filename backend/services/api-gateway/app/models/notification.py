# ==============================================================================
# MODEL: NOTIFICATION — 🔔 Système de notifications
# ==============================================================================

from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from .base import Base


class Notification(Base):
    """
    Modèle Notification - Système de notifications multi-tenant
    
    """
    
    __tablename__ = "notifications"  # Table PostgreSQL
    
    # ==========================================================================
    #  IDENTIFICATION
    # ==========================================================================
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Notification ID"
    )
    
    # ==========================================================================
    #  MULTI-TENANT + USER 
    # ==========================================================================
    
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="Tenant propriétaire (RLS isolation)"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # NULL = broadcast au tenant entier
        comment="User destinataire. NULL = broadcast"
    )
    
    # ==========================================================================
    #  CONTENU
    # ==========================================================================
    
    type = Column(
        String(20),
        nullable=False,
        comment="Type: urgent, info, success"
    )
    
    message = Column(
        String(500),
        nullable=False,
        comment="Texte du message"
    )
    
    # ==========================================================================
    #  ÉTAT
    # ==========================================================================
    
    is_read = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="A été lue?"
    )
    
    # ==========================================================================
    # ⏱ TIMESTAMPS
    # ==========================================================================
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp création"
    )
    
    # ==========================================================================
    # INDEXES pour performance
    # ==========================================================================
    
    __table_args__ = (
        # Index pour trouver les notifications d'un tenant
        Index("ix_notifications_tenant_id", "tenant_id"),
        
        # Index pour trouver les notifications d'un user
        Index("ix_notifications_user_id", "user_id"),
        
        # Index pour les notifications non lues
        Index("ix_notifications_is_read", "is_read"),
        
        # Index pour tri chronologique
        Index("ix_notifications_created_at", "created_at"),
        
        # CHECK constraint pour type
        CheckConstraint("type IN ('urgent', 'info', 'success')", name="notifications_type_enum"),
    )
