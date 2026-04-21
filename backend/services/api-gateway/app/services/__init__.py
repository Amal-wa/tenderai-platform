# ==============================================================================
# SERVICES — Couche de services métier (email, notifications, etc.)
# ==============================================================================


from .email_service import SMTPEmailService, get_email_service, EmailServiceBase
from .welcome_email import create_welcome_email, create_welcome_email_job

__all__ = [
    "SMTPEmailService",
    "get_email_service",
    "EmailServiceBase",
    "create_welcome_email",
    "create_welcome_email_job",
]
