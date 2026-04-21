# ==============================================================================
# app/services/password_reset.py — Gestion de la réinitialisation de mot de passe
# ==============================================================================


import os
import logging
import redis
import secrets
from typing import Tuple, Optional
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from ..models import User, EmailJob, EmailJobType, EmailJobStatus, AuthSession
from ..auth import get_password_hash
from .email_service import get_email_service
from ..audit_service import log_action

logger = logging.getLogger(__name__)

# ==============================================================================
#  REDIS CONNECTION
# ==============================================================================

def _get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client for storing temporary tokens
    
    Returns: redis.Redis instance or None if unavailable
    """
    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"⚠️ Redis not available: {e}")
        return None


# ==============================================================================
#  PASSWORD RESET TOKENS
# ==============================================================================

TOKEN_TTL_SECONDS = 3600  # 1 hour
TOKEN_LENGTH = 32  # Characters for token (256 bits of entropy)
RESET_SESSION_KEY_PREFIX = "pwd_reset"


def generate_reset_token() -> str:
    """
    Generate a cryptographically secure password reset token
    
     Security:
    - 32 bytes = 256 bits of entropy
    - secrets module (cryptographic PRNG)
    - URL-safe encoding (base62)
    
    Returns:
        Secure token string (32 characters)
    """
    return secrets.token_urlsafe(TOKEN_LENGTH)


def store_reset_token(redis_client: redis.Redis, user_id: UUID) -> str:
    """
    Generate and store a reset token in Redis
    
    Args:
        redis_client: Redis connection
        user_id: UUID of user requesting reset
    
    Returns:
        Reset token (send to user via email)
    
    Redis key: f"pwd_reset:{token}" → user_id (TTL: 1 hour)
    """
    token = generate_reset_token()
    key = f"{RESET_SESSION_KEY_PREFIX}:{token}"
    
    # Store with 1-hour expiry
    redis_client.setex(key, TOKEN_TTL_SECONDS, str(user_id))
    
    logger.debug(f"✅ Reset token stored | user_id={user_id} | expires_in=1h")
    return token


def verify_reset_token(redis_client: redis.Redis, token: str) -> Optional[UUID]:
    """
    Verify a reset token and retrieve the associated user_id
    
    Args:
        redis_client: Redis connection
        token: Token from user's email link
    
    Returns:
        UUID of user if valid, None if expired/invalid
    """
    key = f"{RESET_SESSION_KEY_PREFIX}:{token}"
    user_id_str = redis_client.get(key)
    
    if not user_id_str:
        logger.warning(f"⚠️ Reset token invalid or expired | token={token[:10]}...")
        return None
    
    # Delete immediately after retrieval (single-use token)
    redis_client.delete(key)
    
    try:
        return UUID(user_id_str)
    except ValueError:
        logger.error(f"❌ Invalid UUID in reset token | uuid={user_id_str}")
        return None


# ==============================================================================
#  PASSWORD RESET EMAIL
# ==============================================================================

def create_password_reset_email(
    user_email: str,
    tenant_id: UUID,
    reset_token: str,
    organization_name: str,
    frontend_url: str = "https://tenderai.io"
) -> Tuple[str, str]:
    """
    Build password reset email subject and HTML body
    
    Args:
        user_email: Recipient email
        tenant_id: For audit trail
        reset_token: Token to include in reset link
        organization_name: Tenant name for personalization
        frontend_url: Base URL for reset link (e.g., https://tenderai.io)
    
    Returns:
        Tuple of (subject, html_body)
    """
    reset_link = f"{frontend_url}/auth/password-reset?token={reset_token}"
    
    subject = f"TenderAI — Réinitialisez votre mot de passe"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 20px; }}
            .header {{ background: #0066cc; color: white; padding: 20px; border-radius: 5px 5px 0 0; text-align: center; }}
            .content {{ background: white; padding: 20px; border-radius: 0 0 5px 5px; }}
            .button {{ display: inline-block; background: #0066cc; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ margin-top: 20px; font-size: 12px; color: #666; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Réinitialisation du mot de passe</h1>
            </div>
            <div class="content">
                <p>Bonjour,</p>
                
                <p>Vous avez demandé une réinitialisation de votre mot de passe pour <strong>{organization_name}</strong> sur TenderAI.</p>
                
                <p><strong>⚠️ Important :</strong> Ce lien expire dans <strong>1 heure</strong>.</p>
                
                <p>Cliquez sur le bouton ci-dessous pour réinitialiser votre mot de passe :</p>
                
                <center>
                    <a href="{reset_link}" class="button">Réinitialiser le mot de passe</a>
                </center>
                
                <p>Ou copiez ce lien dans votre navigateur :</p>
                <p style="background: #f0f0f0; padding: 10px; word-break: break-all; font-size: 12px;">
                    {reset_link}
                </p>
                
                <p style="margin-top: 30px; color: #666; font-size: 13px;">
                    <strong>Vous n'avez pas demandé cette réinitialisation ?</strong><br>
                    Veuillez ignorer cet email. Votre compte reste sécurisé.
                </p>
            </div>
            <div class="footer">
                <p>© 2026 TenderAI — Plateforme de gestion des appels d'offres</p>
                <p>Email: {user_email}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return subject, html_body


def create_reset_email_job(
    db: Session,
    user_id: UUID,
    user_email: str,
    tenant_id: UUID,
    reset_token: str,
    organization_name: str
) -> EmailJob:
    """
    Create an EmailJob record for password reset email
    
    Args:
        db: SQLAlchemy session
        user_id: User requesting reset (for audit)
        user_email: Email to send to
        tenant_id: Organization ID
        reset_token: Token to include in email
        organization_name: Tenant name for email content
    
    Returns:
        EmailJob created (not yet committed)
    """
    subject, html_body = create_password_reset_email(
        user_email=user_email,
        tenant_id=tenant_id,
        reset_token=reset_token,
        organization_name=organization_name
    )
    
    email_job = EmailJob(
        tenant_id=tenant_id,
        job_type=EmailJobType.PASSWORD_RESET,
        recipient_email=user_email,
        subject=subject,
        html_body=html_body,
        status=EmailJobStatus.PENDING,
        attempts=0,
        next_retry_at=None  # Send immediately
    )
    
    db.add(email_job)
    logger.debug(f"✅ Reset email job created | user_id={user_id} | email={user_email}")
    
    return email_job


# ==============================================================================
#  PUBLIC API: PASSWORD RESET FLOW
# ==============================================================================

def handle_password_reset_request(
    db: Session,
    email: str
) -> None:
    """
    Handle password reset request (P0 feature)
    
    🎯 Security: No user enumeration
    - Always return 200 OK
    - Email sent only if user exists
    - Generic response message
    
    Args:
        db: SQLAlchemy session
        email: Email address to send reset link to
    
    Returns:
        None (always succeeds from client perspective)
    """
    redis_client = _get_redis_client()
    if not redis_client:
        logger.error("❌ Redis client unavailable for password reset")
        # Still return success to client (don't reveal infrastructure issues)
        return
    
    # Find user by email (no user enumeration message returned)
    user = db.query(User).filter(User.email == email.lower()).first()
    
    if not user:
        logger.info(f"ℹ️ Password reset requested for non-existent email | email={email}")
        return  # Always return success
    
    if not user.is_active:
        logger.warning(f"⚠️ Password reset requested for inactive user | user_id={user.id}")
        return  # Still return success
    
    try:
        # Generate token
        reset_token = store_reset_token(redis_client, user.id)
        
        # Create email job
        create_reset_email_job(
            db=db,
            user_id=user.id,
            user_email=user.email,
            tenant_id=user.tenant_id,
            reset_token=reset_token,
            organization_name=user.tenant.name if user.tenant else "TenderAI"
        )
        
        db.commit()
        
        logger.info(
            f"✅ Password reset email queued | user_id={user.id} | "
            f"email={user.email} | token_ttl=1h"
        )
    
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Error during password reset request | email={email} | error={str(e)}",
            exc_info=True
        )
        # Still return success to client


def handle_password_reset_confirm(
    db: Session,
    token: str,
    new_password: str
) -> Tuple[bool, str]:
    redis_client = _get_redis_client()
    if not redis_client:
        return False, "Service temporarily unavailable"

    try:
        user_id = verify_reset_token(redis_client, token)
        if not user_id:
            logger.warning("⚠️ Invalid reset token provided")
            return False, "Invalid or expired reset token"

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"⚠️ User not found after token verification | user_id={user_id}")
            return False, "User not found"

        if not user.is_active:
            logger.warning(f"⚠️ Inactive user attempted password reset | user_id={user_id}")
            return False, "Account is inactive"

        # Mettre à jour le mot de passe
        user.hashed_password = get_password_hash(new_password)
        db.add(user)

        # Révoquer toutes les sessions actives
        db.query(AuthSession).filter(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at == None  # noqa: E711
        ).update({"revoked_at": datetime.now(timezone.utc)})

        db.commit()

        # Audit log
        log_action(
            db=db,
            user_id=user.id,
            tenant_id=user.tenant_id,
            action="password.reset",
            resource_type="user",
            resource_id=user.id,
            reason="All sessions revoked after password reset",
            status="success"
        )

        return True, "Password reset successfully. Please login again."

    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Error during password reset confirm | token={token[:10]}... | error={str(e)}",
            exc_info=True
        )
        return False, "An error occurred during password reset"
