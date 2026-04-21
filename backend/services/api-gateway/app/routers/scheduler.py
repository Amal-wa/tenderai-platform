# ==============================================================================
# app/routers/scheduler.py - Endpoint privé pour les tâches du Scheduler
# ==============================================================================

import logging
import hmac
from fastapi import APIRouter, HTTPException, status, Header, Depends
from typing import Optional
import os

from ..security.auth.key_manager import check_and_rotate_keys

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/internal/scheduler",
    tags=["Scheduler (Internal)"],
)


def verify_scheduler_secret(x_scheduler_secret: Optional[str] = Header(None)) -> None:
    """
    Vérifie que le header secret est valide.
    
    Utilise la variable d'environnement SCHEDULER_SECRET.
    """
    expected_secret = os.getenv("SCHEDULER_SECRET", "")
    
    # Si aucun secret configuré et pas de header, refuser
    if not expected_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scheduler secret not configured on server"
        )
    
    # Vérifier le header avec comparaison constant-time (protection contre timing attacks)
    if not x_scheduler_secret or not hmac.compare_digest(
        x_scheduler_secret.encode(), expected_secret.encode()
    ):
        logger.warning("❌ Tentative d'authentification du scheduler échouée")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing scheduler secret"
        )


@router.post("/rotate-keys")
def rotate_keys(
    _: None = Depends(verify_scheduler_secret)
) -> dict:
    """
    Effectue la rotation des clés EdDSA.
    
    Endpoint appelé par le service scheduler indépendant.
    
    **Authentification** : Header `X-Scheduler-Secret` requis
    
    **Retour** :
    ```json
    {
        "status": "success",
        "message": "Key rotation completed",
        "timestamp": "2024-03-27T02:15:30Z",
        "rotated": true
    }
    ```
    """
    try:
        logger.info("🔑 Rotation des clés EdDSA lancée par le scheduler...")
        
        # Effectuer la rotation
        check_and_rotate_keys()
        
        logger.info("✅ Rotation complétée avec succès")
        
        return {
            "status": "success",
            "message": "Key rotation completed",
            "timestamp": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "rotated": True
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la rotation : {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Key rotation failed: {str(e)}"
        )
