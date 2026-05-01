# ==============================================================================
# MAIN.PY — Point d'entrée de l'API FastAPI (MONOLITHE API)
# ==============================================================================


import os
import logging
import uuid as _uuid
import hashlib
import magic
from io import BytesIO
from contextlib import asynccontextmanager
from datetime import timedelta, datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import jwt as _jwt
from jwt.exceptions import InvalidTokenError as JWTError
from dotenv import load_dotenv

from fastapi import FastAPI, Depends, HTTPException, status, Query, Path, Request, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, exists as exists_fn
from sqlalchemy.exc import IntegrityError

from .models import (
    Tenant, Role, User, Document, UserTOTP,
    AuthSession, AuditLog, ComplianceReport, Notification
)
from .schemas import (
    TenantCreate, TenantResponse, TenantUpdate, RoleCreate, RoleResponse, UserCreate, UserLogin, UserResponse, UserDetailResponse,
    UserUpdate, UserProfileResponse, UserProfileUpdate,
    DocumentCreate, DocumentResponse, DocumentDeleteResponse,
    DocumentStatsResponse, ComplianceReportResponse,
    TokenResponse, AuthSessionResponse, SessionRevokeResponse, RegisterRequest, RegisterResponse,
    AuditLogResponse,
    NotificationResponse, AdminDashboardResponse, UserDashboardResponse,
    ErrorResponse, PaginatedResponse,
    PasswordResetRequest, PasswordResetConfirm, PasswordResetResponse, ChangePasswordRequest, ChangePasswordResponse,
    UserInvitationRequest, AcceptInvitationRequest, AcceptInvitationResponse,
    AnalyseStatsResponse, AnalyseRequestSchema, AnalyseResultResponse, AnalyseHistoryItemResponse
)
from .security import (
    create_access_token, create_refresh_token,
)
from .security.cookies import set_auth_cookies, delete_auth_cookies, IS_PRODUCTION
from .auth import (
    get_password_hash, verify_password, password_needs_rehash,
    verify_token, revoke_auth_session, create_auth_session,
    get_current_user, get_current_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS,
    oauth2_scheme, enforce_session_limit, MAX_SESSIONS
)
from .database import get_db
from .storage import minio_client
from .audit_service import log_action
from .core.ratelimit import check_rate_limit, get_client_ip, record_login_attempt
from .core.dependencies import (
    RateLimitStrict, RateLimitNormal, RateLimitRefresh, 
    RateLimitEmailVerify, RateLimitResend
)
from .core.middleware import (
    SecurityHeadersMiddleware, RBACMiddleware, TenantContextMiddleware,
    RequestIdMiddleware, LoggingMiddleware, JWTAuthMiddleware,
    SSRFGuardMiddleware, ensure_tenant_context
)
from .core.permissions import is_super_admin
from .routers.totp import router as totp_router
from .routers.auth_jwks import router as auth_jwks_router
from .routers.api_keys import router as api_keys_router
from .routers.scheduler import router as scheduler_router
from .routers.email import router as email_router
from .routers.analyse import router as analyse_router
import json

# Load environment variables
load_dotenv("/app/.env")

logger = logging.getLogger(__name__)


# ==============================================================================
# LIFESPAN — Gestion du cycle de vie de l'application
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le démarrage et l'arrêt de l'application.
    
    - Startup : valide les clés EdDSA
    - Shutdown : clean shutdown
    
    Note : La rotation des clés est gérée par le service scheduler indépendant
    """
    # ── STARTUP ────────────────────────────────────────────────────────────
    logger.info("🚀 Démarrage de l'application TenderAI...")
    
    # Valider les clés EdDSA
    _startup_validate_keys()
    
    # Charger SCHEDULER_SECRET depuis Vault ou .env
    _startup_load_scheduler_secret()
    
    # Validate cookie security flags
    if IS_PRODUCTION:
        logger.info("✅ Cookie Secure flag: ON")
    else:
        logger.warning("⚠️ APP_ENV != production — cookies sans flag Secure")
    
    logger.info("✅ Application démarrée avec succès")
    
    yield  # L'app fonctionne maintenant
    
    # ── SHUTDOWN ───────────────────────────────────────────────────────────
    logger.info("🛑 Arrêt de l'application...")
    logger.info("✅ Application arrêtée")


def _startup_validate_keys():
    """
    Valide que les clés EdDSA sont chargées et fonctionnelles au démarrage.

     FLUX MODE VAULT (USE_VAULT=true) :
    1. Tentative de connexion à HashiCorp Vault (VAULT_ADDR, VAULT_TOKEN)
    2. Si Vault est disponible:
       - Charge les clés depuis /secret/data/tenderai/ed25519-keys
       - Vérifie si rotation nécessaire (interval > 30 jours par défaut)
       - Effectue la rotation si nécessaire (avec backup automatique)
    3. Si Vault indisponible ou pas configuré:
       - Fallback à .env ou génération automatique

     FLUX MODE ENV (USE_VAULT=false, défaut) :
    1. Charge les clés depuis ED25519_PRIVATE_KEY / ED25519_PUBLIC_KEY en .env
    2. Si absent, génère automatiquement une nouvelle paire
    3. Vérifie la rotation basée intervalle

    La stratégie est : "Vault first si activé, fallback à .env, fail-safe avec auto-génération"
    """
    from .security.auth.key_manager import get_key_manager, check_and_rotate_keys
    
    # Check SECRET_ENCRYPTION_KEY (required in all modes)
    if not os.getenv("SECRET_ENCRYPTION_KEY"):
        raise RuntimeError("SECRET_ENCRYPTION_KEY is not set. Server cannot start.")
    
    # Initialiser le key manager (choisit automatiquement Vault ou Env)
    manager = get_key_manager()
    
    # Charger les clés (ou générer si absent)
    keys = manager.get_current_keys()
    if not keys or not keys.get("private_key") or not keys.get("public_key"):
        logger.warning("⚠️  Pas de clés trouvées. Génération automatique...")
        # Le get_current_keys() devrait avoir généré une paire si vide
        # Si ce n'est pas le cas, il y a un problème
        raise RuntimeError(
            "❌ EdDSA keys failed to load! "
            "Check configuration and logs."
        )

    logger.info("✅ EdDSA keys chargées avec succès")
    
    # Vérifier et effectuer la rotation si nécessaire
    check_and_rotate_keys()
    
    logger.info("✅ Validation de démarrage terminée")


def _create_tenant_roles(db: Session, tenant_id: UUID) -> None:
    """
    Create 6 tenant-specific roles with their exact permissions.
    
    Called during user registration after tenant creation to ensure each
    tenant gets its own set of roles isolated by tenant_id.
    
    Roles created:
    1. superadmin — Full access (owner of organization)
    2. admin — Admin access (all permissions)
    3. manager — Mid-level access (documents + users + proposals)
    4. analyst — Analyst access (read + analysis)
    5. contributor — Limited write access (documents + proposals)
    6. viewer — Read-only access
    
    Args:
        db: SQLAlchemy Session
        tenant_id: UUID of the tenant to create roles for
    """
    
    # Role definitions with permissions list (flat array, not nested)
    roles_to_create: List[Dict[str, Any]] = [
        {
            "name": "superadmin",
            "description": "Propriétaire de l'organisation — accès complet",
            "permissions": [
                "documents:read", "documents:write", "documents:delete",
                "proposals:read", "proposals:write", "proposals:approve",
                "compliance:read", "compliance:write",
                "users:read", "users:write", "users:delete",
                "settings:read", "settings:write",
                "roles:read", "roles:write",
                "billing:read", "billing:write",
                "admin:all"
            ]
        },
        {
            "name": "admin",
            "description": "Administration de l'organisation",
            "permissions": [
                "documents:read", "documents:write", "documents:delete",
                "proposals:read", "proposals:write", "proposals:approve",
                "compliance:read", "compliance:write",
                "users:read", "users:write", "users:delete",
                "settings:read", "settings:write",
                "roles:read", "roles:write",
                "billing:read", "billing:write",
                "admin:all"
            ]
        },
        {
            "name": "manager",
            "description": "Gestion des appels d'offres et de l'équipe",
            "permissions": [
                "documents:read", "documents:write",
                "proposals:read", "proposals:write", "proposals:approve",
                "compliance:read", "compliance:write",
                "users:read", "users:write",
                "settings:read", "settings:write"
            ]
        },
        {
            "name": "analyst",
            "description": "Analyse et conformité",
            "permissions": [
                "documents:read", "documents:write", "documents:delete",
                "proposals:read", "proposals:write",
                "compliance:read", "compliance:write",
                "users:read",
                "settings:read"
            ]
        },
        {
            "name": "contributor",
            "description": "Contribution aux appels d'offres",
            "permissions": [
                "documents:read", "documents:write",
                "proposals:read", "proposals:write",
                "compliance:read"
            ]
        },
        {
            "name": "viewer",
            "description": "Lecture seule",
            "permissions": [
                "documents:read",
                "proposals:read",
                "compliance:read"
            ]
        }
    ]
    
    # Create each role for this tenant
    for role_data in roles_to_create:
        try:
            role = Role(
                tenant_id=tenant_id,
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],  # Flat list of permissions
            )
            db.add(role)
            logger.info(f"✅ Created role '{role_data['name']}' for tenant {tenant_id}")
        except IntegrityError as e:
            # Role may already exist (shouldn't happen in register flow)
            logger.warning(
                f"⚠️  Role '{role_data['name']}' already exists for tenant {tenant_id}: {e}"
            )
            db.rollback()
    
    # Flush all roles to DB in one go (without committing)
    try:
        db.flush()
        logger.info(f"✅ All 6 roles created and flushed for tenant {tenant_id}")
    except Exception as e:
        logger.error(f"❌ Error flushing roles for tenant {tenant_id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la création des rôles pour votre organisation.",
            headers={"X-Error-Code": "role_creation_failed"}
        )


def _startup_load_scheduler_secret():
    """
    Charge SCHEDULER_SECRET au démarrage de l'application.
    
     MODE VAULT (USE_VAULT=true) :
       Lit depuis secret/tenderai/scheduler → scheduler_secret
       
     MODE ENV (USE_VAULT=false, défaut) :
       Lit depuis variable d'environnement SCHEDULER_SECRET
       
    La valeur chargée est définie dans os.environ pour être 
    accédée par les routers (email.py, scheduler.py) via os.getenv().
    """
    use_vault = os.getenv("USE_VAULT", "false").lower() == "true"
    
    scheduler_secret = None
    
    if use_vault:
        # Mode Vault : lire depuis secret/tenderai/scheduler
        try:
            from .security.auth.vault_manager import get_vault_manager
            vault_manager = get_vault_manager()
            scheduler_secret = vault_manager.read_scheduler_secret()
            
            if scheduler_secret:
                logger.info("✅ SCHEDULER_SECRET chargé depuis Vault")
                os.environ["SCHEDULER_SECRET"] = scheduler_secret
            else:
                logger.warning(
                    "⚠️  SCHEDULER_SECRET n'existe pas dans Vault. "
                    "Utiliser le script init_vault.sh pour générer."
                )
        except Exception as e:
            logger.error(
                f"❌ Erreur lors de la lecture SCHEDULER_SECRET depuis Vault : {e}"
            )
            logger.warning("⚠️  Fallback à variable d'environnement...")
    
    # Fallback à .env (mode dev ou si Vault indisponible)
    if not scheduler_secret:
        scheduler_secret = os.getenv("SCHEDULER_SECRET", "")
        if scheduler_secret:
            logger.info("✅ SCHEDULER_SECRET chargé depuis .env")
        else:
            logger.warning(
                "⚠️  SCHEDULER_SECRET non défini. "
                "Le scheduler ne pourra pas authentifier les requests."
            )


# ==============================================================================
# 1. SETUP — Création de l'application FastAPI
# =============================================================================="


app_env = os.getenv("APP_ENV", "development").lower()
docs_url = None if app_env == "production" else "/api/docs"
openapi_url = None if app_env == "production" else "/api/openapi.json"


sentry_dsn = os.getenv("SENTRY_DSN", "")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
        # We recommend adjusting this value in production:
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
        # We recommend adjusting this value in production:
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        # Environment tag for better organization in Sentry dashboard
        environment=app_env,
        # Release/version tracking
        release=os.getenv("APP_VERSION", "0.1.0"),
    )
    logger.info(f"✅ Sentry initialized for error tracking (env={app_env})")
else:
    logger.info("ℹ️  Sentry not configured (SENTRY_DSN not set)")

app = FastAPI(
    title="TenderAI API Gateway",
    version="1.0.0",
    description="API multi-tenant avec RLS, gestion de documents et audit trail",
    docs_url=docs_url,        
    openapi_url=openapi_url,
    lifespan=lifespan, 
    dependencies=[Depends(ensure_tenant_context)],  
)


_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if o.strip()
]

# L'ordre d'add_middleware est inversé en Starlette : le dernier ajouté s'exécute en premier
# SecurityHeaders doit s'exécuter en dernier (sur la response) → on l'ajoute en premier
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS, 
    allow_credentials=True,          
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Add RBAC middleware for extracting auth context from JWT
app.add_middleware(RBACMiddleware)

# Automatically activate tenant context (RLS) for protected routes
# This middleware ensures set_tenant_context() is called before each request
# if the user is authenticated (tenant_id is present in JWT).
# Routes excluded: /health, /api/v1/auth/*, /docs, /metrics
app.add_middleware(TenantContextMiddleware)


# ==============================================================================
# VALIDATION ERROR HANDLER — Capture Pydantic validation errors for debugging
# ==============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for Pydantic validation errors.
    Logs exact field validation failures to help debug 2FA endpoint issues.
    """
    totp_logger = logging.getLogger("totp")
    
    # Log validation errors
    totp_logger.info(f"[VALIDATION ERROR] Endpoint: {request.url.path}")
    totp_logger.info(f"[VALIDATION ERROR] Method: {request.method}")
    totp_logger.info(f"[VALIDATION ERROR] Errors: {exc.errors()}")
    
    # Try to log request body
    try:
        body = await request.body()
        if body:
            totp_logger.info(f"[VALIDATION ERROR] Body: {body.decode() if isinstance(body, bytes) else body}")
    except Exception as e:
        totp_logger.warning(f"[VALIDATION ERROR] Could not read body: {e}")
    
    # Return standard error response
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body_raw": str(exc.raw_errors) if hasattr(exc, 'raw_errors') else None
        }
    )


# Register 2FA TOTP router
app.include_router(totp_router)

# Register JWKS router (public .well-known endpoint)
app.include_router(auth_jwks_router, prefix="/auth")

