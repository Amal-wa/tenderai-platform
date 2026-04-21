# ==============================================================================
# MODEL: LOGIN ATTEMPT
# ==============================================================================
#
# Audit trail de TOUTES les tentatives de connexion
# Succès ET échecs (pour brute-force detection)
# INSERT-only (JAMAIS UPDATE/DELETE)

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, BigInteger, Text, func
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from .base import Base


class LoginAttempt(Base):
    """Audit minimal des tentatives de connexion.

    Enregistrement append-only des tentatives réussies et échouées.
    Conçu pour l'audit et la détection de comportements anormaux.
    """

    __tablename__ = "login_attempts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    email = Column(String(255), nullable=False)

    ip_address = Column(INET, nullable=True)

    user_agent = Column(Text, nullable=True)

    success = Column(Boolean, nullable=False, default=False)

    failure_reason = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


    user = relationship("User", back_populates="login_attempts", foreign_keys=[user_id])
