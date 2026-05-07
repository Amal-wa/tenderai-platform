# ==============================================================================
# DEPENDENCIES.PY — Injection de dépendances centralisée pour FastAPI
# ==============================================================================


from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from uuid import UUID

from ..database import get_db as _get_db, set_tenant_context
from ..auth import get_current_user as _get_current_user
from ..security.api_keys import verify_api_key

from .authz import (
    require_role,         # Dépendance par rôle exact
    require_any_role,     # Dépendance acceptant plusieurs rôles
    check_permission,     # Fonction utilitaire de vérification
)


get_db = _get_db


# ==============================================================================
#  AUTHENTIFICATION JWT
# ==============================================================================

get_current_user = _get_current_user


# ==============================================================================
#  AUTHENTIFICATION COMBINÉE (JWT ou API Key)
# ==============================================================================



async def get_current_auth(
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None),
) -> dict:
    """
    Dépendance pour authentification combinée (JWT ou API Key).
    
   
    """
    from ..auth import get_current_user
    
    # ── PRIORITÉ 1 : X-API-Key header ──────────────────────────────────────
    if x_api_key:
        auth_result = verify_api_key(x_api_key, db)
        
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clé API invalide, révoquée ou expirée.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
       
        set_tenant_context(db, UUID(auth_result["tenant_id"]))
        
        return {
            "type": "api_key",
            "auth_result": auth_result,
            **auth_result,  # Expand tenant_id, user_id, permissions
        }
    
    # ── PRIORITÉ 2 : Authorization header (JWT) ────────────────────────────
    # Appel get_current_user qui:
    # - Extrait le JWT
    # - Vérifie la signature
    # - Défini set_tenant_context() lui-même
    # - Retourne l'objet User
    
    try:
        user = await get_current_user(db=db)
        
        return {
            "type": "jwt",
            "user": user,
            "user_id": str(user.id),
            "tenant_id": str(user.tenant_id),
        }
    except HTTPException:
        # Pas de JWT valide non plus
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise. Fournissez un JWT ou une clé API.",
            headers={"WWW-Authenticate": "Bearer, ApiKey"},
        )


# ==============================================================================
#  API KEY PERMISSION CHECKING
# ==============================================================================

from typing import Callable

def require_permission(permission: str) -> Callable:
    """
    Factory for API key permission validation dependency.

    Ensures that authenticated user has the required permission via API key.
    Rejects JWT-only authentication (requires API key).

    Args:
        permission: Required permission scope (e.g., "documents:read")

    Returns:
        FastAPI dependency function that validates permission
    """

    async def dependency(
        auth: dict = Depends(get_current_auth),
    ) -> dict:
        """
        Validates that auth is via API key and has required permission.

        Args:
            auth: Authentication result from get_current_auth()

        Returns:
            auth dict if validation passes

        Raises:
            HTTPException(403): If API key not provided or permission missing
        """
        if auth.get("type") != "api_key":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key required",
            )

        permissions: list[str] = auth.get("permissions", [])
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return auth

    return dependency


# ==============================================================================
#   RATE LIMITING DEPENDENCIES
# ==============================================================================



from ..core.ratelimit import check_rate_limit, get_client_ip
from ..models import User


def _rate_limit_factory(max_attempts: int, window_minutes: int):
    """
    Factory that creates a rate limit dependency with fixed parameters.

    Args:
        max_attempts: Maximum attempts allowed in time window
        window_minutes: Time window duration in minutes

    Returns:
        FastAPI dependency function
    """
    async def _rate_limit_check(
        request: Request,
        db: Session = Depends(get_db),
    ) -> None:
        """
        Inner dependency called by FastAPI.

        Extracts client IP and email, then applies rate limit check.

        Raises:
            HTTPException(429): If rate limit exceeded
        """
        ip_address = get_client_ip(request)
        email = request.client.host if request.client else "unknown"

        check_rate_limit(
            db=db,
            ip_address=ip_address,
            email=email,
            max_attempts=max_attempts,
            window_minutes=window_minutes,
        )

    return _rate_limit_check


# Pre-configured rate limit constants
RateLimitStrict = _rate_limit_factory(max_attempts=5, window_minutes=1)
"""5 attempts/min — For login, password reset, account deletion"""

RateLimitNormal = _rate_limit_factory(max_attempts=10, window_minutes=1)
"""10 attempts/min — For create, update operations"""

RateLimitRefresh = _rate_limit_factory(max_attempts=30, window_minutes=5)
"""30 attempts/5min — For token refresh (multi-device support)"""

RateLimitEmailVerify = _rate_limit_factory(max_attempts=10, window_minutes=1)
"""10 attempts/min — For email verification checks"""

RateLimitResend = _rate_limit_factory(max_attempts=3, window_minutes=60)
"""3 attempts/hour — For email resend operations"""



__all__ = [
    # DB
    "get_db",
    # Auth
    "get_current_user",
    "get_current_auth",
    # API Key Permissions
    "require_permission",
    # RBAC
    "require_role",
    "require_any_role",
    "check_permission",
    # Rate Limiting
    "RateLimitStrict",
    "RateLimitNormal",
    "RateLimitRefresh",
    "RateLimitEmailVerify",
    "RateLimitResend",
]