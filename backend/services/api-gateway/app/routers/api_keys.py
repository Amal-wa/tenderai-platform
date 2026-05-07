# ==============================================================================
# ROUTERS: API KEYS — Endpoints pour gestion des clés API
# ==============================================================================


from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..auth import get_current_user
from ..models import User, APIKey
from ..security.api_keys import generate_api_key, validate_scopes, API_KEY_SCOPES
from ..audit_service import log_action
from ..core.ratelimit import get_client_ip

import logging
logger = logging.getLogger(__name__)

# ==============================================================================
#  PYDANTIC SCHEMAS
# ==============================================================================

class APIKeyCreateRequest(BaseModel):
    """Requête de création de clé API"""
    name: str = Field(..., min_length=1, max_length=255, description="Nom ami (ex: 'Mon script Python')")
    permissions: List[str] = Field(default=[], description="Scopes parmi API_KEY_SCOPES")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Expiration en jours (optionnel)")

class APIKeyResponse(BaseModel):
    """Réponse pour une clé (sans la clé complète)"""
    id: str
    name: str
    prefix: str
    permissions: List[str]
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime
    revoked_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class APIKeyCreateResponse(BaseModel):
    """Réponse de création (inclut la clé complète UNE SEULE FOIS)"""
    key: str = Field(..., description="Clé API complète (affichée UNE SEULE FOIS)")
    prefix: str
    id: str
    message: str = "Copiez cette clé maintenant — elle ne sera plus affichée."


class APIKeyRevokeResponse(BaseModel):
    """Réponse pour DELETE /api/v1/api-keys/{key_id}"""
    message: str = Field(..., description="Clé API révoquée avec succès")
    key_id: str = Field(..., description="ID de la clé révoquée")
    revoked_at: datetime = Field(..., description="Timestamp de révocation")

# ==============================================================================
# 🔌 ROUTER
# ==============================================================================

router = APIRouter(
    prefix="/api/v1/api-keys",
    tags=["API Keys"],
)

# ==============================================================================
# POST /api/v1/api-keys — Créer une clé API
# ==============================================================================

@router.post(
    "",
    response_model=APIKeyCreateResponse,
    summary="Créer une nouvelle clé API",
    description="Génère une nouvelle clé API. La clé est affichée UNE SEULE FOIS.",
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    request_body: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    http_request: Request = None,
):
    """
    Crée une nouvelle clé API.
    
    SÉCURITÉ :
    - La clé complète est générée et retournée UNE SEULE FOIS
    - On stocke en DB uniquement le hash Argon2id + prefix
    - Client DOIT copier et stocker la clé de manière sécurisée
    
     VALIDATION :
    - name: 1-255 caractères
    - permissions: valides parmi API_KEY_SCOPES
    - expires_in_days: 1-365 jours (optionnel)
    
    RETURNS:
        APIKeyCreateResponse avec la clé complète
    """
    # ── VALIDATION ──────────────────────────────────────────────────────────
    
    # Vérifier les scopes fournis
    if request_body.permissions:
        if not validate_scopes(request_body.permissions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scopes. Valid scopes: {API_KEY_SCOPES}",
            )
    
    # ── GÉNÉRATION ──────────────────────────────────────────────────────────
    
    # Générer la clé + hasher
    full_key, prefix, key_hash = generate_api_key()
    
    # Calculer expires_at si expiration demandée
    expires_at = None
    if request_body.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=request_body.expires_in_days)
    
    # ── CRÉATION EN DB ──────────────────────────────────────────────────────
    
    api_key = APIKey(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        name=request_body.name,
        key_prefix=prefix,
        key_hash=key_hash,
        permissions=request_body.permissions or [],
        expires_at=expires_at,
    )
    
    try:
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )
    
    # ── AUDIT ───────────────────────────────────────────────────────────────
    
    try:
        log_action(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action="apikey.created",
            resource_type="api_key",
            resource_id=str(api_key.id),
            new_value={"name": request_body.name, "prefix": prefix, "permissions": request_body.permissions or []},
            status="success",
            ip_address=get_client_ip(http_request) if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None,
        )
    except Exception as e:
        logger.warning(f"⚠️  Failed to log audit: {e}")
    
    # ── RÉPONSE AVEC CLÉ COMPLÈTE ───────────────────────────────────────────
    
    logger.info(f"✅ API key created: {prefix} (user={current_user.id})")
    
    return APIKeyCreateResponse(
        key=full_key,
        prefix=prefix,
        id=str(api_key.id),
        message="Copiez cette clé maintenant — elle ne sera plus affichée.",
    )

