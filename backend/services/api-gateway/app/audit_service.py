# ==============================================================================
# audit_service.py — Helper pour audit_logs
# ==============================================================================

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

from .models import AuditLog


def get_previous_audit_hash(db: Session) -> str:
    last_log = db.query(AuditLog).order_by(
        desc(AuditLog.timestamp)
    ).with_for_update().first()

    if not last_log:
        return "genesis"

    return last_log.hash


def log_action(
    db: Session,
    tenant_id: UUID,
    user_id: UUID,
    action: str,
    resource_type: str,
    resource_id: UUID,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    status: str = "success",
    reason: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """
    Enregistre une action dans audit_logs avec hash chain.
    """

    previous_hash = get_previous_audit_hash(db)

    # Créer l'entrée
    now = datetime.now(timezone.utc)

    # Calculer le hash
    hash_data = {
        "tenant_id": str(tenant_id),
        "user_id": str(user_id),
        "action": action,
        "resource_type": resource_type,
        "resource_id": str(resource_id),
        "timestamp": now.isoformat(),
        "previous_hash": previous_hash,
    }

    current_hash = hashlib.sha256(
        json.dumps(hash_data, sort_keys=True).encode()
    ).hexdigest()

   
    db.execute(
        text("""
            INSERT INTO audit_logs (
                tenant_id, user_id, action, resource_type, resource_id,
                old_value, new_value, status, reason,
                ip_address, user_agent, timestamp, hash, previous_hash
            ) VALUES (
                :tenant_id, :user_id, :action, :resource_type, :resource_id,
                CAST(:old_value AS jsonb), CAST(:new_value AS jsonb), :status, :reason,
                :ip_address, :user_agent, :timestamp, :hash, :previous_hash
            )
        """),
        {
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "old_value": json.dumps(old_value or {}),
            "new_value": json.dumps(new_value or {}),
            "status": status,
            "reason": reason,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": now,
            "hash": current_hash,
            "previous_hash": previous_hash,
        }
    )

    logger.info(
        f"📝 Audit: {action} on {resource_type}:{resource_id} "
        f"by user {user_id} ({status})"
    )
