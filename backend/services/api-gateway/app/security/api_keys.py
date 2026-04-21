# ==============================================================================
# API KEY UTILITIES — Génération et vérification des clés API
# ==============================================================================


import secrets
from typing import Tuple, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError

import logging
logger = logging.getLogger(__name__)

# ==============================================================================
#  PASSWORD HASHER — Partagé avec les mots de passe
# ==============================================================================

def _get_hasher() -> PasswordHasher:
    """Retourne le hasher Argon2id (même que pour les mots de passe)"""
    return PasswordHasher(
        time_cost=2,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        salt_len=16,
        type=Type.ID,
    )

# ==============================================================================
#  GENERATE API KEY
# ==============================================================================

def generate_api_key() -> Tuple[str, str, str]:
    """
    Génère une nouvelle clé API avec hash Argon2id.
    
    📝 FORMAT :
    Clé complète = "tai_" + secrets.token_urlsafe(32)
    Prefix = "tai_" + 4 premiers caractères du token (8 char total)
    Hash = Argon2id(clé complète)
    
    🔐 SÉCURITÉ :
    - secrets.token_urlsafe(32) = 256 bits de random (cryptographique)
    - Hash Argon2id résiste au brute-force
    - Prefix permet l'UI (affiche tai_abc1... sans révéler la clé)
    
    RETURNS:
        (full_key, prefix, key_hash)
   
    """
    # Générer le token aléatoire
    # secrets.token_urlsafe(32) → ~256 bits, format URL-safe (a-z, A-Z, 0-9, -, _)
    token = secrets.token_urlsafe(32)
    
    # Construire la clé complète
    full_key = f"tai_{token}"
    
    # Prefix = "tai_" (4 chars) + 4 premiers du token = 8 chars
    prefix = full_key[:8]
    
    # Hasher la clé complète avec Argon2id
    hasher = _get_hasher()
    key_hash = hasher.hash(full_key)
    
    logger.debug(f"✅ Generated API key with prefix: {prefix}")
    
    return full_key, prefix, key_hash

# ==============================================================================
#  VERIFY API KEY
# ==============================================================================

def verify_api_key(raw_key: str, db: Session) -> Optional[dict]:
    """
    Vérifie une clé API:
    1. Cherche par prefix dans la DB
    2. Vérifie le hash Argon2id
    3. Vérifie que la clé n'est pas révoquée
    4. Vérifie que la clé n'est pas expirée
    5. Met à jour last_used_at
    
    🔐 SÉCURITÉ :
    - Pas de log de la clé complète, seulement du prefix
    - Comparaison en temps constant (Argon2id natif)
    - Fail-safe : si quelque chose de louche → retourne None
    
    ARGS:
        raw_key: La clé API fournie par le client (ex: "tai_abc123...")
        db: SQLAlchemy session
    
    RETURNS:
        Dict avec {tenant_id, user_id, permissions} si valide
        None si invalide, révoquée, expirée ou mal formée
    """
    from ..models import APIKey
    
    # Validation rapide du format
    if not raw_key or not isinstance(raw_key, str) or len(raw_key) < 8:
        logger.warning("❌ API key malformed (too short or invalid type)")
        return None
    
    # Extraire le prefix (8 premiers caractères)
    prefix = raw_key[:8]
    
    # Chercher la clé par prefix
    try:
        api_key = db.query(APIKey).filter(APIKey.key_prefix == prefix).first()
    except Exception as e:
        logger.error(f"❌ Database error while querying API key: {e}")
        return None
    
    if not api_key:
        logger.warning(f"❌ No API key found with prefix: {prefix}")
        return None
    
    # Logger avec le prefix seulement (pas la clé complète)
    logger.debug(f"🔍 Found API key: {prefix}... (user_id={api_key.user_id})")
    
    # Vérifier la révocation
    if api_key.is_revoked():
        logger.warning(f"❌ API key revoked: {prefix} (revoked_at={api_key.revoked_at})")
        return None
    
    # Vérifier l'expiration
    if api_key.is_expired():
        logger.warning(f"❌ API key expired: {prefix} (expires_at={api_key.expires_at})")
        return None
    
    # Vérifier le hash Argon2id
    hasher = _get_hasher()
    try:
        hasher.verify(api_key.key_hash, raw_key)
    except VerifyMismatchError:
        logger.warning(f"❌ API key hash mismatch: {prefix}")
        return None
    except Exception as e:
        logger.error(f"❌ Hash verification error: {e}")
        return None
    
    
    try:
        api_key.last_used_at = datetime.now(timezone.utc)
        db.commit()
        logger.debug(f"✅ API key verified and updated: {prefix}")
    except Exception as e:
        logger.warning(f"⚠️  Failed to update last_used_at: {e}")
        # Ne pas échouer si on ne peut pas meter à jour last_used_at
        db.rollback()
    
    # Retourner les infos d'authentification
    return {
        "api_key_id": str(api_key.id),
        "tenant_id": str(api_key.tenant_id),
        "user_id": str(api_key.user_id),
        "permissions": api_key.permissions or [],
    }

# ==============================================================================
#  SCOPES DISPONIBLES
# ==============================================================================

API_KEY_SCOPES = [
    "documents:read",
    "documents:write",
    "proposals:read",
    "proposals:generate",
    "compliance:check",
]

def validate_scopes(scopes: list) -> bool:
    """
    Vérifie que tous les scopes fournis sont valides.
    
    ARGS:
        scopes: Liste de scopes (ex: ["documents:read", "proposals:write"])
    
    RETURNS:
        True si tous les scopes sont valides, False sinon
    """
    if not isinstance(scopes, list):
        return False
    
    for scope in scopes:
        if scope not in API_KEY_SCOPES:
            logger.warning(f"❌ Invalid scope: {scope}")
            return False
    
    return True
