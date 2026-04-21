# ==============================================================================
# app/routers/auth_jwks.py — JWKS Endpoint
# ==============================================================================


import logging
import base64
from typing import Dict, Any, List

from fastapi import APIRouter
from cryptography.hazmat.primitives.serialization import (
    load_pem_public_key,
    Encoding,
    PublicFormat,
)
from cryptography.hazmat.primitives.asymmetric import ed25519

from app.security.auth.key_manager import get_key_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


def _base64url_encode(data: bytes) -> str:
    """
    Encodes bytes to base64url (RFC 4648) without padding.
    
    Used for JWKS 'x' field (public key coordinate).
    """
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _extract_public_key_coordinate(public_key_pem: str) -> str:
    """
    Extrait la coordonnée publique Ed25519 et l'encode en base64url.
    
    Args:
        public_key_pem : Clé publique au format PEM
    
    Returns:
        Coordonnée x en base64url
    
    Raises:
        ValueError : Si la clé est invalide ou pas en format PEM
    """
    try:
        public_key_obj = load_pem_public_key(public_key_pem.encode())
        
        if not isinstance(public_key_obj, ed25519.Ed25519PublicKey):
            raise ValueError("Clé n'est pas une clé Ed25519 valide")
        
        # Ed25519 public key est 32 bytes (256 bits)
        public_key_bytes = public_key_obj.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        
        return _base64url_encode(public_key_bytes)
    except Exception as e:
        raise ValueError(f"Impossible d'extraire la coordonnée publique : {e}")


@router.get("/.well-known/jwks.json", response_model=Dict[str, Any])
async def get_jwks() -> Dict[str, Any]:
    """
    Expose les clés publiques EdDSA courantes et précédentes en format JWKS.
    
    Endpoint public (pas d'authentification requise).
    Utilisé par les clients pour valider les JWT émis par cette API.
    
    Exemple de réponse :
    ```json
    {
      "keys": [
        {
          "kty": "OKP",
          "crv": "Ed25519",
          "kid": "current",
          "x": "11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo"
        },
        {
          "kty": "OKP",
          "crv": "Ed25519",
          "kid": "previous",
          "x": "NHvGKAOW_OhsVv1v8K3EH-KqcSxRBXZfH6wZ2JnW8U4"
        }
      ]
    }
    ```
    
    Returns:
        Dict JWKS avec la liste des clés publiques disponibles
    """
    keys_list: List[Dict[str, str]] = []
    manager = get_key_manager()

    try:
        # Récupérer la clé courante
        current_keys = manager.get_current_keys()
        if current_keys and current_keys.get("public_key"):
            current_x = _extract_public_key_coordinate(current_keys["public_key"])
            keys_list.append({
                "kty": "OKP",
                "crv": "Ed25519",
                "kid": "current",
                "x": current_x,
            })
            logger.debug("✅ Clé courante ajoutée au JWKS")
        else:
            logger.warning("⚠️  Pas de clé courante disponible")

        # Récupérer la clé précédente (optionnel)
        previous_keys = manager.get_previous_keys()
        if previous_keys and previous_keys.get("public_key"):
            try:
                previous_x = _extract_public_key_coordinate(previous_keys["public_key"])
                keys_list.append({
                    "kty": "OKP",
                    "crv": "Ed25519",
                    "kid": "previous",
                    "x": previous_x,
                })
                logger.debug("✅ Clé précédente ajoutée au JWKS")
            except ValueError as e:
                logger.warning(f"⚠️  Impossible d'ajouter la clé précédente : {e}")

    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération du JWKS : {e}", exc_info=True)
        # Retourner quand même une structure valide (même vide)
        pass

    return {
        "keys": keys_list
    }