# Register API Keys router
app.include_router(api_keys_router)

# Register Scheduler router (internal, private endpoints)
app.include_router(scheduler_router)

# Register Email router (internal, private endpoints)
app.include_router(email_router)

# Register Analyse router (IA analysis endpoints)
app.include_router(analyse_router)


@app.get("/health", tags=["Health"])
async def health():
    """
    Endpoint de vérification de santé.
    Utilisé par Docker, Kubernetes ou le load balancer pour vérifier
    que l'API est démarrée et répond correctement.
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/v1/health", tags=["Health"])
async def health_v1():
    """
    Endpoint de vérification de santé (versioned path).
    Alias pour /health avec chemin /api/v1/health pour consistance avec le répertoire d'API.
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/docs", tags=["Documentation"], include_in_schema=False)
async def docs_redirect():
    """
    Redirect /docs to /api/docs for backward compatibility.
    Swagger UI docs are available at /api/docs in development mode.
    """
    return RedirectResponse(url="/api/docs")


@app.get("/openapi.json", tags=["Documentation"], include_in_schema=False)
async def openapi_json_redirect():
    """
    Redirect /openapi.json to /api/openapi.json for backward compatibility.
    OpenAPI schema is available at /api/openapi.json in development mode.
    """
    return RedirectResponse(url="/api/openapi.json")


# ==============================================================================
# CLEANUP — Maintenance des données (appelé par le Scheduler)
# ==============================================================================

@app.post("/api/v1/internal/cleanup/sessions", tags=["Maintenance"])
async def cleanup_expired_sessions(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    🧹 Nettoie les sessions expirées et les tokens révoqués anciens.
    
    SÉCURITÉ STRICTE :
     Vérifie le header secret X-Scheduler-Secret
     Vérifie que la requête vient d'une IP interne (whitelist)
     Rate limiting pour éviter les abus
    
    IPs autorisées (réseau interne Docker) :
    - 127.0.0.1 (localhost)
    - 172.17.0.0/16 (default Docker bridge)
    - 172.18.0.0/16 (custom Docker networks)
    - Variables d'env : ALLOWED_INTERNAL_IPS (comma-separated)
    
    Appelé uniquement par le Scheduler via Docker network.
    
    Stratégie de nettoyage :
    1. Supprimer les sessions "access" expirées (< 1 jour après expiration)
    2. Supprimer les sessions "refresh" révoquées (> 30 jours après révocation)
    3. Supprimer les sessions "partial" expirées (< 1 heure après expiration)
    
    Retourne le nombre de lignes supprimées.
    """
    from ipaddress import ip_address, IPv4Network
    
    # ========================================================================
    # 1. VÉRIFIER L'IP SOURCE (WHITELIST STRICTE)
    # ========================================================================
    client_ip = None
    if request.client:
        # Vérifier d'abord X-Forwarded-For (si derrière proxy)
        forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        client_ip = forwarded_for or request.client.host
    
    if not client_ip:
        logger.warning(
            "⚠️  Impossible de déterminer l'IP du client pour /cleanup/sessions"
        )
        raise HTTPException(status_code=403, detail="Cannot determine client IP")
    
    # IPs autorisées par défaut (Docker internal + localhost)
    default_allowed_ips = [
        "127.0.0.1",
        "localhost",
    ]
    default_allowed_networks = [
        IPv4Network("172.17.0.0/16"),  # Docker default bridge
        IPv4Network("172.18.0.0/16"),  # Docker custom networks
        IPv4Network("172.19.0.0/16"),  # Docker networks
        IPv4Network("172.20.0.0/16"),  # Docker networks
    ]
    
    # Charger les IPs supplémentaires depuis env
    extra_ips = os.getenv("ALLOWED_INTERNAL_IPS", "").split(",")
    allowed_ips = default_allowed_ips + [ip.strip() for ip in extra_ips if ip.strip()]
    
    # Vérifier si l'IP du client est autorisée
    is_ip_allowed = client_ip in allowed_ips
    
    # Vérifier les CIDR networks
    if not is_ip_allowed:
        try:
            client_ip_obj = ip_address(client_ip)
            for network in default_allowed_networks:
                if client_ip_obj in network:
                    is_ip_allowed = True
                    break
        except ValueError:
            pass  # Invalid IP format, will reject below
    
    if not is_ip_allowed:
        logger.warning(
            f"🚨 SECURITY ALERT: Tentative d'accès à /cleanup/sessions "
            f"depuis IP NON autorisée : {client_ip}\n"
            f"Autorisées : {allowed_ips} + {default_allowed_networks}"
        )
        raise HTTPException(status_code=403, detail="IP not whitelisted")
    
    # ========================================================================
    # 2. VÉRIFIER LE SECRET
    # ========================================================================
    secret = request.headers.get("X-Scheduler-Secret", "").strip()
    expected_secret = os.getenv("SCHEDULER_SECRET", "")
    
    # Timing-safe comparison pour éviter les timing attacks
    import secrets
    if not secrets.compare_digest(secret, expected_secret):
        logger.warning(
            f"⚠️  Tentative d'accès au cleanup sans secret valide "
            f"depuis IP autorisée {client_ip}"
        )
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # ========================================================================
    # 3. EXÉCUTER LE CLEANUP
    # ========================================================================
    logger.info(f"✅ Cleanup autorisé depuis {client_ip} — exécution...")
    
    now = datetime.now(timezone.utc)
    
    # 1. Supprimer les access sessions expirées depuis > 1 jour
    deleted_access = db.query(AuthSession).filter(
        and_(
            AuthSession.token_type == "access",
            AuthSession.expires_at < (now - timedelta(days=1)),
            AuthSession.revoked_at == None,  # noqa: E711
        )
    ).delete(synchronize_session=False)
    
    logger.info(f"  ✅ {deleted_access} access sessions expirées supprimées")
    
    # 2. Supprimer les refresh sessions révoquées depuis > 30 jours
    deleted_refresh_old = db.query(AuthSession).filter(
        and_(
            AuthSession.token_type == "refresh",
            AuthSession.revoked_at < (now - timedelta(days=30)),
        )
    ).delete(synchronize_session=False)
    
    logger.info(f"  ✅ {deleted_refresh_old} refresh sessions anciennes (révoquées) supprimées")
    
    # 3. Supprimer les partial sessions (2FA) expirées depuis > 1 heure
    deleted_partial = db.query(AuthSession).filter(
        and_(
            AuthSession.token_type == "partial",
            AuthSession.expires_at < (now - timedelta(hours=1)),
        )
    ).delete(synchronize_session=False)
    
    logger.info(f"  ✅ {deleted_partial} partial sessions expirées supprimées")
    
    db.commit()
    
    total_deleted = deleted_access + deleted_refresh_old + deleted_partial
    logger.warning(
        f"✅ CLEANUP COMPLÉTÉ : {total_deleted} sessions supprimées "
        f"(access: {deleted_access}, refresh: {deleted_refresh_old}, partial: {deleted_partial})"
    )
    
    return {
        "status": "success",
        "deleted_access": deleted_access,
        "deleted_refresh_old": deleted_refresh_old,
        "deleted_partial": deleted_partial,
        "total_deleted": total_deleted,
        "timestamp": now.isoformat(),
        "client_ip": client_ip,
    }


# ==============================================================================
# 2. AUTH — Authentification & Sessions
# ==============================================================================

@app.get(
    "/api/v1/auth/check-email",
    tags=["Auth"],
    summary="Vérifier si un email existe déjà"
)
async def check_email(
    email: str = Query(..., description="Email à vérifier"),
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    """
    Vérifier l'unicité d'un email lors de l'inscription.
    
     Public endpoint (aucune auth requise)
    Permet au formulaire d'inscription d'afficher une erreur immédiate
    si l'email est déjà pris (à l'étape 1, pas à l'étape 4).
    
    Args:
        email: Email à vérifier
    
    Returns:
        {"exists": bool}
        - true si l'email existe déjà
        - false si l'email est disponible
    
    Rate limit: Couvert par le middleware existant (10 req/min anonyme)
    """
    from sqlalchemy import select
    
    # Query: SELECT COUNT(*) > 0 FROM users WHERE email = ? AND is_deleted = false
    exists = db.scalar(
        select(exists_fn().where(User.email == email.lower(), User.is_deleted == False))
    )
    
    logger.debug(f"📧 Email check | email={email} | exists={bool(exists)}")
    
    return {"exists": bool(exists)}


@app.post(
    "/api/v1/auth/register",
    response_model=None,
    status_code=201,
    tags=["Auth"],
    summary="4-Step Registration Wizard — Create account, organization, and subscription"
)
async def register(
    request: Request,
    register_data: RegisterRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
     4-STEP REGISTRATION WIZARD ENDPOINT
    
    Handles complete registration flow from the frontend wizard:
    - Step 1: Account (first_name, last_name, email, password)
    - Step 2: Organization (org_name, sector, country, org_size, portals)
    - Step 3: Plan (plan, billing)
    - Step 4: Confirmation (submitted via this endpoint)
    
     CREATES:
    1. New Tenant with organization details (sector, plan, billing, etc.)
    2. New User with credentials
    3. New AuthSession to track the login
    4. AuditLog for registration event
    
     SECURITY:
    - Email uniqueness checked (409 Conflict if exists)
    - Password hashed with Argon2id
    - Rate limiting: 5 registrations per IP per hour (prevent spam)
    - Trial period: 14 days from registration
    - Tokens signed with EdDSA ED25519
    
     SIDE EFFECTS:
    - Sends welcome email via SendGrid (async, non-blocking)
    - Logs audit trail for security monitoring
    
     RETURNS:
    - access_token (15 min JWT)
    - refresh_token (7 days JWT)
    - token_type ("bearer")
    - expires_in (900 seconds = 15 min)
    - user_id, tenant_id, email, tenant_name, trial_ends_at
    """
    
    # ========================================================================
    # 1. VALIDATE EMAIL UNIQUENESS
    # ========================================================================
    existing_user = db.query(User).filter(User.email == register_data.email, User.is_deleted == False).first()
    if existing_user:
        logger.warning(f"⚠️  Registration attempt with duplicate email: {register_data.email}")
        
        # Distinguish between unverified and verified accounts
        if not existing_user.email_verified:
            # Account exists but email not verified — offer to resend verification
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "EMAIL_UNVERIFIED",
                    "message": "Un compte existe avec cette adresse email mais l'email n'a pas été vérifié. "
                               "Vérifiez votre boîte mail ou demandez un nouveau lien de confirmation.",
                    "can_resend": True,
                },
                headers={"X-Error-Code": "email_unverified"}
            )
        else:
            # Account fully registered — redirect to login
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "EMAIL_EXISTS",
                    "message": "Un compte existe déjà avec cette adresse email. Veuillez vous connecter.",
                    "can_resend": False,
                },
                headers={"X-Error-Code": "email_already_registered"}
            )
    
    # ========================================================================
    # 2. CREATE TENANT (Organization)
    # ========================================================================
    # Calculate trial end date: now + 14 days
    trial_ends_at = datetime.now(timezone.utc) + timedelta(days=14)
    
    tenant = Tenant(
        name=register_data.org_name,
        email=register_data.email,
        subscription_plan=register_data.plan or "Avancée",  # Default to "Avancée"
        # New fields for registration wizard
        sector=register_data.sector,
        org_size=register_data.org_size,
        country=register_data.country or "TN",
        portals=register_data.portals or [],  # JSONB array
        plan=register_data.plan or "Avancée",
        billing=register_data.billing or "annual",
        trial_ends_at=trial_ends_at,
    )
    
    try:
        db.add(tenant)
        db.flush()  # Get the tenant ID without committing
    except IntegrityError as e:
        db.rollback()
        
        # Check if it's a duplicate tenant name constraint
        if "tenants_name_key" in str(e) or "unique constraint" in str(e).lower():
            logger.warning(
                f"⚠️  Registration attempt with duplicate organization name: {register_data.org_name}"
            )
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "TENANT_ALREADY_EXISTS",
                    "message": "Une organisation avec ce nom existe déjà sur TenderAI. "
                               "Demandez à votre administrateur de vous inviter."
                },
                headers={"X-Error-Code": "tenant_already_exists"}
            )
        else:
            # Other integrity errors (shouldn't happen, but log them)
            logger.error(f"❌ IntegrityError during tenant creation: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail="Une erreur d'intégrité données est survenue.",
                headers={"X-Error-Code": "integrity_error"}
            )
    
    # ========================================================================
    # 2b. CREATE 6 TENANT-SPECIFIC ROLES
    # ========================================================================
    # Each tenant gets its own set of roles with these exact permissions
    _create_tenant_roles(db=db, tenant_id=tenant.id)
    
    # ========================================================================
    # 3. CREATE USER
    # ========================================================================
    user = User(
        tenant_id=tenant.id,
        email=register_data.email,
        hashed_password=get_password_hash(register_data.password),  # Argon2id
        full_name=f"{register_data.first_name} {register_data.last_name}",
        is_active=True,
        email_verified=False,  # ← User must verify email before accessing system
    )
    
    db.add(user)
    db.flush()  # Get the user ID without committing
    
    # ========================================================================
    # 3b. ASSIGN SUPERADMIN ROLE TO NEW USER (tenant owner)
    # ========================================================================
    # User who registers creates their own tenant → they are superadmin
    # Roles were created in step 2b above
    
    superadmin_role: Optional[Role] = db.query(Role).filter(
        and_(
            Role.tenant_id == tenant.id,
            Role.name == "superadmin"
        )
    ).first()
    
    if superadmin_role:
        user.role_id = superadmin_role.id
        logger.info(f"✅ Assigned superadmin role to new user {user.id} for tenant {tenant.id}")
    else:
        logger.warning(f"⚠️  Superadmin role not found for tenant {tenant.id} — user {user.id} has no role")
    
    # ========================================================================
    # 4. CREATE JWT TOKENS
    # ========================================================================
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent") if request else None
    
    # Create access and refresh tokens
    token_data = {"sub": str(user.id), "tenant_id": str(tenant.id)}
    access_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_delta,
    )
    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=refresh_delta,
    )
    
    # Decode tokens to extract JTI (without verifying signature — we just signed them)
    ap = _jwt.decode(access_token, options={"verify_signature": False})
    rp = _jwt.decode(refresh_token, options={"verify_signature": False})
    
    # ========================================================================
    # 5. CREATE AUTH SESSIONS IN DATABASE
    # ========================================================================
    # Store sessions for later revocation (logout from specific device)
    create_auth_session(
        db=db,
        user_id=user.id,
        tenant_id=tenant.id,
        jti=ap["jti"],
        token_type="access",
        expires_delta=access_delta,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    
    create_auth_session(
        db=db,
        user_id=user.id,
        tenant_id=tenant.id,
        jti=rp["jti"],
        token_type="refresh",
        expires_delta=refresh_delta,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    
    log_action(
        db=db,
        user_id=user.id,
        tenant_id=tenant.id,
        action="user.created",
        resource_type="user",
        resource_id=user.id,
        status="success",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    user.last_login_at = datetime.now(timezone.utc)

    # ========================================================================
    # 6. COMMIT ALL CHANGES TO DATABASE
    # ========================================================================
    db.commit()
    db.refresh(tenant)
    db.refresh(user)
    
    # ========================================================================
    # 7. SEND VERIFICATION EMAIL (async, non-blocking)
    # ========================================================================
    # Create JWT token for email verification (TTL 24h)
    from .security.auth.jwt_handler import get_jwt_handler
    
    jwt_handler = get_jwt_handler()
    verification_token = jwt_handler.create_token(
        data={"sub": str(user.id), "type": "email_verification"},
        expires_delta=timedelta(hours=24),
        token_type="email_verification",
    )
    
    # Create EmailJob for verification email
    # Scheduled to be sent by APScheduler (every 30 seconds)
    from .services.verification_email import create_verification_email_job
    
    verification_job = create_verification_email_job(
        db=db,
        user_id=user.id,
        user_email=register_data.email,
        first_name=register_data.first_name,
        verification_token=verification_token,
        frontend_url=os.getenv("FRONTEND_URL", "https://tenderai.io"),
        tenant_id=tenant.id  # ✅ FIXED: Pass tenant_id (required by DB schema)
    )
    
    logger.info(
        f"📧 Verification email job created | user_id={user.id} | "
        f"email={register_data.email} | job_id={verification_job.id} | "
        f"token_ttl=24h | will be sent by scheduler within 30 seconds"
    )
    
    # ========================================================================
    # 7b. COMMIT VERIFICATION EMAIL JOB TO DATABASE
    # ========================================================================
    # Verification email job is added to session - commit it so scheduler can pick it up
    # Welcome email will be sent AFTER email verification (in verify-email endpoint)
    db.commit()
    
    # ========================================================================
    # 8. CONSTRUCT & RETURN RESPONSE
    # ========================================================================
    access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    expires_in_seconds = access_token_expire_minutes * 60  # Convert to seconds
    
    response_data = RegisterResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in_seconds,
        user_id=user.id,
        tenant_id=tenant.id,
        email=user.email,
        tenant_name=tenant.name,
        trial_ends_at=trial_ends_at,
        email_verified=False,  # ← Must verify email before accessing system
    )
    
    # Set httpOnly cookies for access and refresh tokens
    # Use model_dump(mode='json') for Pydantic v2 to properly serialize UUID fields
    jsonpayload_response = JSONResponse(content=response_data.model_dump(mode='json'))
    set_auth_cookies(jsonpayload_response, access_token, refresh_token)
    
    return jsonpayload_response


@app.post(
    "/api/v1/auth/login",
    response_model=None,
    tags=["Auth"],
    summary="Authentification — retourne les tokens JWT",
    dependencies=[Depends(RateLimitStrict)]
)
async def login(request: Request, credentials: UserLogin = Body(...), db: Session = Depends(get_db)):
    """
    FEATURE 1 : Authentification JWT
    ==================================

     FLUX COMPLET DU LOGIN :
    ---------------------------
    1. Vérifier le rate limit (5 tentatives par minute par IP)
    2. Vérifier l'email + le mot de passe (Argon2id)
    3. Créer un ACCESS TOKEN (15 min) avec tenant_id dans le payload
    4. Créer un REFRESH TOKEN (7 jours) avec tenant_id dans le payload
    5. Enregistrer les sessions en DB (pour pouvoir les révoquer)
    6. Logger la tentative (audit trail)
    7. Retourner les deux tokens au client

     TENANT_ID DANS LE TOKEN (FEATURE 2) :
    ------------------------------------------
    Le token contient {"sub": "user-uuid", "tenant_id": "tenant-uuid", ...}
    Ce tenant_id est signé avec la clé secrète du serveur.
    → Impossible pour le client de le modifier sans invalider la signature.
    → C'est le SEUL endroit où tenant_id est défini. Le frontend ne l'envoie
      JAMAIS dans les requêtes suivantes — il vit dans le token.


    RATE LIMITING : 5 tentatives par minute par IP (protection brute-force).
    """
    # ── Étape 0 : Vérifier le rate limit ──────────────────────────────────────
    # Rate limit enforced via dependencies=[Depends(RateLimitStrict)]
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent")

    # ── Vérification des credentials ──────────────────────────────────────────
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        #  Message générique intentionnel : on ne révèle pas si l'email existe
        record_login_attempt(
            db=db,
            email=credentials.email,
            success=False,
            failure_reason="bad_password" if user else "user_not_found",
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user.id if user else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        record_login_attempt(
            db=db,
            email=credentials.email,
            success=False,
            failure_reason="account_inactive",
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user.id,
        )
        raise HTTPException(status_code=403, detail="Compte désactivé")

    # ── Check if email is verified ──────────────────────────────────────────
    if not user.email_verified:
        record_login_attempt(
            db=db,
            email=credentials.email,
            success=False,
            failure_reason="email_not_verified",
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user.id,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Vérifiez votre email avant de vous connecter. "
                           "Un lien de confirmation a été envoyé à votre adresse email."
            }
        )

    # ── Check if 2FA is enabled ────────────────────────────────────────────
    totp_record: Optional[UserTOTP] = db.query(UserTOTP).filter(
        and_(UserTOTP.user_id == user.id, UserTOTP.is_enabled == True)  # noqa: E712
    ).first()
    
    if totp_record:
        # 2FA is enabled → return partial_token, frontend redirects to /2fa-login
        from .security import create_partial_token
        
        partial_token_data: Dict[str, Any] = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "email": user.email,
        }
        partial_token: str = create_partial_token(
            data=partial_token_data,
            expires_delta=timedelta(minutes=5),
        )
        
        pp = _jwt.decode(partial_token, options={"verify_signature": False})
        auth_session = AuthSession(
            user_id=user.id,
            tenant_id=user.tenant_id,
            jti=pp.get("jti"),
            token_type="partial",
            expires_at=datetime.fromtimestamp(pp.get("exp"), tz=timezone.utc),
            revoked_at=None,
        )
        db.add(auth_session)
        db.commit()
        
        # Log successful email/password auth, now awaiting 2FA
        record_login_attempt(
            db=db,
            email=credentials.email,
            success=True,
            failure_reason=None,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user.id,
        )
        
        return JSONResponse(
            content={
                "requires_2fa": True,
                "partial_token": partial_token,
                "token_type": "partial",
                "expires_in": 300,  # 5 minutes
            },
            status_code=200,
        )
    else:
        # 2FA not configured → proceed with full token creation
        pass

    if password_needs_rehash(user.hashed_password):
        logger.info(f"🔄 Rehashing password for user {user.id} — security params updated")
        user.hashed_password = get_password_hash(credentials.password)
        # Commit immédiat pour que le nouveau hash soit persisté
        # (on aura un autre commit plus tard, mais celui-ci garantit la durabilité)
        db.commit()
    
    # ── Création des tokens ──────────────────────────────────────────────────
    token_data   = {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    access_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data=token_data,
        expires_delta=access_delta,
    )
    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    # ── Enregistrement des sessions en DB ─────────────────────────────────────
    # On stocke le JTI de chaque token pour pouvoir les révoquer lors du logout.
    # Sans ça, un token volé resterait valide jusqu'à son expiration naturelle.
    # Décoder sans vérification de signature (on vient de les signer nous-même)
    ap = _jwt.decode(access_token, options={"verify_signature": False})
    rp = _jwt.decode(refresh_token, options={"verify_signature": False})

    # ── Appliquer la limite de sessions ──────────────────────────────────────
    from app.auth import enforce_session_limit, MAX_SESSIONS
    
    enforce_session_limit(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        max_sessions=MAX_SESSIONS,
    )
   
    create_auth_session(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        jti=ap["jti"],
        token_type="access",
        expires_delta=access_delta,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    
    create_auth_session(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        jti=rp["jti"],
        token_type="refresh",
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=user_agent,
        ip_address=ip_address,
    )
  
    db.commit()
    
    # ── Audit ──────────────────────────────────────────────────────────────────
    record_login_attempt(
        db=db,
        email=credentials.email,
        success=True,
        ip_address=ip_address,
        user_agent=user_agent,
        user_id=user.id,
    )
    
   
    user.last_login_at = datetime.now(timezone.utc)
    
    # PROBLÈME 3 : Calculer le vrai hash SHA-256 au lieu de "pending"
    from .security.audit import compute_audit_hash, get_previous_audit_hash
    previous_hash = get_previous_audit_hash(db)
    entry_data = {
        "tenant_id": str(user.tenant_id),
        "user_id": str(user.id),
        "action": "login",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip_address": ip_address,
    }
    
    audit_log = AuditLog(
        tenant_id=user.tenant_id,
        user_id=user.id,
        action="session.started",
        resource_type="auth",
        resource_id=user.id,
        status="success",
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc),
        hash=compute_audit_hash(entry_data, previous_hash),
        previous_hash=previous_hash,
    )
    db.add(audit_log)
    db.commit()

   
    response = JSONResponse(
        content={
            "token_type": "bearer",
            "expires_in": int(access_delta.total_seconds()),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "tenant_id": str(user.tenant_id),
            }
        }
    )
    
    # Set auth cookies with centralized security configuration
    set_auth_cookies(response, access_token, refresh_token)
    
    return response


