# ==============================================================================
# app/services/user_invitation.py — Gestion des invitations d'utilisateurs
# ==============================================================================


import os
import logging
import redis
import secrets
from typing import Tuple, Optional
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from ..models import User, EmailJob, EmailJobType, EmailJobStatus
from ..auth import get_password_hash
from ..database import set_tenant_context
from ..models.user_totp import UserTOTP

logger = logging.getLogger(__name__)

# ==============================================================================
#  REDIS CONNECTION
# ==============================================================================

def _get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client for storing invitation tokens"""
    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"⚠️ Redis not available: {e}")
        return None


# ==============================================================================
# INVITATION TOKENS
# ==============================================================================

INVITE_TOKEN_TTL_SECONDS = 604800  # 7 days
INVITE_TOKEN_LENGTH = 32


def generate_invite_token() -> str:
    """
    Generate a cryptographically secure invitation token
    
    Returns: Secure token string (32 characters)
    """
    return secrets.token_urlsafe(INVITE_TOKEN_LENGTH)


def store_invite_token(
    redis_client: redis.Redis,
    inviter_id: UUID,
    recipient_email: str,
    role: str = "user"
) -> str:
    """
    Generate and store an invitation token in Redis
    
    Args:
        redis_client: Redis connection
        inviter_id: UUID of user sending invite
        recipient_email: Email to send invite to
        role: Role for new user (default: 'user')
    
    Returns:
        Invitation token (send to user via email)
    
    Redis key: f"invite:{token}" → {inviter_id}|{recipient_email}|{role}|{timestamp}
    """
    token = generate_invite_token()
    key = f"invite:{token}"
    
    value = f"{inviter_id}|{recipient_email}|{role}|{datetime.now(timezone.utc).isoformat()}"
    
    # Store with 7-day expiry
    redis_client.setex(key, INVITE_TOKEN_TTL_SECONDS, value)
    
    logger.debug(f"✅ Invite token stored | inviter={inviter_id} | email={recipient_email}")
    return token


def verify_invite_token(redis_client: redis.Redis, token: str) -> Optional[Tuple[UUID, str, str]]:
    """
    Verify an invite token and retrieve metadata
    
    Args:
        redis_client: Redis connection
        token: Token from invite email link
    
    Returns:
        Tuple of (inviter_id, recipient_email, role) if valid, None if expired/invalid
    """
    key = f"invite:{token}"
    value = redis_client.get(key)
    
    if not value:
        logger.warning(f"⚠️ Invite token invalid or expired")
        return None
    
    # Parse value
    parts = value.split("|")
    if len(parts) < 3:
        logger.error(f"❌ Invalid invite token format")
        return None
    
    try:
        inviter_id = UUID(parts[0])
        recipient_email = parts[1]
        role = parts[2]
        
        return inviter_id, recipient_email, role
    except (ValueError, IndexError) as e:
        logger.error(f"❌ Error parsing invite token: {e}")
        return None


# ==============================================================================
#  INVITATION EMAIL
# ==============================================================================

def create_invitation_email(
    recipient_email: str,
    inviter_name: str,
    organization_name: str,
    invite_token: str,
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
) -> Tuple[str, str]:
    """
    Build invitation email subject and HTML body
    
    Returns:
        Tuple of (subject, html_body)
    """
    accept_link = f"{frontend_url}/invite/accept?token={invite_token}"
    
    subject = f"Vous êtes invité à rejoindre {organization_name} sur TenderAI"
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
                <h1>Vous êtes invité!</h1>
            </div>
            <div class="content">
                <p>Bonjour,</p>
                
                <p><strong>{inviter_name}</strong> vous invite à rejoindre <strong>{organization_name}</strong> sur <strong>TenderAI</strong>.</p>
                
                <p>TenderAI est une plateforme de gestion des appels d'offres conçue pour simplifier votre processus d'approvisionnement.</p>
                
                <p><strong>⏰ Important :</strong> Ce lien est valable pendant <strong>7 jours</strong>.</p>
                
                <p>Cliquez sur le bouton ci-dessous pour accepter l'invitation et créer un compte :</p>
                
                <center>
                    <a href="{accept_link}" class="button">Accepter l'invitation</a>
                </center>
                
                <p>Ou copiez ce lien dans votre navigateur :</p>
                <p style="background: #f0f0f0; padding: 10px; word-break: break-all; font-size: 12px;">
                    {accept_link}
                </p>
                
                <p style="margin-top: 30px; color: #666; font-size: 13px;">
                    <strong>Vous n'aviez pas prévu cette invitation ?</strong><br>
                    Vous pouvez ignorer cet email ou contacter l'administrateur de {organization_name}.
                </p>
            </div>
            <div class="footer">
                <p>© 2026 TenderAI — Plateforme de gestion des appels d'offres</p>
                <p>Email: {recipient_email}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return subject, html_body


def create_invitation_email_job(
    db: Session,
    recipient_email: str,
    tenant_id: UUID,
    inviter_name: str,
    organization_name: str,
    invite_token: str,
    frontend_url: str | None = None
) -> EmailJob:
    """
    Create an EmailJob record for invitation email
    """
    subject, html_body = create_invitation_email(
        recipient_email=recipient_email,
        inviter_name=inviter_name,
        organization_name=organization_name,
        invite_token=invite_token,
        frontend_url=frontend_url or os.getenv("FRONTEND_URL", "http://localhost:3000")
    )
    
    email_job = EmailJob(
        tenant_id=tenant_id,
        job_type=EmailJobType.INVITATION,
        recipient_email=recipient_email,
        subject=subject,
        html_body=html_body,
        status=EmailJobStatus.PENDING,
        attempts=0,
        next_retry_at=None  # Send immediately
    )
    
    db.add(email_job)
    logger.debug(f"✅ Invitation email job created | email={recipient_email}")
    
    return email_job


# ==============================================================================
#  PUBLIC API: INVITATION FLOW
# ==============================================================================

def send_user_invitation(
    db: Session,
    recipient_email: str,
    inviter_id: UUID,
    tenant_id: UUID,
    inviter_name: str,
    organization_name: str,
    role: str = "user",
    frontend_url: str | None = None
) -> Tuple[bool, str]:
    """
    Send a user invitation (P0 feature)
    
    Args:
        db: SQLAlchemy session
        recipient_email: Email to invite
        inviter_id: UUID of user sending invite
        tenant_id: Organization ID
        inviter_name: Name of inviter (for email)
        organization_name: Organization name (for email)
        role: Role for new user
        frontend_url: Frontend base URL for invitation link (overrides env var)
    
    Returns:
        Tuple of (success: bool, invite_token: str or error_message: str)
    """
    redis_client = _get_redis_client()
    if not redis_client:
        logger.error("❌ Redis client unavailable for user invitation")
        return False, "Service temporarily unavailable"
    
    try:
        # Generate and store token
        invite_token = store_invite_token(
            redis_client,
            inviter_id,
            recipient_email.lower(),
            role
        )
        
        # Create email job
        create_invitation_email_job(
            db=db,
            recipient_email=recipient_email,
            tenant_id=tenant_id,
            inviter_name=inviter_name,
            organization_name=organization_name,
            invite_token=invite_token,
            frontend_url=frontend_url
        )
        
        db.commit()
        
        logger.info(
            f"✅ User invitation created | inviter={inviter_id} | "
            f"email={recipient_email} | token_ttl=7d"
        )
        
        return True, invite_token
    
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Error sending user invitation | email={recipient_email} | error={str(e)}",
            exc_info=True
        )
        return False, "An error occurred while sending the invitation"


def accept_user_invitation(
    db: Session,
    token: str,
    full_name: str,
    password: str
) -> Tuple[bool, str, UUID | None]:
    """
    Accept a user invitation and create account (P0 feature)
    
     Flow:
    1. Verify invitation token
    2. Check if user already exists (prevent duplicates)
    3. Create new user account
    4. Set role from invitation
    5. Update tenant context for RLS
    
    Args:
        db: SQLAlchemy session
        token: Invitation token from email
        full_name: New user's full name
        password: New user's password
    
    Returns:
        Tuple of (success: bool, message: str, user_id: UUID | None)
    """
    redis_client = _get_redis_client()
    if not redis_client:
        return False, "Service temporarily unavailable", None
    
    try:
        from ..models import Tenant, Role
        
        # Verify token
        result = verify_invite_token(redis_client, token)
        if not result:
            logger.warning(f"⚠️ Invalid invitation token")
            return False, "Invalid or expired invitation token", None
        
        inviter_id, recipient_email, role_name = result
        recipient_email = recipient_email.lower()
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            User.email == recipient_email
        ).first()

        if existing_user:
            if not existing_user.is_deleted:
                logger.warning(f"⚠️ User already exists | email={recipient_email}")
                return False, "Account already exists for this email", None
            else:
                db.query(UserTOTP).filter(
                    UserTOTP.user_id == existing_user.id
                ).delete(synchronize_session=False)
                existing_user.is_deleted = False
                existing_user.is_active = True
                existing_user.full_name = full_name
                existing_user.hashed_password = get_password_hash(password)
                existing_user.email_verified = True
                existing_user.last_login_at = None
                db.commit()
                db.refresh(existing_user)
                logger.info(f"✅ Reactivated | email={recipient_email}")
                return True, "Account reactivated successfully", existing_user.id
            
        # Get inviter to retrieve tenant_id
        inviter = db.query(User).filter(User.id == inviter_id).first()
        if not inviter:
            logger.warning(f"⚠️ Inviter not found | inviter_id={inviter_id}")
            return False, "Invitation is no longer valid", None
        
        tenant_id = inviter.tenant_id
        
        # Set tenant context for RLS
        set_tenant_context(db, tenant_id)
        
        # Get role by name (default to 'user' if not found)
        role = db.query(Role).filter(
            Role.tenant_id == tenant_id,
            Role.name == role_name
        ).first()
        
        if not role:
            logger.warning(f"⚠️ Role not found | role={role_name} | tenant={tenant_id}")
            role = db.query(Role).filter(
                Role.tenant_id == tenant_id,
                Role.name == "user"
            ).first()
        
        if not role:
            return False, "Role configuration error", None
        
        # Create new user
        # Nettoyage défensif — UserTOTP orphelins par email
        orphan_user = db.query(User).filter(
            User.email == recipient_email
        ).first()
        if orphan_user:
            db.query(UserTOTP).filter(
                UserTOTP.user_id == orphan_user.id
            ).delete(synchronize_session=False)
            db.commit()
        
        new_user = User(
            email=recipient_email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            tenant_id=tenant_id,
            role_id=role.id,
            is_active=True,
            email_verified=True
        )
        
        db.add(new_user)
        db.commit()
        
        # Token deleted AFTER TOTP activation (see routers/totp.py verify_2fa)
        # Store pending invitation token marker for later cleanup
        
        logger.info(
            f"✅ User invitation accepted | new_user={new_user.id} | "
            f"email={recipient_email} | role={role_name}"
        )
        
        return True, "Account created successfully", new_user.id
    
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Error accepting invitation | token={token[:10]}... | error={str(e)}",
            exc_info=True
        )
        return False, "An error occurred while accepting the invitation", None
