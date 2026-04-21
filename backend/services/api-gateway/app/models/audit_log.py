# ==============================================================================
# MODEL: AUDIT LOG
# ==============================================================================
#
# Journal d'audit immuable avec chaîne de hash
# Append-only: INSERT only, JAMAIS UPDATE/DELETE
# Hash chain: chaque log signé avec le hash du log précédent
# Détecte modification rétroactive de logs

from sqlalchemy import Column, String, DateTime, ForeignKey, BigInteger, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base
from .enums import AuditStatus


class AuditLog(Base):
    """Journal d'audit append-only avec chaîne de hash minimale.

    Conserve l'historique immuable des actions pour audit et conformité.
    """
    
    __tablename__ = "audit_logs"
    
    # ID (Sequential, immutable)
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Sequential immutable ID"
    )
    
    # Context
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        comment="Tenant propriétaire (RLS isolation)"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User qui a déclenché l'action (NULL si system)"
    )
    
    # Action
    action = Column(
        String(50),
        nullable=False,
        comment="create, read, update, delete, login, logout, login_failed"
    )
    
    resource_type = Column(
        String(100),
        nullable=False,
        comment="user, role, document, chunk, compliance_report, tenant, auth_session"
    )
    
    resource_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="UUID de la ressource affectée (NULL pour actions système)"
    )
    
    # Values (for before/after comparison)
    old_value = Column(
        JSONB,
        nullable=True,
        comment="État avant modification (pour UPDATE/DELETE)"
    )
    
    new_value = Column(
        JSONB,
        nullable=True,
        comment="État après modification (pour CREATE/UPDATE)"
    )
    
    # Outcome
    status = Column(
        String(50),
        nullable=False,
        default=AuditStatus.SUCCESS,
        comment="success ou failure"
    )
    
    reason = Column(
        Text,
        nullable=True,
        comment="Détail d'erreur si status=failure"
    )
    
    # Security Context
    ip_address = Column(
        String(45),
        nullable=True,
        comment="IPv4/IPv6 source IP"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="Device/browser user-agent"
    )
    
    # Timestamp
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Quand l'action s'est produite"
    )
    
    # Hash Chain for Integrity
    hash = Column(
        String(64),
        nullable=False,
        comment="SHA256 de ce log + previous_hash (immuable)"
    )
    
    previous_hash = Column(
        String(64),
        nullable=True,
        comment="SHA256 du log précédent (chain integrity)"
    )
    
    # Relationships
    tenant = relationship(
        "Tenant",
        back_populates="audit_logs",
        foreign_keys=[tenant_id]
    )
    
    user = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[user_id]
    )
    
    # Utility Methods
    def verify_hash(self, previous_log: "AuditLog" = None):
        """
        Vérifier intégrité du hash
        
        Comparer:
        - self.hash == SHA256(self.to_json() + previous_log.hash)
        """
        import hashlib
        import json
        
        # Créer payload à signer
        payload = {
            "action": self.action,
            "resource_type": self.resource_type,
            "timestamp": str(self.timestamp),
            "user_id": str(self.user_id) if self.user_id else None,
            "previous_hash": self.previous_hash,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }
        
        # Calculer hash
        json_str = json.dumps(payload, sort_keys=True)
        computed_hash = hashlib.sha256(json_str.encode()).hexdigest()
        
        # Comparer
        return computed_hash == self.hash
    
    # Notes:
    # - Append-only: ne pas update/delete les enregistrements
    # - Indexes/partitioning peuvent être ajoutés via migrations
