# ==============================================================================
# SERVICE: EMAIL_SERVICE — 📧 SMTP Native Integration
# ==============================================================================

import os
import logging
import smtplib
from typing import Tuple
from datetime import datetime, timezone, timedelta
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ==============================================================================
#  CONFIGURATION ET LOGGING
# ==============================================================================

logger = logging.getLogger(__name__)

# Backoff multiplier: 1 min, 5 min, 30 min
RETRY_DELAYS = [
    timedelta(minutes=1),   # First retry: 1 minute
    timedelta(minutes=5),   # Second retry: 5 minutes
    timedelta(minutes=30),  # Third retry: 30 minutes
]

# SMTP configuration from environment
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@tenderai.io")
SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


def _validate_smtp_config() -> None:
    """
    Valide que la configuration SMTP est complète.
    
    Raises:
        ValueError: Si des paramètres obligatoires manquent
    """
    missing = []
    if not SMTP_HOST:
        missing.append("SMTP_HOST")
    if not SMTP_USER:
        missing.append("SMTP_USER")
    if not SMTP_PASSWORD:
        missing.append("SMTP_PASSWORD")
    if not SMTP_FROM:
        missing.append("SMTP_FROM")
    
    if missing:
        raise ValueError(
            f"SMTP configuration incomplete. Missing: {', '.join(missing)}. "
            f"Configure these ENV variables: {', '.join(missing)}"
        )


# ==============================================================================
#  EMAIL SERVICE BASE CLASS
# ==============================================================================

class EmailServiceBase(ABC):
    """
    Abstract base class pour services d'email
    
    Permet des implementations multiples (Resend, SendGrid, etc.)
    sans coupler le code applicatif à une seule librairie
    """
    
    @abstractmethod
    def send_email(self, to: str, subject: str, html: str) -> Tuple[bool, str]:
        """
        Envoyer un email
        
        Args:
            to: Email du destinataire
            subject: Sujet du mail
            html: Contenu HTML pré-rendu
        
        Returns:
            Tuple[success: bool, message: str]
            - (True, message_id) si succès
            - (False, error_reason) si échec
        """
        pass


# ==============================================================================
#  SMTP EMAIL SERVICE
# ==============================================================================

