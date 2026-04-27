"""
TOTP 2FA setup, verification, and management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional
import os
from cryptography.fernet import Fernet
import logging

from app.auth import get_current_user, verify_password
from app.database import get_db
from app.audit_service import log_action
from app.core.ratelimit import get_client_ip, check_rate_limit
from app.models.user import User
from app.models.user_totp import UserTOTP
from app.models.auth_session import AuthSession
from app.security.totp import (
    generate_totp_secret,
    get_totp_uri,
    generate_qr_code,
    verify_totp_code,
    generate_backup_codes,
    hash_backup_code,
    verify_backup_code,
)
from app.security.cookies import set_auth_cookies

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth/2fa", tags=["2fa"])

# Get encryption key from environment
ENCRYPTION_KEY = os.getenv("SECRET_ENCRYPTION_KEY")
if ENCRYPTION_KEY:
    cipher_suite = Fernet(ENCRYPTION_KEY.encode())
else:
    cipher_suite = None


# Pydantic models
class TOTPVerifyRequest(BaseModel):
    code: str


class TOTPDisableRequest(BaseModel):
    password: str


class TOTPSetupResponse(BaseModel):
    qr_code: str
    secret: str
    backup_codes: list[str]
    message: str


class TOTPVerifyResponse(BaseModel):
    message: str
    is_enabled: bool


class TOTPDisableResponse(BaseModel):
    message: str


def encrypt_secret(secret: str) -> str:
    """Encrypt TOTP secret using Fernet."""
    if not cipher_suite:
        raise RuntimeError("SECRET_ENCRYPTION_KEY not configured")
    return cipher_suite.encrypt(secret.encode()).decode()


def decrypt_secret(encrypted_secret: str) -> str:
    """Decrypt TOTP secret using Fernet."""
    if not cipher_suite:
        raise RuntimeError("SECRET_ENCRYPTION_KEY not configured")
    return cipher_suite.decrypt(encrypted_secret.encode()).decode()


@router.post("/setup", response_model=TOTPSetupResponse)
async def setup_2fa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initialize 2FA setup for the current user.
    
    Returns QR code, secret, and backup codes.
    User must call /verify endpoint to activate 2FA.
    
     REQUIREMENTS:
    - User email must be verified (email_verified = true)
    - User cannot have 2FA already enabled
    """
    
    # ── Check if email is verified ─────────────────────────────────────────────
    if not current_user.email_verified:
        logger.warning(f"⚠️  User {current_user.id} attempted 2FA setup with unverified email")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Veuillez d'abord vérifier votre email."
            }
        )
    
    # Check if encryption key is configured
    if not cipher_suite:
        logger.error("SECRET_ENCRYPTION_KEY not set - 2FA setup cannot proceed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Encryption key not configured",
        )
    
    # Check if 2FA already enabled
    existing = db.query(UserTOTP).filter(
        UserTOTP.user_id == current_user.id,
        UserTOTP.is_enabled,
    ).first()
    
    if existing:
        logger.warning(f"User {current_user.id} attempted to set up 2FA but it's already enabled")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled for this account",
        )
    
    # Generate new secret
    secret = generate_totp_secret()
    
    # Check if uncommitted setup exists (replace it)
    totp_record = db.query(UserTOTP).filter(
        UserTOTP.user_id == current_user.id
    ).first()
    
    if totp_record:
        # Delete old uncommitted setup
        logger.info(f"Deleting previous uncommitted 2FA setup for user {current_user.id}")
        db.delete(totp_record)
        db.commit()
    
    # Generate backup codes
    plaintext_codes = generate_backup_codes(10)
    hashed_codes = [hash_backup_code(code) for code in plaintext_codes]
    
    # Create new TOTP record (not enabled yet)
    encrypted_secret = encrypt_secret(secret)
    
    new_totp = UserTOTP(
        id=None,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        secret=encrypted_secret,
        is_enabled=False,
        backup_codes=hashed_codes,
        created_at=datetime.now(timezone.utc),
    )
    
    db.add(new_totp)
    db.commit()
    
    # Generate QR code
    uri = get_totp_uri(secret, current_user.email)
    qr_code = generate_qr_code(uri)
    
    return TOTPSetupResponse(
        qr_code=qr_code,
        secret=secret,  # Only revealed at setup time
        backup_codes=plaintext_codes,
        message="Scan the QR code with your authenticator app, then call /verify to activate",
    )


