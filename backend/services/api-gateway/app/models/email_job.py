# ==============================================================================
# MODEL: EMAIL_JOB —  Système de gestion des emails asynchrones
# ==============================================================================


from enum import Enum
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, Integer, Text, 
    Index, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from .base import TenantModel


# ==============================================================================
#  ENUMS - Types d'emails et états de traitement
# ==============================================================================

class EmailJobType(str, Enum):
    """Types d'emails supportés par le système"""
    PASSWORD_RESET = "password_reset"           # P0: Réinitialisation mot de passe
    INVITATION = "invitation"                   # P0: Invitation utilisateur
    EMAIL_VERIFICATION = "email_verification"   # P1: Vérification email post-registration
    TOTP_CONFIRMATION = "totp_confirmation"     # P1: Confirmation 2FA
    WELCOME_EMAIL = "welcome_email"             # P2: Email de bienvenue


class EmailJobStatus(str, Enum):
    """États du traitement de l'email"""
    PENDING = "pending"   # En attente de traitement
    SENT = "sent"         # Envoyé avec succès
    FAILED = "failed"     # Échec définitif (3 tentatives épuisées)


# ==============================================================================
# MODEL: EMAIL_JOB
# ==============================================================================

class EmailJob(TenantModel):
    """
    Modèle EmailJob - Queue persistante pour courriers électroniques
    
    
    """
    
    __tablename__ = "email_jobs"  # Table PostgreSQL
    
    # ==========================================================================
    # 🆔 IDENTIFICATION
    # ==========================================================================
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Email job ID"
    )
    
    # ==========================================================================
    #  CONTENU ET TYPE
    # ==========================================================================
    
    job_type = Column(
        SQLEnum(EmailJobType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="Type of email: password_reset, invitation, totp_confirmation, welcome_email"
    )
    
    recipient_email = Column(
        String(255),
        nullable=False,
        comment="Target email address"
    )
    
    subject = Column(
        String(255),
        nullable=False,
        comment="Email subject line"
    )
    
    html_body = Column(
        Text(),
        nullable=False,
        comment="HTML email content with dynamic placeholders resolved"
    )
    
    # ==========================================================================
    #  ÉTAT DE TRAITEMENT
    # ==========================================================================
    
    status = Column(
        SQLEnum(EmailJobStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=EmailJobStatus.PENDING,
        comment="Processing status: pending, sent, failed"
    )
    
    attempts = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of send attempts (max 3)"
    )
    
    # ==========================================================================
    # ⏱ TIMESTAMPS DE TRAITEMENT
    # ==========================================================================
    
    next_retry_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Null = send now, or timestamp for retry (exponential backoff: 1m, 5m, 30m)"
    )
    
    sent_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when successfully sent (status=sent)"
    )
    
    error_message = Column(
        Text(),
        nullable=True,
        comment="Failure reason for debugging (status=failed)"
    )
    
    # ==========================================================================
    #  INDEXES pour performance
    # ==========================================================================
    
    __table_args__ = (
        # Critical: selector pattern pour scheduler job processing
        Index(
            "ix_email_jobs_status_retry_at",
            "status",
            "next_retry_at"
        ),
        
        # Fast lookup par destinataire pour duplicate prevention
        Index(
            "ix_email_jobs_tenant_recipient",
            "tenant_id",
            "recipient_email"
        ),
        
        # Temporal query pour audit/analytics
        Index(
            "ix_email_jobs_created_at",
            "created_at"
        ),
    )