class SMTPEmailService(EmailServiceBase):
    """
    Service d'email via SMTP natif Python
    
     SMTP = Simple Mail Transfer Protocol (RFC 5321)
    Standard universel supporté par tous les serveurs d'email
    
     Avantages SMTP natif:
    - Pas de dépendance externe (stdlib smtplib)
    - Compatible avec Gmail, Office365, serveurs privés
    - Configuration simple (host, port, user, password)
    - Support TLS/STARTTLS natif
    - Contrôle total sur le message MIME
    
     Configuration sécurisée:
    - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD en ENV
    - Pas d'exposé de credentials en logs
    - Errors gracefully handled
    
     Pattern:
    - Synchronous (pour APScheduler BackgroundScheduler)
    - Timeouts intégrés via context managers
    - Logs structurés pour debugging
    """
    
    def __init__(self) -> None:
        """
        Initialiser le service SMTP
        
        Valide que la configuration SMTP est complète.
        
        Raises:
            ValueError: Si config SMTP incomplète
        """
        _validate_smtp_config()
        
        logger.debug(
            f"✅ SMTPEmailService initialized | host={SMTP_HOST} | "
            f"port={SMTP_PORT} | user={SMTP_USER} | from={SMTP_FROM}"
        )
    
    def send_email(self, to: str, subject: str, html: str) -> Tuple[bool, str]:
        """
        Envoyer un email via SMTP
        
         Pattern:
        1. Validate inputs (non-empty, valid email-like formats)
        2. Create MIME message (multipart alternative)
        3. Connect to SMTP server with TLS/STARTTLS
        4. Authenticate with credentials
        5. Send email via server.sendmail()
        6. Handle success: return (True, message_id or "OK")
        7. Handle errors:
           - Network error → (False, network_error_message)
           - Authentication error → (False, auth_error)
           - SMTP error → (False, smtp_error_details)
        8. Log all events
        
        Args:
            to: Email du destinataire (ex: user@example.com)
            subject: Sujet du mail (ex: "Réinitialiser votre mot de passe")
            html: Contenu HTML (ex: <p>Cliquez <a href="...">ici</a></p>)
        
        Returns:
            Tuple[success: bool, detail: str]
            - (True, message_id) if sent
            - (False, error_reason) if failed
        
        Raises:
            Nothing (all errors caught and logged)
        """
        
        # =====================================================================
        # VALIDATION
        # =====================================================================
        if not to or not subject or not html:
            error_msg = "Invalid email params: empty to/subject/html"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        
        try:
            # =====================================================================
            # CREATE MIME MESSAGE
            # =====================================================================
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SMTP_FROM
            msg["To"] = to
            
            # Attach HTML content
            msg.attach(MIMEText(html, "html"))
            
            logger.info(
                f"📧 Sending email | to={to} | subject={subject[:50]}... | "
                f"from={SMTP_FROM}"
            )
            
            # =====================================================================
            # CONNECT TO SMTP SERVER AND SEND
            # =====================================================================
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                # Enable TLS if configured
                if SMTP_USE_TLS:
                    server.starttls()
                
                # Authenticate
                server.login(SMTP_USER, SMTP_PASSWORD)
                
                # Send email
                server.sendmail(SMTP_FROM, to, msg.as_string())
            
            # =====================================================================
            # HANDLE SUCCESS
            # =====================================================================
            logger.info(f"✅ Email sent successfully | to={to}")
            return True, "OK"
        
        except smtplib.SMTPAuthenticationError as e:
            # =====================================================================
            # AUTHENTICATION ERROR
            # =====================================================================
            error_msg = f"SMTP authentication failed: {str(e)}"
            logger.error(
                f"❌ SMTP auth error | to={to} | error={error_msg}",
                exc_info=True
            )
            return False, error_msg
        
        except smtplib.SMTPException as e:
            # =====================================================================
            # SMTP PROTOCOL ERROR
            # =====================================================================
            error_msg = f"SMTP error: {str(e)}"
            logger.error(
                f"❌ SMTP error | to={to} | error={error_msg}",
                exc_info=True
            )
            return False, error_msg
        
        except OSError as e:
            # =====================================================================
            # NETWORK ERROR (connection, timeout, DNS resolution)
            # =====================================================================
            error_msg = f"Network error: {str(e)}"
            logger.error(
                f"❌ Network error | to={to} | host={SMTP_HOST}:{SMTP_PORT} | "
                f"error={error_msg}",
                exc_info=True
            )
            return False, error_msg
        
        except Exception as e:
            # =====================================================================
            # UNEXPECTED ERROR
            # =====================================================================
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(
                f"❌ Unexpected error | to={to} | error={error_msg}",
                exc_info=True
            )
            return False, error_msg
    
    def get_retry_delay(self, attempt_number: int) -> timedelta:
        """
        Calculer le délai de retry basé sur le numéro de tentative
        
         Pattern:
        - Attempt 0 (première tentative) → pas de retry
        - Attempt 1 (re-try 1) → 1 minute
        - Attempt 2 (re-try 2) → 5 minutes
        - Attempt 3+ (re-try 3) → 30 minutes
        
        Args:
            attempt_number: Numéro de tentative (0-indexed)
        
        Returns:
            timedelta pour calculer next_retry_at
        """
        # attempt_number est 0-indexed, RETRY_DELAYS aussi
        if attempt_number >= len(RETRY_DELAYS):
            return RETRY_DELAYS[-1]  # Capped at 30 minutes
        
        return RETRY_DELAYS[attempt_number]
        # attempt_number est 0-indexed, RETRY_DELAYS aussi
        if attempt_number >= len(RETRY_DELAYS):
            return RETRY_DELAYS[-1]  # Capped at 30 minutes
        
        return RETRY_DELAYS[attempt_number]


# ==============================================================================
# 🏗️ SINGLETON FACTORY
# ==============================================================================

_email_service_instance: SMTPEmailService | None = None


def get_email_service() -> SMTPEmailService:
    """
    Get or create the singleton email service instance
    
     Singleton pattern:
    - Une seule instance créée
    - Réutilisée pour toutes les opérations
    - Valide la config SMTP au démarrage
    - Logs l'initialisation
    
    Returns:
        SMTPEmailService instance (cached)
    
    Raises:
        ValueError: Si config SMTP incomplète
    """
    global _email_service_instance
    
    if _email_service_instance is None:
        _email_service_instance = SMTPEmailService()
        logger.info(
            f"✅ Email service initialized | type=SMTP | "
            f"host={SMTP_HOST} | port={SMTP_PORT} | from={SMTP_FROM}"
        )
    
    return _email_service_instance
