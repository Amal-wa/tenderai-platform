"""
SQLAlchemy model for user 2FA/TOTP configuration.
"""

from sqlalchemy import Column, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime
from app.models.base import Base


class UserTOTP(Base):
    """
    Stores TOTP secret and backup codes for 2FA-enabled users.
    
    Secrets are encrypted at rest using Fernet (symmetric encryption).
    Backup codes are stored as SHA-256 hashes for one-time use recovery.
    """
    
    __tablename__ = "user_totp"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    
    # TOTP secret (encrypted at rest)
    secret = Column(Text, nullable=False)
    
    # 2FA status
    is_enabled = Column(Boolean, default=False, nullable=False)
    
    # Backup codes (stored as hashed JSON array)
    backup_codes = Column(JSONB, default=list, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)  # When 2FA was first verified
    last_used_at = Column(DateTime(timezone=True), nullable=True)  # Last TOTP code used
    
    # Indexes
    __table_args__ = (
        Index('ix_user_totp_user_id', 'user_id'),
        Index('ix_user_totp_tenant_id', 'tenant_id'),
    )
    
    def __repr__(self):
        return f"<UserTOTP(user_id={self.user_id}, is_enabled={self.is_enabled})>"
