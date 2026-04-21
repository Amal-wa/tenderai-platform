# ==============================================================================
# MIDDLEWARE.PY — Middleware RBAC pour enrichir le contexte de chaque requête
# ==============================================================================


import logging
import base64
import json
import os
from typing import Callable, Optional
from uuid import UUID

from fastapi import Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session

from ..models import AuthSession
from ..database import get_db as _get_db, set_tenant_context

logger = logging.getLogger(__name__)

IS_PRODUCTION = os.getenv("APP_ENV") == "production"


# ==============================================================================
#  SECURITY HEADERS MIDDLEWARE
# ==============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware FastAPI — ajoute les en-têtes HTTP de sécurité défensifs
    sur toutes les réponses API.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'"
        )
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return response


# ==============================================================================
#  PUBLIC_PATHS — Routes exclues du RLS automatique
# ==============================================================================
#
# Ces routes n'ont pas besoin que set_tenant_context() soit appelé
# car elles sont publiques (pas de JWT ou tenant_id externe) ou
# gèrent elles-mêmes le contexte tenant.
#
PUBLIC_PATHS = frozenset({
    "/health",
    "/metrics",
    "/favicon.ico",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/.well-known/jwks.json",
    "/api/docs",
    "/api/openapi.json",
})


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Middleware qui extrait le contexte JWT pour chaque requête.

   
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Méthode principale appelée pour chaque requête HTTP.

        
        """
        # ──────────────────────────────────────────────────────────────────────
        # ÉTAPE 1 : Initialiser request.state avec des valeurs vides
        # ──────────────────────────────────────────────────────────────────────
        request.state.user_id = None
        request.state.tenant_id = None
        request.state.jti = None
        request.state.token_type = None

        # ──────────────────────────────────────────────────────────────────────
        # ÉTAPE 2 : Extraire le token JWT du header Authorization
        # ──────────────────────────────────────────────────────────────────────
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Retire "Bearer " (7 caractères)
            _extract_jwt_context(token, request)

        # ──────────────────────────────────────────────────────────────────────
        # ÉTAPE 3 : Laisser passer la requête vers l'endpoint
        # ──────────────────────────────────────────────────────────────────────
        response = await call_next(request)

        # ──────────────────────────────────────────────────────────────────────
        # ÉTAPE 4 : Logger la requête pour l'audit (après la réponse)
        # ──────────────────────────────────────────────────────────────────────
        _log_request(request, response)

        return response


def _extract_jwt_context(token: str, request: Request) -> None:
    """
    Extrait les claims du JWT et les stocke dans request.state.

    
    """
    try:
        
        # Un JWT a 3 parties séparées par des points : header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            return  # Pas un JWT valide → ignorer silencieusement

        # Décoder le payload (2ème partie) en Base64
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        # Stocker les claims dans request.state
        request.state.user_id = payload.get("sub")       # Subject = user_id
        request.state.tenant_id = payload.get("tenant_id")
        request.state.jti = payload.get("jti")           # JWT ID = session ID
        request.state.token_type = payload.get("type")   # "access" ou "refresh"

    except Exception:
        #  Ne jamais lever d'exception depuis ce middleware
        # Juste ignorer les erreurs de décodage et laisser request.state avec None
        pass


def _log_request(request: Request, response: Response) -> None:
    """
    Logge chaque requête HTTP pour l'audit.

   
    """
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", None)

    # Ne pas logger les routes de santé (trop fréquentes, peu utiles)
    if request.url.path in ["/health", "/metrics", "/favicon.ico"]:
        return

    logger.info(
        "%s %s | status=%s | user=%s | tenant=%s",
        request.method,
        request.url.path,
        response.status_code,
        user_id or "anonymous",
        tenant_id or "none",
    )


# ==============================================================================
# MIDDLEWARE D'ISOLATION MULTI-TENANT (RLS)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Placeholder middleware pour isolation multi-tenant (RLS).
    
     Le vrai travail est dans la dépendance ensure_tenant_context() ci-bas.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Placeholder — voir ensure_tenant_context() pour le vrai travail."""
        return await call_next(request)


# ==============================================================================
#  DÉPENDANCE FASTAPI : Activation du contexte tenant (RLS)
# ==============================================================================


async def ensure_tenant_context(
    request: Request,
    db: Session = Depends(_get_db)
) -> Optional[str]:
    """
    Dépendance FastAPI qui active automatiquement le contexte tenant (RLS).
    
    
    """
    # ── ÉTAPE 1 : Vérifier si la route est publique ────────────────────
    path = request.url.path
    if path in PUBLIC_PATHS:
        # Route publique → pas besoin de set_tenant_context()
        return None
    
    # ── ÉTAPE 2 : Lire tenant_id depuis le JWT (parsé par RBACMiddleware) ──
    tenant_id = getattr(request.state, "tenant_id", None)
    
    if not tenant_id:
        # Pas de JWT → l'endpoint lèvera 401 via get_current_user()
        # Pas besoin d'activer RLS ici
        return None
    
    # ── ÉTAPE 3 : Activer RLS dans PostgreSQL ────────────────────────────
    try:
        # Convertir tenant_id en UUID si string
        if isinstance(tenant_id, str):
            try:
                tenant_id_uuid = UUID(tenant_id)
            except ValueError as e:
                logger.warning(f"Invalid tenant_id format: {tenant_id} — {e}")
                return None
        else:
            tenant_id_uuid = tenant_id

        #  Appeler set_tenant_context() avec la vraie session DB
        # Cela exécute "SET LOCAL app.current_tenant = 'tenant-uuid'"
        # SET LOCAL porte sur la transaction courante, donc la bonne session
        set_tenant_context(db, tenant_id_uuid)
        
        logger.debug(
            f"🔐 RLS context set | tenant={tenant_id_uuid} | path={path}"
        )
        
        return str(tenant_id_uuid)
        
    except Exception as e:
        #  Ne JAMAIS lever d'exception depuis cette dépendance
        # Juste logger et continuer — PostgreSQL RLS fera le filtrage
        logger.warning(
            f"⚠️ Failed to set tenant context for {path}: {e}. "
            f"Continuing without RLS (may result in empty results)"
        )
        return None



def update_session_last_used(db: Session, jti: str) -> None:
    """
    Mets à jour last_used_at pour une session donnée.
    À appeler chaque fois qu'un token est utilisé pour accéder à une ressource.
    """
    try:
        session = db.query(AuthSession).filter(AuthSession.jti == jti).first()
        
        
        if session:
            session.ensure_timezone_aware()
        
        if session and session.revoked_at is None:
            from datetime import datetime, timezone
            session.last_used_at = datetime.now(timezone.utc)
            db.commit()
    except Exception as e:
        logger.warning(f"Failed to update last_used_at: {e}")
