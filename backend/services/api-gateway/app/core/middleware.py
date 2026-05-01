# ==============================================================================
# MIDDLEWARE.PY — Middleware RBAC pour enrichir le contexte de chaque requête
# ==============================================================================


import logging
import base64
import json
import os
import re
import ipaddress
from typing import Callable, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from time import time

from fastapi import Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from sqlalchemy.orm import Session

from ..models import AuthSession
from ..database import get_db as _get_db, set_tenant_context, SessionLocal
from ..auth import verify_token

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
#  REQUEST ID MIDDLEWARE
# ==============================================================================

class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Génère un UUID unique pour chaque requête et l'ajoute aux en-têtes.
    Utilisé pour tracer les requêtes dans les logs.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            request_id = uuid4()
            request.state.request_id = request_id
            response = await call_next(request)
            response.headers["X-Request-ID"] = str(request_id)
            return response
        except Exception as e:
            logger.exception(
                "RequestIdMiddleware error: %s", str(e)
            )
            # Ne jamais lever d'exception — laisser passer
            return await call_next(request)


# ==============================================================================
#  LOGGING MIDDLEWARE
# ==============================================================================

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logge chaque requête HTTP avec un format JSON structuré
    après l'exécution (pour avoir le status_code).
    """

    # Routes à exclure du logging (trop fréquentes)
    EXCLUDED_PATHS = {"/health", "/metrics", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            # Ne pas logger les routes exclues
            if request.url.path in self.EXCLUDED_PATHS:
                return await call_next(request)

            start_time = time()
            response = await call_next(request)
            duration_ms = (time() - start_time) * 1000

            # Récupérer les identifiants depuis request.state
            request_id = getattr(
                request.state, "request_id", None
            )
            user_id = getattr(request.state, "user_id", None)
            tenant_id = getattr(request.state, "tenant_id", None)

            # Log en format JSON structuré
            log_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "request_id": str(request_id) if request_id else None,
                "user_id": str(user_id) if user_id else None,
                "tenant_id": str(tenant_id) if tenant_id else None,
            }
            logger.info(json.dumps(log_data))
            return response

        except Exception as e:
            logger.exception(
                "LoggingMiddleware error: %s", str(e)
            )
            # Ne jamais lever d'exception
            return await call_next(request)


# ==============================================================================
#  JWT AUTH MIDDLEWARE
# ==============================================================================

# Routes publiques exclues de la validation JWT (pour JWTAuthMiddleware)
JWT_PUBLIC_PATHS = frozenset({
    "/health",
    "/metrics",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/resend-verification",
    "/api/v1/auth/check-email",
    "/api/v1/auth/password-reset/request",
    "/api/v1/auth/password-reset/confirm",
    "/api/v1/auth/invite/accept",
    "/.well-known/jwks.json",
    "/api/docs",
    "/api/openapi.json",
    "/docs",
    "/openapi.json",
})


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Valide les JWT sur les routes protégées.
    Vérifie que le JTI n'est pas révoqué dans la DB.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            # Routes publiques → laisser passer
            if request.url.path in JWT_PUBLIC_PATHS:
                return await call_next(request)

            # Extraire le token du header Authorization
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                # Pas de token → laisser passer (l'endpoint lèvera 401)
                return await call_next(request)

            token = auth_header[7:]

            try:
                # Vérifier la signature du JWT
                payload = verify_token(token)
                jti = payload.get("jti")
                user_id = payload.get("sub")
                tenant_id = payload.get("tenant_id")

                # Stocker dans request.state (sera utilisé par RBACMiddleware)
                request.state.user_id = user_id
                request.state.tenant_id = tenant_id
                request.state.jti = jti

                # Vérifier que le JTI n'est pas révoqué
                if jti:
                    db = SessionLocal()
                    try:
                        now = datetime.now(timezone.utc)
                        session = db.query(AuthSession).filter(
                            AuthSession.jti == jti,
                            AuthSession.revoked_at.is_(None),
                            AuthSession.expires_at > now,
                        ).first()

                        if not session:
                            # JTI révoqué ou expiré
                            return JSONResponse(
                                status_code=401,
                                content={"detail": "Token invalide"},
                            )
                    finally:
                        db.close()

            except Exception as e:
                logger.debug(
                    "JWT validation error on %s: %s",
                    request.url.path, str(e)
                )
                # Token invalide → laisser passer
                # (l'endpoint lèvera 401 via get_current_user)

            return await call_next(request)

        except Exception as e:
            logger.exception(
                "JWTAuthMiddleware error: %s", str(e)
            )
            # Ne jamais lever d'exception
            return await call_next(request)


# ==============================================================================
#  SSRF GUARD MIDDLEWARE
# ==============================================================================

class SSRFGuardMiddleware(BaseHTTPMiddleware):
    """
    Protège contre les attaques SSRF en inspectant les URLs
    dans le body des requêtes POST/PUT/PATCH.
    """

    # IP/plages privées interdites
    PRIVATE_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),  # Localhost
        ipaddress.ip_network("10.0.0.0/8"),  # RFC 1918
        ipaddress.ip_network("172.16.0.0/12"),  # RFC 1918
        ipaddress.ip_network("192.168.0.0/16"),  # RFC 1918
        ipaddress.ip_network("169.254.0.0/16"),  # RFC 3927 (AWS metadata)
        ipaddress.ip_network("fc00::/7"),  # RFC 4193 (IPv6 ULA)
    ]

    # Noms de champs qui peuvent contenir des URLs
    URL_FIELD_PATTERNS = {
        "url", "webhook", "callback", "redirect", "uri",
        "endpoint", "target", "destination"
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            # Ne bloquer que POST/PUT/PATCH
            if request.method not in {"POST", "PUT", "PATCH"}:
                return await call_next(request)

            # Ne pas bloquer les routes internes
            if request.url.path.startswith("/api/v1/internal/"):
                return await call_next(request)

            # Lire le body
            try:
                body_bytes = await request.body()
                if not body_bytes:
                    return await call_next(request)

                body_str = body_bytes.decode("utf-8")
                body = json.loads(body_str)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Body non-JSON → laisser passer
                return await call_next(request)

            # Vérifier les champs URL
            if self._contains_blocked_url(body):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "URL non autorisée"},
                )

            # Créer une nouvelle requête avec le body (nécessaire car
            # await request.body() consume le stream)
            async def receive():
                return {
                    "type": "http.request",
                    "body": body_bytes,
                }

            request._receive = receive  # type: ignore

            return await call_next(request)

        except Exception as e:
            logger.exception(
                "SSRFGuardMiddleware error: %s", str(e)
            )
            # Ne jamais lever d'exception
            return await call_next(request)

    def _contains_blocked_url(self, obj: Any) -> bool:
        """
        Cherche récursivement des URLs bloquées dans un objet JSON.
        Vérifie que les clés contiennent les patterns URL.
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Vérifier si la clé suggère une URL
                key_lower = key.lower()
                if any(
                    pattern in key_lower
                    for pattern in self.URL_FIELD_PATTERNS
                ):
                    if self._is_blocked_url(value):
                        return True

                # Vérifier récursivement
                if isinstance(value, (dict, list)):
                    if self._contains_blocked_url(value):
                        return True

        elif isinstance(obj, list):
            for item in obj:
                if self._contains_blocked_url(item):
                    return True

        return False

    def _is_blocked_url(self, value: Any) -> bool:
        """Vérifie si une valeur est une URL bloquée."""
        if not isinstance(value, str):
            return False

        # Extraire l'URL (supporté http://, https://, ftp://)
        url_match = re.search(
            r"(?:https?|ftp)://([^\s/]+)", value, re.IGNORECASE
        )
        if not url_match:
            return False

        host = url_match.group(1)

        # Vérifier localhost et 0.0.0.0
        if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
            return True

        # Vérifier les plages privées (IPv4 et IPv6)
        try:
            ip = ipaddress.ip_address(host)
            for network in self.PRIVATE_NETWORKS:
                if ip in network:
                    return True
        except ValueError:
            # hostname plutôt qu'une IP → accepter
            pass

        return False


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
    DEPRECATED: Use LoggingMiddleware instead.

    Logge chaque requête HTTP pour l'audit.
    """
    # user_id = getattr(request.state, "user_id", None)
    # tenant_id = getattr(request.state, "tenant_id", None)
    #
    # # Ne pas logger les routes de santé (trop fréquentes, peu utiles)
    # if request.url.path in ["/health", "/metrics", "/favicon.ico"]:
    #     return
    #
    # logger.info(
    #     "%s %s | status=%s | user=%s | tenant=%s",
    #     request.method,
    #     request.url.path,
    #     response.status_code,
    #     user_id or "anonymous",
    #     tenant_id or "none",
    # )
    pass


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
