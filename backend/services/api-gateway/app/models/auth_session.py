# ==============================================================================
# MODEL: AUTH SESSION
# ==============================================================================
#
# Gestion des sessions utilisateur
# Permet multi-device login et revocation sélective
# JTI (JWT ID) pour revocation rapide sans refaire JWT validation

from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from .base import Base


class AuthSession(Base):
    """Gestion compacte des sessions utilisateur (multi-device, révocation).

    Append-only audit des sessions avec `jti` pour révocation ciblée.
    """
    
    __tablename__ = "auth_sessions"
    
    # ID & Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="User propriétaire"
    )
    
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="Tenant (for RLS isolation)"
    )
    
    # JWT Identity
    jti = Column(UUID(as_uuid=True), nullable=False, unique=True, default=uuid4)
    
    # Token Type
    token_type = Column(
        String(20),
        nullable=False,
        server_default="access",
        comment="Type de token : access (30 min) ou refresh (7 jours)"
    )
    
    # Device Info
    user_agent = Column(
        Text,
        nullable=True,
        comment="User-agent header (Safari/14.1.1 on Mac OS)"
    )
    
    ip_address = Column(
        INET,
        nullable=True,
        comment="IPv4/IPv6 source IP (pour détection anomalie)"
    )
    
    # Timeline
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Expiration JWT (1h, 7d pour refresh_token)"
    )
    
    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="NULL = active, non-NULL = revoked at timestamp"
    )
    
    replaced_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Si remplacé par nouveau JTI (refresh token)"
    )
    
    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Dernier usage (pour logout inactivité)"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="auth_sessions",
        foreign_keys=[user_id]
    )
    
    tenant = relationship(
        "Tenant",
        back_populates="auth_sessions",
        foreign_keys=[tenant_id]
    )
    
    # Utility Methods
    def ensure_timezone_aware(self):
        """
        🔧 CRITICAL FIX: Ensure all datetime fields are timezone-aware.
        
        SQLAlchemy sometimes returns naive datetimes from DateTime(timezone=True) columns,
        especially when psycopg3 is used. This method fixes that issue.
        
        Call this whenever a session is retrieved from the database.
        """
        from datetime import timezone
        
        for field_name in ['created_at', 'expires_at', 'revoked_at', 'last_used_at']:
            field_value = getattr(self, field_name, None)
            if field_value and isinstance(field_value, datetime) and field_value.tzinfo is None:
                setattr(self, field_name, field_value.replace(tzinfo=timezone.utc))
        
        return self
    
    def is_active(self):
        """Vérifier si session est active"""
        # FIX: Use timezone-aware datetime to compare with expires_at (which is timezone-aware)
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        
        self.ensure_timezone_aware()
        
        return (
            self.revoked_at is None and
            self.expires_at > now
        )
    
    def is_expired(self):
        """Vérifier si session a expiré"""
        # FIX: Use timezone-aware datetime for consistent comparison
        from datetime import timezone
        
       
        self.ensure_timezone_aware()
        
        return self.expires_at < datetime.now(timezone.utc)