# ==============================================================================
# GET /api/v1/api-keys — Lister ses clés API
# ==============================================================================

@router.get(
    "",
    response_model=List[APIKeyResponse],
    summary="Lister ses clés API",
    description="Retourne la liste des clés API de l'utilisateur (sans les clés complètes)",
)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Liste les clés API de l'utilisateur actuel.
    
     SÉCURITÉ :
    - Affiche UNIQUEMENT les clés de l'utilisateur actuel
    - Affiche le prefix + metadata, JAMAIS la clé complète
    
    RETURNS:
        List[APIKeyResponse]
    """
    # ── REQUÊTE ─────────────────────────────────────────────────────────────
    
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.tenant_id == current_user.tenant_id,
    ).all()
    
    # ── FORMAT DE RÉPONSE ───────────────────────────────────────────────────
    
    return [
        APIKeyResponse(
            id=str(key.id),
            name=key.name,
            prefix=key.key_prefix,
            permissions=key.permissions or [],
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            created_at=key.created_at,
            revoked_at=key.revoked_at,
        )
        for key in api_keys
    ]

# ==============================================================================
# DELETE /api/v1/api-keys/{key_id} — Révoquer une clé
# ==============================================================================

@router.delete(
    "/{key_id}",
    response_model=APIKeyRevokeResponse,
    summary="Révoquer une clé API",
    description="Marque une clé comme révoquée (revoked_at = maintenant)",
)
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    http_request: Request = None,
):
    """
    Révoque une clé API par son ID.
    
     SÉCURITÉ :
    - Vérifie que la clé appartient à l'utilisateur actuel
    - Marque revoked_at = maintenant (active check lors de verify_api_key)
    - L'utilisateur ne peut révoquer que ses propres clés
    
    ARGS:
        key_id: UUID de la clé à révoquer
    
    RAISES:
        404 : clé non trouvée ou appartient à un autre utilisateur
        200 : clé révoquée avec succès
    """
    # ── REQUÊTE ─────────────────────────────────────────────────────────────
    
    try:
        key_id_uuid = UUID(key_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid key ID format (must be UUID)",
        )
    
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id_uuid,
        APIKey.user_id == current_user.id,
        APIKey.tenant_id == current_user.tenant_id,
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or doesn't belong to you",
        )
    
    if api_key.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clé API déjà révoquée",
        )
    
    # ── RÉVOCATION ──────────────────────────────────────────────────────────
    
    api_key.revoked_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to revoke API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key",
        )
    
    # ── AUDIT ───────────────────────────────────────────────────────────────
    
    try:
        log_action(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action="apikey.revoked",
            resource_type="api_key",
            resource_id=str(api_key.id),
            old_value={"name": api_key.name, "prefix": api_key.key_prefix},
            status="success",
            ip_address=get_client_ip(http_request) if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None,
        )
    except Exception as e:
        logger.warning(f"⚠️  Failed to log audit: {e}")
    
    logger.info(f"✅ API key revoked: {api_key.key_prefix} (user={current_user.id})")
    
    return APIKeyRevokeResponse(
        message="Clé API révoquée avec succès",
        key_id=str(api_key.id),
        revoked_at=api_key.revoked_at
    )