@app.get(
    "/api/v1/auth/verify-email",
    tags=["Auth"],
    summary="Vérifier email via lien de confirmation",
    dependencies=[Depends(RateLimitEmailVerify)]
)
async def verify_email(
    request: Request,
    token: str = Query(..., description="JWT token from verification email"),
    db: Session = Depends(get_db),
):
    """
    Valide le lien de confirmation d'email.
    
    FLUX:
    1. Après registration, backend envoie email avec lien :
       /register/verify-email?token=xxx
    2. User clique lien → Frontend appelle ce endpoint (PUBLIC, pas d'auth)
    3. Backend valide le token JWT (TTL 24h)
    4. Backend set user.email_verified = true
    5. Backend retourne message de confirmation
    
    Après cette vérification, le user peut se connecter et doit setup 2FA.
    """
    
    # Rate limiting enforced via dependencies=[Depends(RateLimitEmailVerify)]
    ip_address = get_client_ip(request)
    
    # Validate and decode JWT
    try:
        from .security.auth.jwt_handler import get_jwt_handler
        
        jwt_handler = get_jwt_handler()
        payload = jwt_handler.verify_token(token)
        
        # Ensure it's an email verification token
        if payload.get("type") != "email_verification":
            raise HTTPException(
                status_code=400,
                detail="Lien de vérification invalide"
            )
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=400,
                detail="Lien de vérification invalide (pas d'utilisateur)"
            )
        
        user_id = UUID(user_id_str)
    except JWTError as e:
        logger.warning(f"⚠️  Invalid email verification token: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Lien de vérification expiré ou invalide. "
                   "Veuillez demander un nouveau lien."
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Lien de vérification invalide"
        )
    
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"⚠️  Email verification attempt for non-existent user {user_id}")
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Check if already verified
    if user.email_verified:
        logger.info(f"✅ User {user.id} email already verified")
        return JSONResponse(
            status_code=200,
            content={
                "message": "Votre email est déjà vérifié. "
                           "Connectez-vous pour continuer.",
                "email_verified": True,
                "next_step": "/register/setup-2fa"
            }
        )
    
    # Mark email as verified
    user.email_verified = True
    log_action(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        action="user.email_verified",
        resource_type="user",
        resource_id=user.id,
        status="success",
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    
    # ========================================================================
    # CREATE WELCOME EMAIL JOB (AFTER email verification)
    # ========================================================================
    # Now that user has verified email, create and send welcome email
    from .services.welcome_email import create_welcome_email_job
    
    # Get tenant to access trial_ends_at and org name
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        logger.error(f"❌ Tenant not found for user {user.id}")
    else:
        trial_ends_at_iso = tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else ""
        
        # Split full_name into first_name and last_name
        name_parts = user.full_name.split(" ", 1) if user.full_name else ["", ""]
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        welcome_job = create_welcome_email_job(
            db=db,
            user_id=user.id,
            user_email=user.email,
            first_name=first_name,
            last_name=last_name,
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            trial_ends_at=trial_ends_at_iso,
            frontend_url=os.getenv("FRONTEND_URL", "https://tenderai.io")
        )
        
        logger.info(
            f"📧 Welcome email job created | user_id={user.id} | "
            f"email={user.email} | job_id={welcome_job.id} | "
            f"tenant_name={tenant.name} | trial_ends_at={trial_ends_at_iso}"
        )
    
    db.commit()
    
    logger.info(f"✅ Email verified for user {user.id} ({user.email})")
    
    # ========================================================================
    # Issue fresh tokens with email_verified=True confirmed by backend
    # ========================================================================
    # User already has tokens from registration, but we issue fresh ones
    # to confirm email verification on the server side (role already assigned)
    token_data = {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    access_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_delta,
    )
    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=refresh_delta,
    )
    
    # ── Register tokens in auth_sessions DB (for JTI revocation tracking) ──────
    # Same pattern as login endpoint — decode tokens and create session records
    ap = _jwt.decode(access_token, options={"verify_signature": False})
    rp = _jwt.decode(refresh_token, options={"verify_signature": False})

    user_agent = request.headers.get("user-agent") if request else None
    ip_address = get_client_ip(request)
    
    create_auth_session(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        jti=ap["jti"],
        token_type="access",
        expires_delta=access_delta,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    
    create_auth_session(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        jti=rp["jti"],
        token_type="refresh",
        expires_delta=refresh_delta,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    
    db.commit()
    
    # Create response with fresh tokens as httpOnly cookies
    response = JSONResponse(
        status_code=200,
        content={
            "message": "Votre email est maintenant vérifié. "
                       "Veuillez configurer votre authentification 2FA.",
            "email_verified": True,
            "next_step": "/register/setup-2fa"
        }
    )
    set_auth_cookies(response, access_token, refresh_token)
    return response


@app.post(
    "/api/v1/auth/resend-verification",
    tags=["Auth"],
    summary="Renvoyer le lien de vérification d'email",
    dependencies=[Depends(RateLimitResend)]
)
async def resend_verification(
    request: Request,
    body: dict = Body(..., example={"email": "user@example.com"}),
    db: Session = Depends(get_db),
):
    """
    Renvoie un nouveau lien de vérification d'email.
    
     FLUX:
    1. Frontend envoie email
    2. Backend cherche user par email
    3. Si email_verified == True → 400 "Email déjà vérifié"
    4. Si user n'existe pas → 404
    5. Rate limit: max 3 renvois par heure par email
    6. Génère nouveau token EdDSA TTL 24h
    7. Crée nouveau EmailJob type EMAIL_VERIFICATION
    8. Retourne 200 {"message": "Email envoyé"}
    """
    
    # Rate limiting enforced via dependencies=[Depends(RateLimitResend)]
    ip_address = get_client_ip(request)
    
    # Extract email from body
    email = body.get("email", "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email est requis"
        )
    
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # For security, don't reveal whether email exists
        logger.info(f"ℹ️  Resend verification requested for non-existent email: {email}")
        return JSONResponse(
            status_code=200,
            content={
                "message": "Si ce compte existe, un email de vérification sera envoyé."
            }
        )
    
    # Check if already verified
    if user.email_verified:
        logger.info(f"✅ Resend verification requested for already verified user: {user.id}")
        return JSONResponse(
            status_code=200,
            content={
                "message": "Votre email est déjà vérifié. Vous pouvez vous connecter.",
                "email_verified": True
            }
        )
    
    # Generate new verification token
    from .security.auth.jwt_handler import get_jwt_handler
    
    jwt_handler = get_jwt_handler()
    verification_token = jwt_handler.create_token(
        data={"sub": str(user.id), "type": "email_verification"},
        expires_delta=timedelta(hours=24),
        token_type="email_verification",
    )
    
    # Create new EmailJob
    from .services.verification_email import create_verification_email_job
    
    verification_job = create_verification_email_job(
        db=db,
        user_id=user.id,
        user_email=user.email,
        first_name=user.full_name.split()[0] if user.full_name else "User",
        verification_token=verification_token,
        frontend_url=os.getenv("FRONTEND_URL", "https://tenderai.io"),
        tenant_id=user.tenant_id  # ✅ FIXED: Pass tenant_id from user (user already has tenant)
    )
    
    db.commit()
    
    logger.info(
        f"📧 Verification email resent | user_id={user.id} | "
        f"email={user.email} | job_id={verification_job.id} | "
        f"token_ttl=24h"
    )
    
    log_action(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        action="user.verification_email_resent",
        resource_type="user",
        resource_id=user.id,
        status="success",
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    
    return JSONResponse(
        status_code=200,
        content={
            "message": "Un nouveau lien de vérification a été envoyé à votre email.",
            "email": user.email
        }
    )


@app.get(
    "/api/v1/auth/me",
    response_model=UserProfileResponse,
    tags=["Auth"],
    summary="Profil complet (user + tenant) — pour AuthContext.jsx"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),  # ← Vérifie le JWT automatiquement
    db: Session        = Depends(get_db),
):
    """
    Retourne le profil enrichi de l'utilisateur connecté.

    
    NOTE SUR get_current_user :
    Grâce à Depends(get_current_user), FastAPI a déjà :
    1. Extrait le JWT du header Authorization
    2. Vérifié la signature
    3. Vérifié que le JTI n'est pas révoqué
    4. Chargé l'objet User depuis la DB
    On n'a pas besoin de refaire tout ça ici.
    """
    # Charger le tenant pour avoir son nom et son plan
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant introuvable")

    # Récupérer le nom lisible du rôle (si l'utilisateur en a un)
    role_name = None
    if current_user.role_id:
        role_obj = db.query(Role).filter(Role.id == current_user.role_id).first()
        role_name = role_obj.name if role_obj else None

    # Vérifier si l'utilisateur a 2FA activée
    user_totp = db.query(UserTOTP).filter(
        UserTOTP.user_id == current_user.id,
        UserTOTP.is_enabled,
    ).first()
    totp_enabled = user_totp is not None

    # La couleur accent est optionnelle, stockée dans tenant_metadata
    meta = tenant.tenant_metadata or {}

    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=role_name,
        is_active=current_user.is_active,
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at,
        tenant_id=current_user.tenant_id,
        tenant_name=tenant.name,                    
        subscription_plan=tenant.subscription_plan,
        tenant_color=meta.get("color"),
        totp_enabled=totp_enabled,
    )


@app.patch(
    "/api/v1/auth/me",
    response_model=UserProfileResponse,
    tags=["Auth"],
    summary="Modifier le profil utilisateur"
)
async def update_user_profile(
    update_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Modifie le profil de l'utilisateur connecté (full_name uniquement).
    Email ne peut être modifié ici — flow séparé nécessaire.
    """
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name

    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)

    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant introuvable")

    role_name = None
    if current_user.role_id:
        role_obj = db.query(Role).filter(Role.id == current_user.role_id).first()
        role_name = role_obj.name if role_obj else None

    user_totp = db.query(UserTOTP).filter(
        UserTOTP.user_id == current_user.id,
        UserTOTP.is_enabled,
    ).first()
    totp_enabled = user_totp is not None

    meta = tenant.tenant_metadata or {}

    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="user.profile_updated",
        resource_type="user",
        resource_id=current_user.id,
        new_value={"full_name": current_user.full_name},
        status="success",
        ip_address=get_client_ip(None),
        user_agent=None,
    )

    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=role_name,
        is_active=current_user.is_active,
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at,
        tenant_id=current_user.tenant_id,
        tenant_name=tenant.name,
        subscription_plan=tenant.subscription_plan,
        tenant_color=meta.get("color"),
        totp_enabled=totp_enabled,
    )

@app.post(
    "/api/v1/auth/refresh",
    response_model=None,
    tags=["Auth"],
    summary="Renouveler l'access token avec le refresh token",
    dependencies=[Depends(RateLimitRefresh)]
)
async def refresh_token_endpoint(
    request: Request,
    db: Session = Depends(get_db),
):
    
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ============================================================================
    # RATE LIMITING FOR REFRESH TOKEN ENDPOINT (B2B Multi-Device Support)
    # ============================================================================

   
    user_agent = request.headers.get("User-Agent")
    ip_address = get_client_ip(request)
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token invalide ou expiré.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Vérifier la signature du refresh token
    try:
        payload = verify_token(refresh_token)
    except JWTError:
        raise credentials_exception

    # S'assurer que c'est bien un refresh token (pas un access token)
    if payload.get("type") != "refresh":
        raise credentials_exception

    user_id   = payload.get("sub")
    tenant_id = payload.get("tenant_id")  # Extrait du token → fiable, non falsifiable
    jti       = payload.get("jti")

    if not user_id or not tenant_id:
        raise credentials_exception
    now = datetime.now(timezone.utc)
    session = db.query(AuthSession).filter(
        AuthSession.jti == jti
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session.ensure_timezone_aware()
    if session.revoked_at is not None and session.replaced_by is not None:
        logger.warning(
            f"SECURITY ALERT: Suspected token theft! "
            f"Revoked refresh token (JTI={jti}) reused after replacement (replaced_by={session.replaced_by}). "
            f"User={user_id}, Tenant={tenant_id}"
        )
        log_action(
            db=db,
            tenant_id=UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            action="session.suspicious",
            resource_type="auth",
            resource_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            reason="Suspected token theft - revoked token reuse",
            status="failed",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent") if request else None,
        )
        db.query(AuthSession).filter(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at == None  # noqa: E711
        ).update({"revoked_at": datetime.now(timezone.utc)})
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Activité suspecte détectée. Toutes vos sessions ont été révoquées. Reconnectez-vous.",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Cas 2 — Révocation normale (logout, password reset)
    elif session.revoked_at is not None:
        log_action(
            db=db,
            tenant_id=UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            action="session.rejected",
            resource_type="auth",
            resource_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            reason="Revoked session reuse attempt",
            status="failed",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent") if request else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session révoquée. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"},
        )

#  Cas 3 — Token expiré
    elif session.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Vérifier que l'utilisateur est toujours actif
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()
    except ValueError:
        raise credentials_exception

    if not user or not user.is_active:
        raise credentials_exception

    enforce_session_limit(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        max_sessions=MAX_SESSIONS,
    )

    # Générer un nouvel access token (tenant_id vient de l'objet user en DB)
    access_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access   = create_access_token(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id)},
        expires_delta=access_delta,
    )

    # Générer les tokens avant d'enregistrer les sessions (pour éviter les race conditions)
    refresh_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh = create_refresh_token(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id)},
        expires_delta=refresh_delta,
    )
    
    # Décoder pour obtenir les JTI
    ap = verify_token(new_access)
    rp = verify_token(new_refresh)
    new_jti = rp["jti"]
    
    # ========================================================================
    # Revoke OLD session BEFORE creating NEW ones
    # This prevents race condition where two concurrent refreshes create duplicate sessions
    # ========================================================================
    if jti and session:
        from sqlalchemy import update
        
        # Only update if revoked_at is still NULL (not yet revoked by another concurrent refresh)
        stmt = update(AuthSession).where(
            and_(
                AuthSession.jti == jti,
                AuthSession.revoked_at == None  # noqa: E711
            )
        ).values(
            last_used_at=datetime.now(timezone.utc),
            replaced_by=UUID(new_jti) if isinstance(new_jti, str) else new_jti,
            revoked_at=datetime.now(timezone.utc)
        )
        result = db.execute(stmt)
        
        # Only proceed if we successfully updated the old session
        if result.rowcount == 0:
            # This refresh token was already replaced/revoked by another concurrent request
            logger.warning(
                f"⚠️ Concurrent refresh detected: JTI {jti} already revoked by another request. "
                f"User will need to login again. (User={user_id})"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expiré. Une autre session a renouvellé le token. Reconnectez-vous.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            logger.debug(f"✅ Old refresh session revoked: {jti} → {new_jti}")
    
    # ========================================================================
    # NOW create new sessions (after old one is safely revoked)
    # ========================================================================
    
    # Create new access session
    create_auth_session(db, user.id, user.tenant_id, ap["jti"], "access", access_delta, 
                       user_agent=user_agent, ip_address=ip_address)
    
    # Create new refresh session
    create_auth_session(db, user.id, user.tenant_id, new_jti, "refresh", refresh_delta,
                       user_agent=user_agent, ip_address=ip_address)

    # Log token refresh
    log_action(
        db=db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        action="session.refreshed",
        resource_type="auth",
        resource_id=user.id,
        new_value={"user_id": str(user.id), "tenant_id": str(user.tenant_id)},
        status="success",
        reason="Access token refreshed",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.commit()

  
    response = JSONResponse(
        content={
            "token_type": "bearer",
            "expires_in": int(access_delta.total_seconds()),
            "refreshed": True
        }
    )
    
    # Set auth cookies with centralized security configuration
    set_auth_cookies(response, new_access, new_refresh)
    
    return response


# ==============================================================================
#  PASSWORD RESET ENDPOINTS (P0 features)
# ==============================================================================

@app.post(
    "/api/v1/auth/password-reset/request",
    tags=["Auth"],
    summary="Demander une réinitialisation de mot de passe",
    status_code=200,
    responses={
        200: {
            "description": "Always returns 200 OK (no user enumeration)"
        }
    }
)
async def password_reset_request(
    body: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    REQUEST PASSWORD RESET LINK
    
     Sends a password reset email with a secure token
    
     SECURITY: No user enumeration
    - Always returns 200 OK (even if email doesn't exist)
    - Email sent only if user exists
    - Generic response message
    - Attempt logged for abuse detection
    
     EMAIL DELIVERY:
    - Sent via Resend API (async via scheduler every 30s)
    - Token valid for 1 hour
    - Token stored in Redis (no database logging of actual token)
    
     USAGE:
    1. User enters email on /forgot-password page
    2. Scheduler sends email with reset link
    3. User clicks link → goes to /password-reset?token=xxx
    4. User enters new password → POST /password-reset/confirm
    """
    from app.services.password_reset import handle_password_reset_request
    
    logger.info(f"📧 Password reset requested | email={body.email}")
    
    try:
        handle_password_reset_request(
            db=db,
            email=body.email
        )
    
    except Exception as e:
        logger.error(
            f"❌ Error in password reset request | email={body.email} | error={str(e)}",
            exc_info=True
        )
        # Still return success to client (don't reveal internal errors)
    
    # Always return success message (no user enumeration)
    return {
        "status": "success",
        "message": "Si cette adresse email existe, vous recevrez un lien pour réinitialiser votre mot de passe."
    }


@app.post(
    "/api/v1/auth/password-reset/confirm",
    response_model=PasswordResetResponse,
    tags=["Auth"],
    summary="Confirmer la réinitialisation de mot de passe",
)
async def password_reset_confirm(
    body: PasswordResetConfirm,
    db: Session = Depends(get_db),
) -> dict:
    """
    CONFIRM PASSWORD RESET

     Resets password after token verification
    
     SECURITY:
    - Token validated in Redis (1-hour TTL)
    - Token is single-use (deleted after verification)
    - Password hashed with Argon2id (OWASP standard)
    - Rate limited to prevent brute force
    
     FLOW:
    1. Verify token exists and is not expired
    2. Retrieve user_id from token
    3. Hash new password (Argon2id)
    4. Update user record
    5. Return success
    
     ERROR CASES:
    - 400: Invalid or expired token
    - 400: User not found or inactive
    - 422: Password too weak (< 8 chars)
    """
    from app.services.password_reset import handle_password_reset_confirm
    
    logger.info("🔐 Password reset confirmation requested")
    
    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long"
        )
    
    try:
        success, message = handle_password_reset_confirm(
            db=db,
            token=body.token,
            new_password=body.password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return {
            "status": "success",
            "message": message
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Unexpected error in password reset confirm | error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password reset"
        )


# ==============================================================================
# 👥 USER INVITATION ENDPOINTS (P0 features)
# ==============================================================================

@app.post(
    "/api/v1/admin/users/invite",
    tags=["Users"],
    summary="Inviter un nouvel utilisateur (Admin uniquement)",
    status_code=201,
)
async def invite_user(
    body: UserInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    INVITE NEW USER
    
     Send an invitation email to a new user
    
     SECURITY:
    - Admin/Superadmin RBAC (role-based access control)
    - Tenant isolation: can only invite within own tenant
    - Email validation
    
     EMAIL:
    - Sent via Resend API (async)
    - Valid for 7 days
    - Contains personalized invite link
    
     USAGE:
    1. Admin fills form: email + role
    2. Invitation email sent to new user
    3. User clicks link → /auth/invite/accept?token=xxx
    4. User sets password → account created
    """
    from app.services.user_invitation import send_user_invitation
    
    # Check RBAC: Admin or Superadmin only
    if current_user.role and current_user.role.name not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can invite users"
        )
    
    # Prevent duplicate invitations
    existing_user = db.query(User).filter(
        User.email == body.email.lower(),
        User.tenant_id == current_user.tenant_id
    ).first()
    
    if existing_user:
        if existing_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists in this organization"
            )
    
    logger.info(
        f"👥 User invitation request | inviter={current_user.id} | "
        f"email={body.email} | role={body.role}"
    )
    
    try:
        success, result = send_user_invitation(
            db=db,
            recipient_email=body.email.lower(),
            inviter_id=current_user.id,
            tenant_id=current_user.tenant_id,
            inviter_name=current_user.full_name or current_user.email,
            organization_name=current_user.tenant.name if current_user.tenant else "TenderAI",
            role=body.role
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result
            )
        
        return {
            "status": "success",
            "message": f"Invitation sent to {body.email}",
            "token": result  # For testing/debug (optional)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error sending invitation | email={body.email} | error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending the invitation"
        )


@app.post(
    "/api/v1/auth/invite/accept",
    response_model=AcceptInvitationResponse,
    tags=["Auth"],
    summary="Accepter une invitation et créer un compte",
    status_code=201,
)
async def accept_invitation(
    body: AcceptInvitationRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    ACCEPT INVITATION & CREATE ACCOUNT
    
     New user accepts invitation and sets up account
    
     SECURITY:
    - Token validated in Redis (7-day TTL)
    - Token is single-use (deleted after verification)
    - Password hashed with Argon2id
    
     FLOW:
    1. Verify token exists and not expired
    2. Extract inviter_id, email, role from token
    3. Check user doesn't already exist
    4. Create new account with invited_by tracking
    5. Assign role from invitation
    6. Return success
    
     ERROR CASES:
    - 400: Invalid or expired token
    - 400: User already exists
    - 422: Data validation error
    """
    from app.services.user_invitation import accept_user_invitation
    
    logger.info("👥 Invitation acceptance requested")
    
    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long"
        )
    
    try:
        success, message = accept_user_invitation(
            db=db,
            token=body.token,
            full_name=body.full_name,
            password=body.password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return {
            "status": "success",
            "message": message
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Unexpected error accepting invitation | error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while accepting the invitation"
        )


@app.post(
    "/api/v1/auth/logout",
    tags=["Auth"],
    summary="Déconnexion — révoque la session courante"
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session        = Depends(get_db),
    token: str         = Depends(oauth2_scheme),
):
    """
    

    Révoque la session JWT courante dans auth_sessions (revoked_at = NOW()).

    Après ce logout, toute requête avec ce token recevra un 401, même si
    le token n'est pas encore expiré selon sa date d'expiration.

    Grâce à la vérification JTI dans get_current_user(), la révocation
    en base de données est vérifiée à chaque requête.
    Sans ce mécanisme, l'utilisateur resterait "connecté" 15 min après logout.
    """
    # Extraire le JTI du token pour identifier la session à révoquer
    try:
        payload = verify_token(token)
        jti     = payload.get("jti")
        if jti:
            revoke_auth_session(db, jti)  # Marque revoked_at = NOW() en DB
    except Exception:
        pass  # Si le token est déjà invalide, on répond OK quand même
              # (le client supprime ses tokens locaux de toute façon)

    # Log successful logout to audit trail
    ip_address = get_client_ip(request)
    
    # Compute audit hash for this entry using previous hash from DB
    from .security.audit import compute_audit_hash, get_previous_audit_hash
    previous_hash = get_previous_audit_hash(db)
    entry_data = {
        "tenant_id": str(current_user.tenant_id),
        "user_id": str(current_user.id),
        "action": "session.ended",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip_address": ip_address,
    }
    
    audit_log = AuditLog(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="session.ended",
        resource_type="auth",
        resource_id=current_user.id,
        status="success",
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc),
        hash=compute_audit_hash(entry_data, previous_hash),
        previous_hash=previous_hash,
    )
    db.add(audit_log)
    db.commit()

    response = JSONResponse(content={"message": "Logged out successfully"})
    
    # Delete both auth cookies with centralized security configuration
    delete_auth_cookies(response)

    return response


@app.post(
    "/api/v1/auth/change-password",
    response_model=ChangePasswordResponse,
    tags=["Auth"],
    summary="Changer le mot de passe",
    status_code=status.HTTP_200_OK,
)
async def change_password(
    request: Request,
    change_request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change the password of the current user with verification of the old password.
    Revokes all other sessions for security.
    """
    if change_request.new_password != change_request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Les mots de passe ne correspondent pas"
        )

    if change_request.current_password == change_request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe doit être différent de l'ancien"
        )

    if not verify_password(change_request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect"
        )

    current_user.hashed_password = get_password_hash(change_request.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()

    sessions_to_revoke = db.query(AuthSession).filter(
        and_(
            AuthSession.user_id == current_user.id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(timezone.utc),
        )
    ).all()

    for session in sessions_to_revoke:
        session.revoked_at = datetime.now(timezone.utc)
    db.commit()

    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="auth.password_changed",
        resource_type="user",
        resource_id=current_user.id,
        status="success",
        reason="Password changed — all other sessions revoked",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return ChangePasswordResponse(
        message="Mot de passe modifié avec succès"
    )


# ==============================================================================
# 3. DOCUMENTS-ME — Toutes les routes documents (tenant_id du JWT uniquement)
# ==============================================================================

@app.get(
    "/api/v1/me/documents",
    response_model=PaginatedResponse,
    tags=["Documents"],
    summary="Liste les documents du tenant connecté (tenant_id = JWT)"
)
async def list_my_documents(
    page:     int           = Query(1, ge=1),
    limit:    int           = Query(20, ge=1, le=100),
    status:   Optional[str] = Query(None, description="Filtre par statut"),
    search:   Optional[str] = Query(None, description="Recherche dans le nom du fichier"),
    ordering: str           = Query("-created_at", description="Tri. Préfixe '-' = décroissant"),
    current_user: User      = Depends(get_current_user),  # FEATURE 1 + 2
    db: Session             = Depends(get_db),
):
    """
    DÉMONSTRATION COMPLÈTE DES 3 FEATURES
    =======================================

     get_current_user() vérifie le JWT et charge l'utilisateur
       → current_user.tenant_id = UUID extrait du token (jamais de l'URL)

     set_tenant_context() active le RLS dans PostgreSQL
       → SET LOCAL app.current_tenant = 'uuid-buildcorp'

     La requête SQL est automatiquement filtrée par PostgreSQL
       → WHERE tenant_id = 'uuid-buildcorp' appliqué par la policy RLS

    Résultat :
      Alice (BuildCorp) → voit UNIQUEMENT les docs de BuildCorp
      Sarah (AquaTech)  → voit UNIQUEMENT les docs d'AquaTech
      Même endpoint, même code, isolation garantie.
    """
    
    # Set tenant context on THIS session before querying
    from .database import set_tenant_context
    set_tenant_context(db, current_user.tenant_id)
    
    logger.info(f"🔐 LIST DOCUMENTS: user={current_user.email} | tenant_id={current_user.tenant_id}")
    # Le filtre tenant_id est redondant avec RLS, mais le rendre explicite
    # aide à la lisibilité et constitue une 2e couche de sécurité applicative.
    query = db.query(Document).filter(
        and_(
            Document.tenant_id == current_user.tenant_id,
            ~Document.is_deleted,
        )
    )

    # Filtres optionnels transmis par le frontend (query params)
    if status:
        query = query.filter(Document.status == status)
    if search:
        query = query.filter(Document.filename.ilike(f"%{search}%"))

    # Tri dynamique : "-created_at" → ORDER BY created_at DESC
    if ordering.startswith("-"):
        col = getattr(Document, ordering[1:], Document.created_at)
        query = query.order_by(desc(col))
    else:
        col = getattr(Document, ordering, Document.created_at)
        query = query.order_by(col)

    total  = query.count()
    offset = (page - 1) * limit
    items  = query.offset(offset).limit(limit).all()

    return PaginatedResponse(
        items=[DocumentResponse.model_validate(d) for d in items],
        total=total,
        page=page,
        page_size=limit,
        pages=(total + limit - 1) // limit if limit else 1,
    )


@app.post(
    "/api/v1/me/documents",
    response_model=DocumentResponse,
    status_code=201,
    tags=["Documents"],
    summary="Créer un document pour le tenant connecté (tenant_id = JWT)"
)
async def create_my_document(
    doc_data: DocumentCreate,
    current_user: User = Depends(get_current_user),  # FEATURE 1 + 2
    db: Session        = Depends(get_db),
):
    """
    Créer un document.

    Le tenant_id du document est défini par le serveur depuis le JWT.
    Le client ne peut pas créer un document dans un autre tenant.
        
       POST /api/v1/me/documents
       → tenant_id = current_user.tenant_id (extrait du JWT)
    """
    

    document = Document(
        # tenant_id vient du JWT, jamais du body de la requête
        tenant_id=current_user.tenant_id,
        filename=doc_data.filename,
        storage_path=doc_data.storage_path,
        file_size=doc_data.file_size,
        mime_type=doc_data.mime_type,
        language=doc_data.language or "fr",
        document_metadata=doc_data.document_metadata or {},
        uploaded_by=current_user.id,
        created_by=current_user.id,
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Log document creation
    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="document.created",
        resource_type="document",
        resource_id=document.id,
        new_value={
            "filename": document.filename,
            "file_size": document.file_size,
            "mime_type": document.mime_type,
            "status": document.status,
        },
        status="success",
        reason=f"Document '{document.filename}' created",
        ip_address=None,
        user_agent=None,
    )
    db.commit()
    
    return document


@app.get(
    "/api/v1/me/documents/stats",
    response_model=DocumentStatsResponse,
    tags=["Documents"],
    summary="Statistiques du tableau de bord (tenant_id = JWT)"
)
async def get_my_document_stats(
    current_user: User = Depends(get_current_user),
    db: Session        = Depends(get_db),
):
    """
    Calcule les statistiques pour le tableau de bord du tenant connecté.

    Toutes les statistiques sont isolées par RLS — un tenant ne voit
    jamais les chiffres d'un autre tenant.

    Retourne :
        total          : nombre total de documents
        completed      : documents avec status="completed"
        processing     : documents en cours de traitement
        avg_score      : score moyen de conformité (depuis document_metadata)
        total_budget   : somme des budgets (depuis document_metadata)
        next_deadline  : prochain appel d'offres à échéance
    """
    
    # Set tenant context on THIS session before querying
    from .database import set_tenant_context
    set_tenant_context(db, current_user.tenant_id)
    base = db.query(Document).filter(
        and_(
            Document.tenant_id == current_user.tenant_id,
            ~Document.is_deleted,
        )
    )

    total      = base.count()
    completed  = base.filter(Document.status == "completed").count()
    processing = base.filter(Document.status.in_(["processing", "uploaded"])).count()

    # Extraction des valeurs depuis document_metadata (champ JSON flexible)
    # Ex: {"compliance_score": 87, "budget_eur": 5000000, "deadline": "2026-06-01"}
    docs = base.all()

    scores  = [
        d.document_metadata.get("compliance_score")
        for d in docs
        if d.document_metadata and d.document_metadata.get("compliance_score") is not None
    ]
    budgets = [
        d.document_metadata.get("budget_eur")
        for d in docs
        if d.document_metadata and d.document_metadata.get("budget_eur") is not None
    ]

    avg_score    = round(sum(scores) / len(scores), 1) if scores else None
    total_budget = sum(budgets) if budgets else None

    # Prochaine deadline : on trie par date et on prend la plus proche
    next_deadline_data = None
    upcoming = [d for d in docs if d.document_metadata and d.document_metadata.get("deadline")]
    if upcoming:
        upcoming.sort(key=lambda d: d.document_metadata["deadline"])
        nxt  = upcoming[0]
        meta = nxt.document_metadata
        try:
            deadline_dt = datetime.fromisoformat(meta["deadline"])
            days_left   = (deadline_dt.date() - datetime.now(timezone.utc).date()).days
            next_deadline_data = {
                "ref":            meta.get("ref", nxt.filename),
                "deadline":       meta["deadline"],
                "days_remaining": max(0, days_left),
            }
        except Exception:
            pass  # Date malformée → on ignore sans planter

    return DocumentStatsResponse(
        total=total,
        completed=completed,
        processing=processing,
        avg_score=avg_score,
        total_budget_eur=total_budget,
        next_deadline=next_deadline_data,
    )


@app.get(
    "/api/v1/me/documents/{doc_id}",
    response_model=DocumentResponse,
    tags=["Documents"],
    summary="Détail d'un document (tenant_id = JWT)"
)
async def get_my_document(
    doc_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),  # FEATURE 1 + 2
    db: Session        = Depends(get_db),
):
    """
    Récupère le détail d'un document spécifique.

    La sécurité est double :
    1. RLS (FEATURE 3) : PostgreSQL ne retourne que les docs du tenant du JWT
    2. Filtre applicatif : WHERE tenant_id = current_user.tenant_id
    → Un utilisateur ne peut PAS accéder au document d'un autre tenant
      même s'il connaît son UUID.
    """
    # Set tenant context on THIS session before any DB query
    from .database import set_tenant_context
    set_tenant_context(db, current_user.tenant_id)
    
    document = db.query(Document).filter(
        and_(
            Document.id == doc_id,
            Document.tenant_id == current_user.tenant_id,  # sécurité applicative
            ~Document.is_deleted,
        )
    ).first()

    if not document:
        # On répond 404 et non 403 : on ne révèle pas qu'un doc existe
        # mais appartient à un autre tenant (évite l'énumération d'IDs)
        raise HTTPException(status_code=404, detail="Document non trouvé")

    return document
              

@app.delete(
    "/api/v1/me/documents/{doc_id}",
    response_model=DocumentDeleteResponse,
    tags=["Documents"],
    summary="Supprimer un document (soft delete avec audit)"
)
async def delete_my_document(
    request: Request,
    doc_id: UUID = Path(...),
    delete_data: Optional[Dict[str, Any]] = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
     SUPPRESSION DE DOCUMENT (SOFT DELETE + AUDIT)
    
    SÉCURITÉ :
    - L'utilisateur peut supprimer uniquement SES documents
    - Les admins peuvent supprimer n'importe quel document de leur tenant
    
    AUDIT :
    - Tous les détails sont loggés dans audit_logs
    - Hash chain maintenu pour intégrité
    
    SOFT DELETE :
    - is_deleted = true
    - deleted_at = maintenant
    - deleted_by = current_user.id
    - deletion_reason (optionnel)
    """
    # Set tenant context on THIS session before any DB query
    from .database import set_tenant_context
    set_tenant_context(db, current_user.tenant_id)
    
    
    # ── 2. Récupérer le document ──────────────────────────────────────────
    document = db.query(Document).filter(
        and_(
            Document.id == doc_id,
            Document.tenant_id == current_user.tenant_id,
            ~Document.is_deleted,
        )
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document introuvable ou déjà supprimé"
        )
    
    # ── 3. Vérifier les permissions ───────────────────────────────────────
    # Vérifier que l'utilisateur est propriétaire OU admin
    is_owner = document.uploaded_by == current_user.id
    is_admin = current_user.role and current_user.role.name in ["admin", "tenant_admin"]
    
    if not (is_owner or is_admin):
        # Log l'échec dans audit_logs
        log_action(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action="document.deleted",
            resource_type="document",
            resource_id=document.id,
            status="failure",
            reason="Permission denied: not owner and not admin",
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        db.commit()
        
        raise HTTPException(
            status_code=403,
            detail="Vous n'avez pas la permission de supprimer ce document"
        )
    
    # ── 4. Capturer l'état avant suppression ──────────────────────────────
    old_state = {
        "title": document.filename,
        "filename": document.filename,
        "status": document.status,
        "storage_path": document.storage_path,
        "file_size": document.file_size,
        "created_at": document.created_at.isoformat() if document.created_at else None,
    }
    
    # ── 5. Soft delete ────────────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    
    # Extraire la raison si fournie
    reason = None
    if delete_data and isinstance(delete_data, dict):
        reason = delete_data.get("reason")
    
    document.is_deleted = True
    document.deleted_at = now
    document.deleted_by = current_user.id
    document.updated_at = now
    # Set purge_after to 30 days from now (for nightly purge job)
    document.purge_after = now + timedelta(days=30)
    
    # Si votre modèle a un champ deletion_reason
    if hasattr(document, 'deletion_reason'):
        document.deletion_reason = reason
    
    # ── 6. Audit log ──────────────────────────────────────────────────────
    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="document.deleted",
        resource_type="document",
        resource_id=document.id,
        old_value=old_state,
        new_value={
            "is_deleted": True,
            "deleted_at": now.isoformat(),
            "deleted_by": str(current_user.id),
            "reason": reason or "Aucune raison fournie",
        },
        status="success",
        reason=reason or "Document supprimé par l'utilisateur",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    
    # ── 7. Commit ─────────────────────────────────────────────────────────
    db.commit()
    db.refresh(document)
    
    logger.info(
        f"✅ Document {doc_id} supprimé par {current_user.email} "
        f"(tenant {current_user.tenant_id})"
    )
    
    # ── 8. Réponse ────────────────────────────────────────────────────────
    return {
        "id": document.id,
        "filename": document.filename,
        "deleted_at": document.deleted_at,
        "deleted_by": document.deleted_by,
        "reason": reason,
        "message": "Document supprimé avec succès",
    }


@app.post(
    "/api/v1/me/documents/upload",
    response_model=DocumentResponse,
    status_code=201,
    tags=["Documents"],
    summary="Upload un nouveau document (PDF ou Word)",
    dependencies=[Depends(RateLimitNormal)]
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    reference: Optional[str] = None,
    deadline: Optional[str] = None,
    budget_eur: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload un fichier PDF ou Word et crée automatiquement l'entrée en base.
    
    WORKFLOW :
    1. Valider le fichier (type, taille max 50MB)
    2. Upload vers MinIO (stockage S3-compatible)
    3. Créer l'entrée dans la table documents
    4. Lancer l'indexation/analyse en arrière-plan (TODO)
    
    RLS : Le document est automatiquement lié au tenant_id de l'utilisateur.
    """
    # Set tenant context on THIS session before any DB query
    from .database import set_tenant_context
    set_tenant_context(db, current_user.tenant_id)
    
    # ============================================================================
    # RATE LIMITING FOR DOCUMENT UPLOAD (DoS Protection)
    # ============================================================================
    # Rate limiting enforced via dependencies=[Depends(RateLimitNormal)]
    # 10 requests/min per (IP, user email) pair
    # Prevents DoS via storage exhaustion and CPU exhaustion from processing.
    ip_address = get_client_ip(request)
    
    ALLOWED_TYPES = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux (max 50MB). Taille: {file_size / 1024 / 1024:.2f}MB"
        )
    
    detected_type = magic.from_buffer(file_content[:2048], mime=True)
    if detected_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Type de fichier invalide. Seuls les fichiers PDF et Word sont acceptés."
        )
    
    # Retourner au début du fichier pour MinIO
    file_data = BytesIO(file_content)
    
    # ── Upload vers MinIO ─────────────────────────────────────────────────
    try:
        upload_result = minio_client.upload_file(
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.id),
        )
    except Exception as e:
        logger.error(f"Erreur upload MinIO: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'upload du fichier")
    
    # ── Créer l'entrée en base de données ────────────────────────────────
    now = datetime.now(timezone.utc)

    # Calculer le hash SHA256 du fichier (pour détection doublons et intégrité)
    file_hash = hashlib.sha256(file_content).hexdigest()

    # Métadonnées du document
    doc_metadata = {
        "uploaded_at": now.isoformat(),     # Timestamp d'upload
        "file_hash": file_hash,             # SHA256 du fichier
        "content_length": file_size,        # Taille exacte du contenu
        "mime_type": file.content_type,     # Type MIME
    }

    # Ajouter les métadonnées optionnelles fournies par le client
    if reference:
        doc_metadata["ref"] = reference
    if deadline:
        doc_metadata["deadline"] = deadline
    if budget_eur:
        doc_metadata["budget_eur"] = budget_eur

    
    new_doc = Document(
        id=_uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        filename=file.filename,
        storage_path=upload_result["storage_path"],
        file_size=upload_result["file_size"],
        mime_type=upload_result["mime_type"],
        file_hash=file_hash,                # ✅ Nouveau champ !
        status="uploaded",
        language="fr",
        document_metadata=doc_metadata,
        uploaded_by=current_user.id,
        created_by=current_user.id,
    )
    
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    # Log document upload
    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="document.created",
        resource_type="document",
        resource_id=new_doc.id,
        new_value={
            "filename": new_doc.filename,
            "file_size": new_doc.file_size,
            "mime_type": new_doc.mime_type,
            "status": new_doc.status,
        },
        status="success",
        reason=f"Document '{new_doc.filename}' uploaded",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    
    
    
    logger.info(f"✅ Document créé: {new_doc.id} pour user {current_user.email}")
    
    return new_doc


@app.get(
    "/api/v1/me/documents/{doc_id}/download",
    response_model=Dict[str, str],
    tags=["Documents"],
    summary="Obtenir une URL de téléchargement signé pour un document"
)
async def download_document(
    doc_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    GÉNÉRATION D'URL DE TÉLÉCHARGEMENT SIGNÉ
    
    SÉCURITÉ :
    - L'utilisateur peut télécharger uniquement SES documents
    - Admin peuvent télécharger n'importe quel document du tenant
    - URL signée expire après 1 heure
    
    RÉPONSE :
    - Retourne une URL MinIO présignée (temporaire + signée)
    - Le client utilise cette URL pour télécharger directement depuis MinIO
    - Pas d'authentification requise pour l'URL elle-même (signature = authentification)
    
    RLS : Vérifie que le document appartient au tenant de l'utilisateur
    """
    
    # ── 1. Récupérer le document ───────────────────────────────────────────
    document = db.query(Document).filter(
        and_(
            Document.id == doc_id,
            Document.tenant_id == current_user.tenant_id,
            ~Document.is_deleted,
        )
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # ── 2. Générer l'URL signée ───────────────────────────────────────────
    presigned_url = minio_client.get_presigned_url(
        object_name=document.storage_path,
        expires=timedelta(hours=1)
    )
    
    # ── 3. Log l'accès ────────────────────────────────────────────────────
    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="document.downloaded",
        resource_type="document",
        resource_id=document.id,
        status="success",
        reason=f"Presigned URL generated for '{document.filename}'",
    )
    db.commit()
    
    logger.info(
        f"✅ Download URL générée pour document {doc_id} "
        f"par {current_user.email} (tenant {current_user.tenant_id})"
    )
    
    return {"download_url": presigned_url}


# ==============================================================================
# 4. TENANTS — Gestion des organisations (admin système)
# ==============================================================================

@app.get("/api/v1/tenants", response_model=PaginatedResponse, tags=["Tenants"])
async def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),  # ← Admin système uniquement
    db: Session = Depends(get_db)
):
    """Liste tous les tenants (admin système uniquement)."""
    total  = db.query(Tenant).filter(Tenant.is_active).count()
    offset = (page - 1) * page_size
    items  = db.query(Tenant).filter(Tenant.is_active).offset(offset).limit(page_size).all()
    return PaginatedResponse(
        items=[TenantResponse.model_validate(t) for t in items],
        total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@app.post("/api/v1/tenants", response_model=TenantResponse, status_code=201, tags=["Tenants"])
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Créer une nouvelle organisation."""
    existing = db.query(Tenant).filter(Tenant.email == tenant_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    tenant = Tenant(
        name=tenant_data.name,
        email=tenant_data.email,
        subscription_plan=tenant_data.subscription_plan or "free",
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


# ==============================================================================
# 4.5. TENANT SETTINGS — Current tenant info & logo
# ==============================================================================

@app.get("/api/v1/me/tenant", response_model=TenantResponse, tags=["Tenant Settings"])
async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's tenant information.
    
    Le tenant_id vient du JWT, jamais de l'URL.
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    metadata = dict(tenant.tenant_metadata or {})
    if metadata.get("logo_path"):
        # Return API proxy URL instead of MinIO presigned URL (avoids CORS issues)
        metadata["logo_url"] = "/api/v1/me/tenant/logo/image"
    
    tenant_dict = TenantResponse.model_validate(tenant).model_dump()
    tenant_dict["tenant_metadata"] = metadata
    return tenant_dict


@app.patch("/api/v1/me/tenant", response_model=TenantResponse, tags=["Tenant Settings"])
async def update_current_tenant(
    tenant_data: TenantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current tenant settings.
    
    SECURITY: Only tenant admin/superadmin can update
    """
    # Check role: admin or superadmin
    if not current_user.role or current_user.role.name not in ("admin", "superadmin", "tenant_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update tenant settings"
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Only allow updating: name, email, tenant_metadata
    if tenant_data.name is not None:
        # Check for duplicate name (unique constraint)
        existing = db.query(Tenant).filter(
            and_(Tenant.name == tenant_data.name, Tenant.id != current_user.tenant_id)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Tenant name already in use")
        tenant.name = tenant_data.name
    
    if tenant_data.email is not None:
        # Check for duplicate email
        existing = db.query(Tenant).filter(
            and_(Tenant.email == tenant_data.email, Tenant.id != current_user.tenant_id)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        tenant.email = tenant_data.email
    
    if tenant_data.sector is not None:
        tenant.sector = tenant_data.sector
    
    if tenant_data.country is not None:
        tenant.country = tenant_data.country
    
    if tenant_data.tenant_metadata is not None:
        # Merge new metadata with existing (don't overwrite logo_url/logo_path)
        tenant.tenant_metadata = {
            **tenant.tenant_metadata,
            **tenant_data.tenant_metadata
        }
    
    db.commit()
    db.refresh(tenant)
    
    # Log action
    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="tenant.updated",
        resource_type="tenant",
        resource_id=tenant.id,
        new_value={
            "name": tenant.name,
            "email": tenant.email,
        },
        status="success",
        reason="Tenant settings updated"
    )
    
    return TenantResponse.model_validate(tenant)


@app.post("/api/v1/me/tenant/logo", tags=["Tenant Settings"])
async def upload_tenant_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload tenant logo.
    
    SECURITY: Only tenant admin/superadmin
    Request: multipart/form-data with field "file"
    Validation: PNG, JPEG, WebP, SVG only; max 2MB
    
    Response:
        {
            "logo_url": "https://minio.../logos/tenant-id/logo.png?signature=...",
            "message": "Logo mis à jour"
        }
    """
    # Check role
    if not current_user.role or current_user.role.name not in ("admin", "superadmin", "tenant_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can upload tenant logo"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        file_bytes = BytesIO(file_content)
        
        # Upload to MinIO via storage service
        upload_result = minio_client.upload_logo(
            file_data=file_bytes,
            filename=file.filename or "logo.png",
            content_type=file.content_type or "image/png",
            tenant_id=str(current_user.tenant_id)
        )
        
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant.tenant_metadata = {
            **tenant.tenant_metadata,
            "logo_path": upload_result["storage_path"]
        }
        db.commit()
        
        # Use API proxy URL instead of MinIO presigned URL (avoids CORS issues)
        logo_url = "/api/v1/me/tenant/logo/image"
        
        # Log action
        log_action(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action="tenant.logo_updated",
            resource_type="tenant",
            resource_id=tenant.id,
            new_value={
                "logo_path": upload_result["storage_path"],
                "file_size": upload_result["file_size"]
            },
            status="success",
            reason="Tenant logo uploaded"
        )
        
        return {
            "logo_url": logo_url,
            "message": "Logo mis à jour"
        }
        
    except ValueError as e:
        # Validation error from upload_logo
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error uploading logo: {e}")
        raise HTTPException(status_code=500, detail="Error uploading logo")


@app.get("/api/v1/me/tenant/logo/image", tags=["Tenant Settings"])
async def get_tenant_logo_image(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Serve tenant logo image directly through API (avoids CORS issues with MinIO).
    Returns the image binary with proper Content-Type header.
    """
    try:
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        logo_path = tenant.tenant_metadata.get("logo_path") if tenant.tenant_metadata else None
        if not logo_path:
            raise HTTPException(status_code=404, detail="No logo uploaded")
        
        try:
            response = minio_client.client.get_object(
                bucket_name=minio_client.bucket_name,
                object_name=logo_path
            )
            
            # Read image data
            image_data = response.read()
            response.close()
            
            # Determine content type from file extension
            if logo_path.endswith('.png'):
                content_type = "image/png"
            elif logo_path.endswith('.webp'):
                content_type = "image/webp"
            elif logo_path.endswith('.svg'):
                content_type = "image/svg+xml"
            else:
                content_type = "image/jpeg"
            
            return StreamingResponse(
                BytesIO(image_data),
                media_type=content_type,
                headers={
                    "Content-Disposition": f"inline; filename={logo_path.split('/')[-1]}",
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        except Exception as e:
            logger.error(f"❌ Error retrieving logo from MinIO: {e}")
            raise HTTPException(status_code=500, detail="Error retrieving logo")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error serving logo: {e}")
        raise HTTPException(status_code=500, detail="Error serving logo")


# ==============================================================================
# 5. ROLES — Réservé aux admins
# ==============================================================================


@app.get("/api/v1/{tenant_id}/roles", response_model=PaginatedResponse, tags=["Roles"])
async def list_roles(
    tenant_id: UUID = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Liste les rôles du tenant."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    total  = db.query(Role).filter(Role.tenant_id == tenant_id).count()
    offset = (page - 1) * page_size
    items  = db.query(Role).filter(Role.tenant_id == tenant_id).offset(offset).limit(page_size).all()
    return PaginatedResponse(
        items=[RoleResponse.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@app.post("/api/v1/{tenant_id}/roles", response_model=RoleResponse, status_code=201, tags=["Roles"], dependencies=[Depends(RateLimitNormal)])
async def create_role(
    request: Request,
    tenant_id: UUID = Path(...),
    role_data: RoleCreate = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Créer un nouveau rôle."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    # ⏱️ RATE LIMITING: Rate limiting enforced via dependencies=[Depends(RateLimitNormal)]
    # 10 requests/minute/IP to prevent brute force role creation
    ip_address = get_client_ip(request)
    
    existing = db.query(Role).filter(
        and_(Role.tenant_id == tenant_id, Role.name == role_data.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Rôle déjà existant")
    
   
    permissions = role_data.permissions or []
    has_admin_perms = "admin:all" in permissions or "*" in permissions
    if has_admin_perms:
        if not is_super_admin(current_user, db):
            raise HTTPException(
                status_code=403,
                detail="Seul le superadmin peut créer un rôle avec permissions admin"
            )
    
   
    if role_data.is_system and not is_super_admin(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="Seul le superadmin peut créer un rôle système"
        )
    
    role = Role(
        tenant_id=tenant_id, name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions or {},
        is_system=role_data.is_system if role_data.is_system else False,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    # Log role creation
    log_action(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="role.created",
        resource_type="role",
        resource_id=role.id,
        new_value={
            "name": role.name,
            "description": role.description,
            "permissions": role.permissions,
        },
        status="success",
        reason=f"Role '{role.name}' created",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.commit()
    
    return role


# ==============================================================================
# 6. USERS — Réservé aux admins
# ==============================================================================

@app.get("/api/v1/{tenant_id}/users", response_model=PaginatedResponse, tags=["Users"])
async def list_users(
    tenant_id: UUID = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    role: Optional[str] = Query(None, description="Filtrer par nom de rôle (ex: 'admin', 'analyst', 'viewer')"),
    search: Optional[str] = Query(None, description="Rechercher par email ou full_name"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Liste les utilisateurs du tenant (admin uniquement).
    
     FILTRAGE :
    - role : Filtrer par nom de rôle (ex: 'admin', 'analyst', 'viewer')
    - search : Rechercher par email ou full_name
    
     TRI :
    - Par hiérarchie de rôle (superadmin → admin → manager → analyst → contributor → viewer)
    - Puis par full_name alphabétiquement
    """
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
  
    
    # Importer les fonctions SQLAlchemy nécessaires
    from sqlalchemy import case, asc, or_
    
    # Définir l'ordre de hiérarchie des rôles
    role_hierarchy = case(
        (Role.name == "superadmin", 1),
        (Role.name == "admin", 2),
        (Role.name == "manager", 3),
        (Role.name == "analyst", 4),
        (Role.name == "contributor", 5),
        (Role.name == "viewer", 6),
        else_=7,  # Rôles non-reconnus en dernier
    )
    
    # Requête avec jointure et filtres
    filters = [
        User.tenant_id == tenant_id,
        User.is_deleted == False  # noqa: E712
    ]
    
    # Filtrer par rôle si spécifié
    if role:
        filters.append(Role.name == role)
    
    # Filtrer par recherche (email ou full_name) si spécifié
    if search:
        search_term = f"%{search.lower()}%"
        filters.append(
            or_(
                User.email.ilike(search_term),
                User.full_name.ilike(search_term)
            )
        )
    
    q = db.query(User).outerjoin(Role).filter(
        and_(*filters)
    ).order_by(
        asc(role_hierarchy),  # Hiérarchie (1-7)
        asc(User.full_name)   # Puis par nom
    )
    
    total  = q.count()
    offset = (page - 1) * page_size
    items  = q.offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        items=[UserDetailResponse.model_validate(u) for u in items],
        total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@app.post("/api/v1/{tenant_id}/users", response_model=UserResponse, status_code=201, tags=["Users"], dependencies=[Depends(RateLimitNormal)])
async def create_user_admin(
    request: Request,
    tenant_id: UUID = Path(...),
    user_data: UserCreate = Body(...),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Créer un utilisateur (admin uniquement).
    
    Le rôle peut être spécifié soit par:
    - role_id: UUID directement
    - role: string (nom du rôle: 'analyst', 'admin', 'viewer')
    """
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
   
    ip_address = get_client_ip(request)
    
    existing = db.query(User).filter(
        and_(User.tenant_id == tenant_id, User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    # Résoudre le rôle : par UUID ou par nom
    role_id = user_data.role_id
    if user_data.role and not role_id:
        # Chercher le rôle par nom dans le tenant
        role_obj = db.query(Role).filter(
            and_(Role.tenant_id == tenant_id, Role.name == user_data.role)
        ).first()
        if role_obj:
            role_id = role_obj.id

    if role_id:
        assigned_role = db.query(Role).filter(Role.id == role_id).first()
        if assigned_role:
            role_perms = assigned_role.permissions or []
            is_admin_role = (
                (assigned_role.is_system and assigned_role.name in ["admin", "superadmin", "system_admin", "tenant_admin"]) or
                ("admin:all" in role_perms or "*" in role_perms)
            )
            if is_admin_role and not is_super_admin(current_user, db):
                raise HTTPException(
                    status_code=403,
                    detail="Seul le superadmin peut assigner un rôle admin"
                )
    
    user = User(
        tenant_id=tenant_id, email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name, role_id=role_id, is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Log user creation
    log_action(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="user.created",
        resource_type="user",
        resource_id=user.id,
        new_value={
            "email": user.email,
            "full_name": user.full_name,
            "role_id": str(user.role_id) if user.role_id else None,
            "is_active": user.is_active,
        },
        status="success",
        reason=f"User '{user.email}' created by admin",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent") if request else None,
    )
    
    
    if user.role_id:
        assigned_role = db.query(Role).filter(Role.id == user.role_id).first()
        if assigned_role:
            role_perms = assigned_role.permissions or []
            is_admin_role = (
                (assigned_role.is_system and assigned_role.name in ["admin", "superadmin", "system_admin", "tenant_admin"]) or
                ("admin:all" in role_perms or "*" in role_perms)
            )
            if is_admin_role:
                log_action(
                    db=db,
                    tenant_id=tenant_id,
                    user_id=current_user.id,
                    action="role.assigned",
                    resource_type="user",
                    resource_id=user.id,
                    new_value={"role": assigned_role.name},
                    status="success",
                    reason=f"Admin role '{assigned_role.name}' assigned to user '{user.email}'",
                    ip_address=get_client_ip(request),
                    user_agent=request.headers.get("user-agent") if request else None,
                )
    
    db.commit()
    
    return user


@app.get("/api/v1/{tenant_id}/users/{user_id}", response_model=UserDetailResponse, tags=["Users"])
async def get_user(
    tenant_id: UUID = Path(...),
    user_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère un utilisateur spécifique."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    user = db.query(User).filter(and_(User.id == user_id, User.tenant_id == tenant_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user


@app.patch("/api/v1/{tenant_id}/users/{user_id}", response_model=UserResponse, tags=["Users"], dependencies=[Depends(RateLimitNormal)])
async def update_user(
    request: Request,
    tenant_id: UUID = Path(...),
    user_id: UUID = Path(...),
    user_data: UserUpdate = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Modifier un utilisateur (admin uniquement).
    """
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
   
    ip_address = get_client_ip(request)
    
    if user_data.is_active is not None and not is_super_admin(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="Seul le superadmin peut activer/désactiver les utilisateurs"
        )
    
    # Empêcher l'auto-désactivation (un utilisateur ne peut pas désactiver son propre compte)
    if user_data.is_active is not None and not user_data.is_active and user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Vous ne pouvez pas désactiver votre propre compte"
        )
 
    user = db.query(User).filter(and_(User.id == user_id, User.tenant_id == tenant_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Empêcher la désactivation du dernier superadmin actif
    if user_data.is_active is not None and not user_data.is_active:
        # Vérifier si cet utilisateur est un superadmin
        user_role = db.query(Role).filter(Role.id == user.role_id).first() if user.role_id else None
        
        if user_role and user_role.name == "superadmin":
            # Compter les superadmins ACTIFS du tenant
            active_superadmin_count = db.query(User).filter(
                and_(
                    User.tenant_id == tenant_id,
                    User.is_active,
                    not User.is_deleted,
                    Role.name == "superadmin"
                )
            ).join(Role).count()
            
            # Si c'est le dernier superadmin actif, refuser la désactivation
            if active_superadmin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Impossible de désactiver le dernier superadmin actif du tenant"
                )
    
    
    if user_data.role_id and user_data.role_id != user.role_id:
        new_role = db.query(Role).filter(Role.id == user_data.role_id).first()
        if new_role:
            role_perms = new_role.permissions or []
            is_admin_role = (
                (new_role.is_system and new_role.name in ["admin", "superadmin", "system_admin", "tenant_admin"]) or
                ("admin:all" in role_perms or "*" in role_perms)
            )
            if is_admin_role and not is_super_admin(current_user, db):
                raise HTTPException(
                    status_code=403,
                    detail="Seul le superadmin peut assigner un rôle admin"
                )
    
    old_value = {
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "role_id": str(user.role_id) if user.role_id else None,
    }
    
    if user_data.email:
        user.email = user_data.email
    if user_data.full_name:
        user.full_name = user_data.full_name
    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password)
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.role_id:
        user.role_id = user_data.role_id
    
    if user_data.is_active is False:
        db.query(AuthSession).filter(
            and_(
                AuthSession.user_id == user.id,
                AuthSession.revoked_at == None  # noqa: E711
            )
        ).update({"revoked_at": datetime.now(timezone.utc)})
    
    new_value = {
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "role_id": str(user.role_id) if user.role_id else None,
    }
    
    log_action(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="user.updated",
        resource_type="user",
        resource_id=user.id,
        old_value=old_value,
        new_value=new_value,
        status="success",
        reason=f"User '{user.email}' updated by admin",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent") if request else None,
    )
    
    if user_data.role_id and user_data.role_id != old_value.get("role_id"):
        new_role = db.query(Role).filter(Role.id == user.role_id).first()
        if new_role:
            role_perms = new_role.permissions or []
            is_admin_role = (
                (new_role.is_system and new_role.name in ["admin", "superadmin", "system_admin", "tenant_admin"]) or
                ("admin:all" in role_perms or "*" in role_perms)
            )
            if is_admin_role:
                log_action(
                    db=db,
                    tenant_id=tenant_id,
                    user_id=current_user.id,
                    action="role.assigned",
                    resource_type="user",
                    resource_id=user.id,
                    new_value={"role": new_role.name},
                    status="success",
                    reason=f"Admin role '{new_role.name}' assigned to user '{user.email}'",
                    ip_address=get_client_ip(request),
                    user_agent=request.headers.get("user-agent") if request else None,
                )
    
    db.commit()
    db.refresh(user)
    
    return user


@app.delete("/api/v1/{tenant_id}/users/{user_id}", status_code=204, tags=["Users"], dependencies=[Depends(RateLimitStrict)])
async def delete_user(
    request: Request,
    tenant_id: UUID = Path(...),
    user_id: UUID = Path(...),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Supprimer un utilisateur (soft delete — admin uniquement).
    
    SÉCURITÉ: 
    - Soft delete (is_deleted=True) pour conserver l'historique audit
    - Seul le superadmin peut supprimer des utilisateurs
    - Impossible de supprimer le seul superadmin du tenant
    """
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    
    ip_address = get_client_ip(request)
    
    if not is_super_admin(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="Seul le superadmin peut supprimer des utilisateurs"
        )
    
    
    user = db.query(User).filter(and_(User.id == user_id, User.tenant_id == tenant_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Empêcher la suppression du seul superadmin du tenant
    superadmin_count = db.query(User).filter(
        and_(
            User.tenant_id == tenant_id,
            User.is_deleted == False,  # noqa: E712
            Role.name == "superadmin"
        )
    ).join(Role).count()
    
    user_role = db.query(Role).filter(Role.id == user.role_id).first() if user.role_id else None
    if user_role and user_role.name == "superadmin" and superadmin_count <= 1:
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer le seul superadmin du tenant"
        )
    
    # Capture state before deletion
    old_state = {
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "role_id": str(user.role_id) if user.role_id else None,
    }
    
    # Soft delete
    now = datetime.now(timezone.utc)
    user.is_deleted = True
    user.updated_at = now
    
    
    db.query(AuthSession).filter(
        and_(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at == None  # noqa: E711
        )
    ).update({"revoked_at": datetime.now(timezone.utc)})
    
    db.commit()
    
    # Log user deletion
    log_action(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="user.deleted",
        resource_type="user",
        resource_id=user.id,
        old_value=old_state,
        new_value={
            "is_deleted": True,
            "deleted_at": now.isoformat(),
            "deleted_by": str(current_user.id),
        },
        status="success",
        reason=f"User '{user.email}' deleted by superadmin",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.commit()
    
    # Return 204 No Content
    return None


# ==============================================================================
# 7. AUDIT — Journal immuable (admin uniquement)
# ==============================================================================

@app.get("/api/v1/{tenant_id}/audit", response_model=PaginatedResponse, tags=["Audit"])
async def list_audit_logs(
    tenant_id: UUID = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resource_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    since: Optional[str] = Query(None, description="ISO 8601 timestamp — filtre timestamp >= since"),
    until: Optional[str] = Query(None, description="ISO 8601 timestamp — filtre timestamp <= until"),
    search: Optional[str] = Query(None, description="Recherche textuelle sur user_email + ip_address (ILIKE)"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    from datetime import datetime as dt
    
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
   
    from sqlalchemy.orm import aliased
    UserAlias = aliased(User)
    
    q = db.query(
        AuditLog,
        UserAlias.email.label("user_email"),
        UserAlias.full_name.label("user_name")
    ).outerjoin(
        UserAlias,
        and_(
            AuditLog.user_id == UserAlias.id,
            AuditLog.tenant_id == UserAlias.tenant_id  # Scoped au tenant
        )
    ).filter(AuditLog.tenant_id == tenant_id)
    
    # Appliquer les filtres (AVANT la pagination)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    
    if action:
        q = q.filter(AuditLog.action == action)
    
    # Filtres de date (ISO 8601)
    if since:
        try:
            since_dt = dt.fromisoformat(since)
            q = q.filter(AuditLog.timestamp >= since_dt)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Paramètre 'since' invalide. Utilisez ISO 8601.")
    
    if until:
        try:
            until_dt = dt.fromisoformat(until)
            q = q.filter(AuditLog.timestamp <= until_dt)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Paramètre 'until' invalide. Utilisez ISO 8601.")
    
    # Recherche textuelle (ILIKE sur email + IP)
    if search:
        search_pattern = f"%{search}%"
        q = q.filter(
            or_(
                UserAlias.email.ilike(search_pattern),
                AuditLog.ip_address.ilike(search_pattern)
            )
        )
    
    # Calculer le total APRÈS les filtres
    total = q.count()
    
    # Pagination
    offset = (page - 1) * page_size
    results = q.order_by(desc(AuditLog.timestamp)).offset(offset).limit(page_size).all()
    
    # Construire les réponses — mapper les colonnes jointes
    items = []
    for result in results:
        if isinstance(result, tuple):
            log, user_email, user_name = result
        else:
            log = result
            user_email = None
            user_name = None
        
        log_dict = AuditLogResponse.model_validate(log).model_dump()
        log_dict["user_email"] = user_email
        log_dict["user_name"] = user_name
        items.append(AuditLogResponse(**log_dict))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


# ==============================================================================
# 8. DASHBOARD — Vue agrégée pour le frontend
# ==============================================================================

@app.get("/api/v1/me/dashboard/admin", response_model=AdminDashboardResponse, tags=["Dashboard"])
async def get_admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dashboard pour les administrateurs tenant (tenant_admin role).
    
    Retourne des stats agrégées tenant-wide :
    - KPIs: documents actifs, score conformité moyen, win rate
    - Documents récents
    - Distribution des statuts
    - Activité équipe
    - Notifications
    
    Redis Cache: "dashboard:admin:{tenant_id}" TTL=60s
    """
    from sqlalchemy import func
    
    
    user_permissions = current_user.role.permissions or [] if current_user.role else []
    is_admin = (
        (current_user.role and current_user.role.name in ["admin", "superadmin", "system_admin", "tenant_admin"]) or
        ("admin:all" in user_permissions or "*" in user_permissions )
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Rôle tenant_admin requis")
    
    tenant_id = current_user.tenant_id
    
   
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
   
    active_docs = db.query(func.count(Document.id)).filter(
        and_(Document.tenant_id == tenant_id, Document.status == "processing", ~Document.is_deleted)
    ).scalar() or 0
    
    total_docs = db.query(func.count(Document.id)).filter(
        and_(Document.tenant_id == tenant_id, ~Document.is_deleted)
    ).scalar() or 0
    
    avg_score = db.query(func.avg(ComplianceReport.compliance_score)).filter(
        ComplianceReport.tenant_id == tenant_id
    ).scalar() or 0.0
    
    completed_count = db.query(func.count(Document.id)).filter(
        and_(Document.tenant_id == tenant_id, Document.status == "completed", ~Document.is_deleted)
    ).scalar() or 0
    
    win_rate = (completed_count / total_docs * 100) if total_docs > 0 else 0.0
    
  
    recent_docs = db.query(Document).filter(
        and_(Document.tenant_id == tenant_id, ~Document.is_deleted)
    ).order_by(desc(Document.created_at)).limit(5).all()
    
   
    status_counts = {
        "pending": db.query(func.count(Document.id)).filter(
            and_(Document.tenant_id == tenant_id, Document.status == "pending", ~Document.is_deleted)
        ).scalar() or 0,
        "processing": active_docs,
        "completed": completed_count,
        "failed": db.query(func.count(Document.id)).filter(
            and_(Document.tenant_id == tenant_id, Document.status == "failed", ~Document.is_deleted)
        ).scalar() or 0,
    }
    
    
    BUSINESS_ACTIONS = [
        'document.created', 'document.updated', 'document.deleted',
        'document.downloaded', 'user.created', 'user.updated', 'role.assigned'
    ]
    
    team_activity = db.query(
        AuditLog.user_id,
        User.full_name,
        AuditLog.action,
        AuditLog.resource_type,
        AuditLog.resource_id,
        AuditLog.timestamp
    ).join(User, AuditLog.user_id == User.id, isouter=True).filter(
        AuditLog.tenant_id == tenant_id,
        AuditLog.action.in_(BUSINESS_ACTIONS),
        AuditLog.user_id != current_user.id
    ).order_by(desc(AuditLog.timestamp)).limit(5).all()
    
    from .schemas import TeamActivityItem, StatusDistribution, KPIData
    team_activity_list = [
        TeamActivityItem(
            user_id=item[0] or _uuid.uuid4(),
            full_name=item[1] or "System",
            action=item[2],
            resource_type=item[3],
            resource_id=item[4],
            timestamp=item[5]
        )
        for item in team_activity
    ]
    
   
    notifications = db.query(Notification).filter(
        and_(
            Notification.tenant_id == tenant_id,
            or_(
                Notification.user_id == current_user.id,
                Notification.user_id == None  # noqa: E711
            )
        )
    ).order_by(desc(Notification.created_at)).limit(5).all()
    
    return AdminDashboardResponse(
        tenant=TenantResponse.model_validate(tenant),
        user=UserResponse.model_validate(current_user),
        kpis=KPIData(
            active_documents=active_docs,
            total_documents=total_docs,
            avg_compliance_score=float(avg_score),
            win_rate=win_rate
        ),
        recent_documents=[DocumentResponse.model_validate(d) for d in recent_docs],
        status_distribution=StatusDistribution(**status_counts),
        team_activity=team_activity_list,
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
    )


@app.get("/api/v1/me/dashboard/user", response_model=UserDashboardResponse, tags=["Dashboard"])
async def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dashboard pour les utilisateurs réguliers (analyst, viewer, etc).
    
    Retourne des stats personnelles :
    - KPIs: mes documents, mes complétés, mon score moyen
    - Mes documents récents
    - Prochaines échéances
    - Dernière analyse
    - Notifications
    
    Redis Cache: "dashboard:user:{user_id}" TTL=30s
    """
    from sqlalchemy import func
    
    tenant_id = current_user.tenant_id
    user_id = current_user.id
    
  
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
   
    my_total = db.query(func.count(Document.id)).filter(
        and_(Document.tenant_id == tenant_id, Document.uploaded_by == user_id, ~Document.is_deleted)
    ).scalar() or 0
    
    my_completed = db.query(func.count(Document.id)).filter(
        and_(Document.tenant_id == tenant_id, Document.uploaded_by == user_id, 
             Document.status == "completed", ~Document.is_deleted)
    ).scalar() or 0
    
    my_avg_score = db.query(func.avg(ComplianceReport.compliance_score)).filter(
        and_(ComplianceReport.tenant_id == tenant_id,
             ComplianceReport.document_id.in_(
                 db.query(Document.id).filter(
                     and_(Document.tenant_id == tenant_id, Document.uploaded_by == user_id, 
                          ~Document.is_deleted)
                 )
             ))
    ).scalar() or 0.0
    
    
    my_docs = db.query(Document).filter(
        and_(Document.tenant_id == tenant_id, Document.uploaded_by == user_id, ~Document.is_deleted)
    ).order_by(desc(Document.created_at)).limit(10).all()
    
    
    upcoming = db.query(Document).filter(
        and_(Document.tenant_id == tenant_id, Document.uploaded_by == user_id,
             Document.status == "processing", ~Document.is_deleted)
    ).order_by(Document.created_at).limit(3).all()
 
    last_report = db.query(ComplianceReport).join(
        Document, ComplianceReport.document_id == Document.id
    ).filter(
        and_(ComplianceReport.tenant_id == tenant_id,
             Document.uploaded_by == user_id)
    ).order_by(desc(ComplianceReport.created_at)).first()
    
    from .schemas import LastAnalysisItem, KPIData
    last_analysis = None
    if last_report:
        last_doc = db.query(Document).filter(Document.id == last_report.document_id).first()
        if last_doc:
            last_analysis = LastAnalysisItem(
                document=DocumentResponse.model_validate(last_doc),
                report=ComplianceReportResponse.model_validate(last_report)
            )
    
    
    notifications = db.query(Notification).filter(
        and_(
            Notification.tenant_id == tenant_id,
            or_(
                Notification.user_id == user_id,
                Notification.user_id == None  # noqa: E711 (broadcasts)
            )
        )
    ).order_by(desc(Notification.created_at)).limit(5).all()
    
    return UserDashboardResponse(
        tenant=TenantResponse.model_validate(tenant),
        user=UserResponse.model_validate(current_user),
        kpis=KPIData(
            my_documents=my_total,
            my_completed=my_completed,
            my_avg_score=float(my_avg_score)
        ),
        my_documents=[DocumentResponse.model_validate(d) for d in my_docs],
        upcoming_deadlines=[DocumentResponse.model_validate(d) for d in upcoming],
        last_analysis=last_analysis,
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
    )


# ==============================================================================
# 8.1 NOTIFICATIONS — Gestion des notifications
# ==============================================================================

@app.get("/api/v1/me/notifications", response_model=PaginatedResponse, tags=["Notifications"])
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Liste les notifications de l'utilisateur (personnelles + broadcasts).
    
    Filtrage automatique :
    - Notifications personnelles (user_id = current_user.id)
    - Notifications broadcast (user_id IS NULL)
    - RLS filtre par tenant_id automatiquement
    """
    tenant_id = current_user.tenant_id
    
    q = db.query(Notification).filter(
        and_(
            Notification.tenant_id == tenant_id,
            or_(
                Notification.user_id == current_user.id,
                Notification.user_id == None  # noqa: E711
            )
        )
    )
    
    total = q.count()
    offset = (page - 1) * page_size
    items = q.order_by(desc(Notification.created_at)).offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@app.patch("/api/v1/me/notifications/{notification_id}/read", response_model=NotificationResponse, tags=["Notifications"])
async def mark_notification_read(
    notification_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marque une notification comme lue.
    
    SECURITY: User can only mark their own notifications as read
    (or broadcasts they have access to)
    """
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    
   
    if notif.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    if notif.user_id and notif.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    
    return NotificationResponse.model_validate(notif)


@app.patch("/api/v1/me/notifications/read-all", response_model=Dict[str, Any], tags=["Notifications"])
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marque TOUTES les notifications de l'utilisateur comme lues.
    
    Inclut les notifications personnelles ET les broadcasts.
    """
    db.query(Notification).filter(
        and_(
            Notification.tenant_id == current_user.tenant_id,
            Notification.is_read == False,  # noqa: E712
            or_(
                Notification.user_id == current_user.id,
                Notification.user_id == None  # noqa: E711
            )
        )
    ).update({"is_read": True})
    
    db.commit()
    
    return {"message": "Toutes les notifications sont marquées comme lues"}


# ==============================================================================
# 9. SESSIONS — Gestion des sessions actives (multi-device)
# ==============================================================================

@app.get("/api/v1/auth/sessions", response_model=List[AuthSessionResponse], tags=["Auth"])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Liste toutes les sessions actives de l'utilisateur (tous ses appareils)."""
    try:
        payload = verify_token(token)
        current_jti = payload.get("jti")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
    
    sessions = db.query(AuthSession).filter(
        and_(
            AuthSession.user_id == current_user.id,
            AuthSession.revoked_at == None,  # noqa: E711
            AuthSession.expires_at > datetime.now(timezone.utc),
        )
    ).order_by(desc(AuthSession.created_at)).all()
    
    for session in sessions:
        session.ensure_timezone_aware()
    
    response_sessions = []
    for session in sessions:
        session_response = AuthSessionResponse.model_validate(session)
        session_response.is_current = (session.jti == current_jti)
        response_sessions.append(session_response)
    
    return response_sessions


@app.delete("/api/v1/auth/sessions/{session_id}", response_model=SessionRevokeResponse, tags=["Auth"])
async def revoke_session(
    request: Request,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    Revoke a specific session (logout from a specific device).
    Cannot revoke the current session — use /auth/logout for that.
    """
    try:
        payload = verify_token(token)
        current_jti = payload.get("jti")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

    session = db.query(AuthSession).filter(
        and_(AuthSession.id == session_id, AuthSession.user_id == current_user.id)
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée")

    if session.revoked_at is not None:
        raise HTTPException(status_code=400, detail="Session déjà révoquée")

    if current_jti and session.jti == UUID(current_jti):
        raise HTTPException(
            status_code=400,
            detail="Utilisez /auth/logout pour déconnecter la session courante"
        )

    session.revoked_at = datetime.now(timezone.utc)
    db.commit()

    log_action(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="session.revoked",
        resource_type="auth",
        resource_id=session.id,
        status="success",
        reason="User revoked session from another device",
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return SessionRevokeResponse(
        message="Session révoquée avec succès",
        session_id=str(session.id),
        revoked_at=session.revoked_at
    )


# ==============================================================================
# GESTIONNAIRE D'ERREURS
# ==============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Formate toutes les erreurs HTTP en JSON standardisé (ErrorResponse).
    Ainsi le frontend peut toujours lire error.detail pour afficher un message.
    
    Gère les cas spéciaux :
    - Rate limit (429) : ajoute le header Retry-After
    - Detail dict : convertit en string pour la validation
    """
    # Convertir detail en string si ce n'est pas déjà une chaîne
    if isinstance(exc.detail, str):
        detail_str = exc.detail
        retry_after = None
    elif isinstance(exc.detail, dict):
        retry_after = exc.detail.get("retry_after_seconds")
        detail_str = exc.detail.get("message", str(exc.detail))
    else:
        detail_str = str(exc.detail)
        retry_after = None
    
    response = JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=detail_str or "Une erreur s'est produite",
            error_code="http_error",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ).model_dump(mode='json'),
    )
    
    # Ajouter le header Retry-After pour les erreurs 429 (Too Many Requests)
    if exc.status_code == 429 and retry_after:
        response.headers["Retry-After"] = str(retry_after)
    
    return response