# ==============================================================================
# RATELIMIT.PY — Protection contre les attaques brute-force
# ==============================================================================


import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy import and_, cast, String
from sqlalchemy.orm import Session

from ..models.login_attempt import LoginAttempt

logger = logging.getLogger(__name__)

# Constantes configurables
MAX_ATTEMPTS_PER_IP = 5       # Max tentatives par IP par fenêtre
MAX_ATTEMPTS_PER_EMAIL = 10   # Max tentatives par email par fenêtre
WINDOW_MINUTES = 1            # Durée de la fenêtre en minutes


def get_client_ip(request: Optional[Request]) -> str:
    """
    Extract real client IP address, validating X-Forwarded-For header.
    
    """
    if not request or not request.client:
        return "unknown"
    
    # Get trusted proxy IPs from environment
    trusted_proxies_env = os.getenv("TRUSTED_PROXIES", "127.0.0.1,::1")
    trusted_proxies = [ip.strip() for ip in trusted_proxies_env.split(",")]
    
    direct_ip = request.client.host
    
    # Only trust X-Forwarded-For if request came from a trusted proxy
    if direct_ip in trusted_proxies:
        forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if forwarded_for:
            return forwarded_for
    
    return direct_ip


def check_rate_limit(
    db: Session,
    ip_address: str,
    email: str,
    max_attempts: int = 5,
    window_minutes: int = 1,
) -> None:
    """
    Vérifie si une IP ou un email a dépassé la limite de tentatives.

    
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=window_minutes)

    # ──────────────────────────────────────────────────────────────────────────
    # VÉRIFICATION 1 : Limite par IP
    # ──────────────────────────────────────────────────────────────────────────
    if ip_address:
        
        ip_failures = db.query(LoginAttempt).filter(
            and_(
                cast(LoginAttempt.ip_address, String) == ip_address,
                LoginAttempt.created_at >= window_start,
                LoginAttempt.success == False,  # noqa: E712
            )
        ).count()

        if ip_failures >= max_attempts:
            logger.warning(
                "Rate limit dépassé — IP: %s | %d tentatives en %d min",
                ip_address, ip_failures, window_minutes
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Trop de tentatives de connexion depuis votre adresse IP. "
                    f"Réessayez dans {window_minutes} minute(s)."
                ),
                # Header standard HTTP pour indiquer quand réessayer
                headers={"Retry-After": str(window_minutes * 60)},
            )

    # ──────────────────────────────────────────────────────────────────────────
    # VÉRIFICATION 2 : Limite par email
    # ──────────────────────────────────────────────────────────────────────────
    # Protection contre les attaques distribuées :
    # un attaquant peut utiliser plusieurs IPs pour contourner la limite par IP.
    # La limite par email bloque cela.
    email_failures = db.query(LoginAttempt).filter(
        and_(
            LoginAttempt.email == email.lower(),  # Normaliser l'email
            LoginAttempt.created_at >= window_start,
            LoginAttempt.success == False,  # noqa: E712
        )
    ).count()

    if email_failures >= max_attempts:
        logger.warning(
            "Rate limit dépassé — email: %s | %d tentatives en %d min",
            email, email_failures, window_minutes
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Trop de tentatives de connexion sur ce compte. "
                f"Réessayez dans {window_minutes} minute(s)."
            ),
            headers={"Retry-After": str(window_minutes * 60)},
        )


def record_login_attempt(
    db: Session,
    email: str,
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    failure_reason: Optional[str] = None,
    user_id=None,
) -> LoginAttempt:
    """
    Enregistre une tentative de connexion dans la base de données.

    
    """
    attempt = LoginAttempt(
        email=email.lower(),  # Normaliser l'email
        success=success,
        ip_address=ip_address,
        user_agent=user_agent,
        failure_reason=failure_reason if not success else None,
        user_id=user_id,
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    # Logger pour le monitoring
    if success:
        logger.info("Login réussi — email: %s | ip: %s", email, ip_address)
    else:
        logger.warning(
            "Échec login — email: %s | ip: %s | raison: %s",
            email, ip_address, failure_reason
        )

    return attempt