@router.post("/verify", response_model=TOTPVerifyResponse)
async def verify_2fa(
    http_request: Request,
    request: TOTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify TOTP code and activate 2FA.
    
    Must have called /setup first.
    """
    
    # Find uncommitted TOTP setup
    totp_record = db.query(UserTOTP).filter(
        UserTOTP.user_id == current_user.id
    ).first()
    
    if not totp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No 2FA setup found. Call /setup first.",
        )
    
    # Decrypt secret and verify code
    try:
        decrypted_secret = decrypt_secret(totp_record.secret)
    except Exception as e:
        logger.error(f"Failed to decrypt secret for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Encryption error",
        )
    
    # Verify TOTP code
    if not verify_totp_code(decrypted_secret, request.code):
        # Log failed verification attempt
        log_action(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="totp.verified",
            resource_type="2fa",
            resource_id=current_user.id,
            status="failure",
            reason="Invalid 2FA code",
            ip_address=http_request.client.host if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None,
        )
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid code",
        )
    
    # Activate 2FA
    totp_record.is_enabled = True
    totp_record.verified_at = datetime.now(timezone.utc)
    db.commit()
    
    # Log successful verification
    log_action(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="totp.enabled",
        resource_type="2fa",
        resource_id=current_user.id,
        old_value={"is_enabled": False},
        new_value={"is_enabled": True, "verified_at": datetime.now(timezone.utc).isoformat()},
        status="success",
        reason="2FA successfully activated",
        ip_address=http_request.client.host if http_request else None,
        user_agent=http_request.headers.get("user-agent") if http_request else None,
    )
    db.commit()
    
    return TOTPVerifyResponse(
        message="2FA activated successfully",
        is_enabled=True,
    )


@router.post("/disable", response_model=TOTPDisableResponse)
async def disable_2fa(
    http_request: Request,
    request: TOTPDisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disable 2FA for the current user.
    
    Requires password verification for security.
    """
    
    # Check if user has a password set
    if not current_user.hashed_password:
        logger.error(f"User {current_user.id} has no hashed_password configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User password not configured",
        )
    
    # NOW verify password (after confirming hash exists)
    # Verify password - arguments are: (plain_password, hashed_password)
    #  Important: the order matters!
    if not verify_password(request.password, current_user.hashed_password):
        logger.warning(f"Invalid password verification attempt for 2FA disable by user {current_user.id}")
        log_action(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="totp.disabled",
            resource_type="2fa",
            resource_id=current_user.id,
            status="failure",
            reason="Invalid password",
            ip_address=http_request.client.host if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None,
        )
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )
    
    # Check if 2FA is enabled
    totp_record = db.query(UserTOTP).filter(
        UserTOTP.user_id == current_user.id,
        UserTOTP.is_enabled,
    ).first()
    
    if not totp_record:
        log_action(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="totp.disabled",
            resource_type="2fa",
            resource_id=current_user.id,
            status="failure",
            reason="2FA not enabled",
            ip_address=http_request.client.host if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None,
        )
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled for this account",
        )
    
    # Delete TOTP record
    db.delete(totp_record)
    db.commit()
    
    # Log successful deactivation
    log_action(
        db=db,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="totp.disabled",
        resource_type="2fa",
        resource_id=current_user.id,
        old_value={"is_enabled": True},
        new_value={"is_enabled": False},
        status="success",
        reason="2FA disabled by user",
        ip_address=http_request.client.host if http_request else None,
        user_agent=http_request.headers.get("user-agent") if http_request else None,
    )
    db.commit()
    
    return TOTPDisableResponse(
        message="2FA disabled successfully",
    )


