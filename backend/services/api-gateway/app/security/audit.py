# ==============================================================================
# AUDIT.PY — Fonctions utilitaires pour les logs d'audit immuables
# ==============================================================================


import hashlib
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import AuditLog


def compute_audit_hash(entry: Dict[str, Any], previous_hash: Optional[str]) -> str:
    """
    Calcule le hash SHA-256 d'une entrée d'audit.
    
    La chaîne d'audit fonctionne comme une blockchain :
    - Hash actuel = SHA-256(contenu_actuel + hash_précédent)
    - Si quelqu'un modifie un log ancien, tous les hashes suivants changent
    - Un vérificateur peut detecter une falsification en comparant les chaînes
    
    Args:
        entry: Dict contenant tenant_id, user_id, action, timestamp, ip_address, etc.
        previous_hash: Le hash du log précédent (ou None si c'est le premier log)
    
    Returns:
        str: Le hash SHA-256 en hexadécimal (64 caractères)
    """
    content = json.dumps(entry, sort_keys=True, default=str)
    
    content += (previous_hash or "")
    
    return hashlib.sha256(content.encode()).hexdigest()


def get_previous_audit_hash(db: Session) -> Optional[str]:
    """
    Récupère le hash du dernier log d'audit enregistré.
    
    Utilisé pour créer la chaîne : chaque nouveau log contient le hash
    du log précédent.
    
    Args:
        db: Session SQLAlchemy
    
    Returns:
        str: Le hash du dernier log, ou None si c'est le premier log
    """
    last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    return last_log.hash if last_log else None