# ============================================================================
# 2FA LOGIN ENDPOINT
# ============================================================================

class TOTPLoginRequest(BaseModel):
    partial_token: str
    code: Optional[str] = None
    backup_code: Optional[str] = None


class TOTPLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@router.post("/login", response_model=TOTPLoginResponse)
async def login_with_2fa(
    http_request: Request,
    request: TOTPLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Complete login with 2FA verification.
    
    Flow:
    1. User calls /auth/login
    2. If 2FA enabled, receives partial_token (type="2fa_pending", expires in 5 min)
    3. User enters TOTP code from authenticator
    4. Calls this endpoint with partial_token + code
    5. If valid → returns full access_token + refresh_token
    6. Updates last_used_at on user_totp record
    
    Can also use backup codes instead of TOTP code.
    """
    from app.security import verify_jwt_token
    from app.security import create_access_token, create_refresh_token
    from app.models.user import User
    from datetime import timedelta
    import jwt as _jwt
    
    # Import token constants
    from app.auth import (
        ACCESS_TOKEN_EXPIRE_MINUTES,
        REFRESH_TOKEN_EXPIRE_DAYS,
    )
    
    # Verify partial token
    try:
        payload = verify_jwt_token(request.partial_token)
    except Exception as e:
        logger.error(f"Invalid partial token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired partial token. Please login again.",
        )
    
    # Check token type
    if payload.get("type") != "partial":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Expected partial token.",
        )
    
    
    from app.auth import _check_jti_valid
    partial_jti = payload.get("jti")
    if not partial_jti or not _check_jti_valid(db, partial_jti):
        logger.warning(f"[2FA SECURITY] Revoked or invalid partial_token JTI: {partial_jti}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Partial token already used or expired. Please login again.",
        )
    
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    email = payload.get("email") or payload.get("sub")  # Extract email for rate limiting
    
    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )
    
    # Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )
    
    # Verify tenant matches
    if str(user.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant mismatch.",
        )
    
    # Fetch TOTP record
    totp_record = db.query(UserTOTP).filter(
        UserTOTP.user_id == user_id,
        UserTOTP.is_enabled,
    ).first()
    
    logger.info(f"[2FA DEBUG] user_id: {user_id}")
    logger.info(f"[2FA DEBUG] totp_record found: {totp_record is not None}")
    logger.info(f"[2FA DEBUG] is_enabled: {totp_record.is_enabled if totp_record else 'N/A'}")
    
    if not totp_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="2FA not enabled for this account.",
        )
    
    # Decrypt secret
    try:
        decrypted_secret = decrypt_secret(totp_record.secret)
        logger.info(f"[2FA DEBUG] secret decrypted length: {len(decrypted_secret) if decrypted_secret else 0}")
        logger.info(f"[2FA DEBUG] code received: {request.code}")
    except Exception as e:
        logger.error(f"Failed to decrypt secret: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Encryption error.",
        )
    
    
    ip_address = get_client_ip(http_request)
    check_rate_limit(
        db=db,
        ip_address=ip_address,
        email=email,
        max_attempts=5,
        window_minutes=1
    )
    
    # Try to verify TOTP code first
    code_to_verify = request.code or request.backup_code
    
    is_totp_valid = verify_totp_code(decrypted_secret, code_to_verify) if code_to_verify else False
    logger.info(f"[2FA DEBUG] verification result: {is_totp_valid}")
    import pyotp
    totp = pyotp.TOTP(decrypted_secret)
    logger.info(f"[2FA DEBUG] current valid code: {totp.now()}")
    
    # Enhanced debugging
    logger.info(f"[2FA DEBUG] code_to_verify: '{code_to_verify}'")
    logger.info(f"[2FA DEBUG] secret length: {len(decrypted_secret)}")
    logger.info(f"[2FA DEBUG] is_totp_valid: {is_totp_valid}")
    totp_obj = pyotp.TOTP(decrypted_secret)
    logger.info(f"[2FA DEBUG] expected code NOW: {totp_obj.now()}")
    logger.info(f"[2FA DEBUG] expected code PREV: {totp_obj.at(datetime.now(timezone.utc), -1)}")
    
    # If TOTP invalid, try backup code
    is_backup_valid = False
    remaining_codes = totp_record.backup_codes
    if not is_totp_valid and code_to_verify:
        is_backup_valid, remaining_codes = verify_backup_code(
            code_to_verify,
            totp_record.backup_codes or []
        )
    
    if not is_totp_valid and not is_backup_valid:
        # Log failed 2FA attempt
        log_action(
            db=db,
            user_id=user.id,
            tenant_id=user.tenant_id,
            action="session.failed",
            resource_type="auth_session",
            resource_id=user.id,
            status="failure",
            reason="Invalid TOTP code or backup code",
            ip_address=http_request.client.host if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None,
        )
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid TOTP code or backup code.",
        )
    
    # If backup code was used, update remaining codes
    if is_backup_valid:
        totp_record.backup_codes = remaining_codes
        db.commit()
        
        # Log backup code usage
        log_action(
            db=db,
            user_id=user.id,
            tenant_id=user.tenant_id,
            action="use_backup_code",
            resource_type="2fa",
            resource_id=user.id,
            new_value={"codes_remaining": len(remaining_codes)},
            status="success",
            reason="Backup code used for 2FA login",
            ip_address=http_request.client.host if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None,
        )
        db.commit()
    
    # Update last_used_at
    totp_record.last_used_at = datetime.now(timezone.utc)
    db.commit()
    
    # Extract user_agent and ip_address from request
    user_agent = http_request.headers.get("user-agent") if http_request else None
    ip_address = http_request.client.host if http_request else None
    
    # Create full tokens
    token_data = {"sub": str(user.id), "tenant_id": str(user.tenant_id)}
    access_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_delta,
    )
    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    
    # ── Store access and refresh token sessions in DB (for multi-device tracking) ──
    ap = _jwt.decode(access_token, options={"verify_signature": False})
    rp = _jwt.decode(refresh_token, options={"verify_signature": False})
    
    from app.auth import create_auth_session, revoke_auth_session
    
    
    db.query(AuthSession).filter(
        AuthSession.user_id == user.id,
        AuthSession.revoked_at == None,  # noqa: E711
        AuthSession.expires_at > datetime.now(timezone.utc),
    ).update({"revoked_at": datetime.now(timezone.utc)})
    
   
    create_auth_session(
        db, user.id, user.tenant_id, ap["jti"], "access", 
        access_delta, user_agent=user_agent, ip_address=ip_address
    )
    create_auth_session(
        db, user.id, user.tenant_id, rp["jti"], "refresh",
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=user_agent, ip_address=ip_address
    )
    
    # ── Revoke the partial token (one-time use only) ───────────────────────────
    # partial_jti was already extracted and validated earlier (line ~430)
    # Now mark it as revoked to prevent replay attacks
    if partial_jti:
        revoke_auth_session(db, partial_jti)
    
    db.commit()
    
    # Log successful 2FA login
    log_action(
        db=db,
        user_id=user.id,
        tenant_id=user.tenant_id,
        action="session.started",
        resource_type="auth_session",
        resource_id=user.id,
        status="success",
        reason="2FA login successful",
        ip_address=http_request.client.host if http_request else None,
        user_agent=http_request.headers.get("user-agent") if http_request else None,
    )
    db.commit()
    
    # Return response with httpOnly cookies (same pattern as /auth/login)
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
