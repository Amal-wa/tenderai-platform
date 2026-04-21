# ==============================================================================
# SERVICE: WELCOME_EMAIL — 📧 Bienvenue Email après Registration
# ==============================================================================
from typing import Tuple
from uuid import UUID
from sqlalchemy.orm import Session
import logging

from ..models import EmailJob, EmailJobType, EmailJobStatus

logger = logging.getLogger(__name__)


def create_welcome_email(
    first_name: str,
    last_name: str,
    tenant_name: str,
    trial_ends_at: str,  # ISO format string
    user_email: str,
    frontend_url: str = "https://tenderai.io"
) -> Tuple[str, str]:
    """
    Build welcome email subject and HTML body
    
    Features:
    - Personalized greeting (first_name + last_name)
    - Organization context (tenant_name)
    - Trial end date
    - Login button to start using the platform
    - Inline CSS for email client compatibility
    - Navy/amber/cream palette (accessible design)
    
    Args:
        first_name: User's first name
        last_name: User's last name
        tenant_name: Organization name (from Tenant)
        trial_ends_at: Trial end date in ISO format (e.g., "2026-04-26T15:30:00+00:00")
        user_email: Recipient email address
        frontend_url: Base URL for login link (default: https://tenderai.io)
    
    Returns:
        Tuple of (subject, html_body)
    
    Example:
        >>> subject, html = create_welcome_email(
        ...     first_name="Jean",
        ...     last_name="Dupont",
        ...     tenant_name="Sup'Com",
        ...     trial_ends_at="2026-04-26T15:30:00+00:00",
        ...     user_email="jean@supcom.tn",
        ...     frontend_url="https://tenderai.io"
        ... )
    """
    
    # Parse trial end date and format for display (e.g., "26 avril 2026")
    from datetime import datetime
    
    try:
        trial_dt = datetime.fromisoformat(trial_ends_at.replace('Z', '+00:00'))
        # Format en français
        trial_date_fr = trial_dt.strftime("%d %B %Y")  # e.g., "26 April 2026"
        
        # Translate month names to French if needed
        months_fr = {
            'January': 'janvier', 'February': 'février', 'March': 'mars',
            'April': 'avril', 'May': 'mai', 'June': 'juin',
            'July': 'juillet', 'August': 'août', 'September': 'septembre',
            'October': 'octobre', 'November': 'novembre', 'December': 'décembre'
        }
        for en, fr in months_fr.items():
            trial_date_fr = trial_date_fr.replace(en, fr)
    except Exception:
        trial_date_fr = trial_ends_at  # Fallback to raw date
    
    login_url = f"{frontend_url}/login"
    
    subject = f"Bienvenue sur TenderAI, {first_name} !"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #0F1C35;
                background-color: #F5F3EE;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #FFFFFF;
                padding: 0;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(15, 28, 53, 0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #0F1C35 0%, #1a2c4a 100%);
                color: #FFFFFF;
                padding: 32px 24px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
                letter-spacing: -0.5px;
            }}
            .content {{
                padding: 32px 24px;
                background: #FFFFFF;
            }}
            .greeting {{
                font-size: 16px;
                margin-bottom: 20px;
            }}
            .organization {{
                background: #F5F3EE;
                border-left: 4px solid #C4962A;
                padding: 16px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .organization-label {{
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 4px;
            }}
            .organization-name {{
                font-size: 18px;
                font-weight: 600;
                color: #0F1C35;
            }}
            .trial-info {{
                background: #FFF8F0;
                border: 1px solid #E8D5C4;
                padding: 16px;
                border-radius: 8px;
                margin: 20px 0;
                font-size: 14px;
            }}
            .trial-info strong {{
                color: #C4962A;
            }}
            .button {{
                display: inline-block;
                background: #C4962A;
                color: #FFFFFF;
                padding: 14px 32px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                margin: 24px 0;
                transition: background 0.2s;
                border: none;
                cursor: pointer;
            }}
            .button:hover {{
                background: #b08129;
            }}
            .divider {{
                border: none;
                border-top: 1px solid #E8D5C4;
                margin: 24px 0;
            }}
            .section {{
                margin: 24px 0;
            }}
            .section-title {{
                font-size: 14px;
                font-weight: 600;
                color: #0F1C35;
                margin-bottom: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .section-content {{
                font-size: 14px;
                color: #333;
                line-height: 1.8;
            }}
            .footer {{
                background: #F5F3EE;
                padding: 20px 24px;
                text-align: center;
                font-size: 12px;
                color: #666;
                border-top: 1px solid #E8D5C4;
            }}
            .footer p {{
                margin: 8px 0;
            }}
            a {{
                color: #C4962A;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- ============================================================
                 HEADER
                 ============================================================ -->
            <div class="header">
                <h1>🎉 Bienvenue</h1>
            </div>
            
            <!-- ============================================================
                 MAIN CONTENT
                 ============================================================ -->
            <div class="content">
                <div class="greeting">
                    <p>Bonjour <strong>{first_name}</strong>,</p>
                    <p>Merci de votre inscription sur TenderAI ! Nous sommes ravis de vous accueillir.</p>
                </div>
                
                <!-- Organization Context -->
                <div class="organization">
                    <div class="organization-label">📦 Votre organisation</div>
                    <div class="organization-name">{tenant_name}</div>
                </div>
                
                <!-- Trial Period Info -->
                <div class="trial-info">
                    <p>✨ <strong>Vous bénéficiez d'une période d'essai gratuite de 14 jours</strong></p>
                    <p style="margin-top: 8px;">
                        Accès complet à toutes les fonctionnalités jusqu'au <strong>{trial_date_fr}</strong>.
                    </p>
                </div>
                
                <!-- CTA Button -->
                <div style="text-align: center;">
                    <a href="{login_url}" class="button">Accéder à mon compte →</a>
                </div>
                
                <!-- Divider -->
                <hr class="divider">
                
                <!-- Getting Started Section -->
                <div class="section">
                    <div class="section-title">🚀 Pour bien commencer</div>
                    <div class="section-content">
                        <p><strong>1. Complétez votre profil</strong> – Ajoutez les membres de votre équipe pour collaborer</p>
                        <p><strong>2. Configurez vos préférences</strong> – Choisissez votre secteur d'activité et vos besoins</p>
                        <p><strong>3. Explorez les appels d'offres</strong> – Accédez à une base de données complète des marchés publics</p>
                    </div>
                </div>
                
                <!-- Support Section -->
                <div class="section">
                    <div class="section-title">❓ Besoin d'aide ?</div>
                    <div class="section-content">
                        <p>Consultez notre <a href="{frontend_url}/help">centre d'aide</a> ou contactez notre équipe support à <strong>support@tenderai.io</strong></p>
                    </div>
                </div>
            </div>
            
            <!-- ============================================================
                 FOOTER
                 ============================================================ -->
            <div class="footer">
                <p><strong>TenderAI</strong> — Plateforme intelligente de gestion des appels d'offres publics</p>
                <p>Email: <a href="mailto:{user_email}">{user_email}</a></p>
                <p>© 2026 TenderAI. Tous droits réservés.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return subject, html_body


def create_welcome_email_job(
    db: Session,
    user_id: UUID,
    user_email: str,
    first_name: str,
    last_name: str,
    tenant_id: UUID,
    tenant_name: str,
    trial_ends_at: str,  # ISO format string from datetime.isoformat()
    frontend_url: str = "https://tenderai.io"
) -> EmailJob:
    """
    Create an EmailJob record for welcome email
    
    Called after successful registration (step 7).
    The EmailJob is added to the DB session but NOT committed yet.
    Commit happens at the main register endpoint level.
    
    Args:
        db: SQLAlchemy session
        user_id: New user ID (for audit trail)
        user_email: Email to send welcome to
        first_name: User's first name
        last_name: User's last name
        tenant_id: Organization ID
        tenant_name: Organization name (ex: "Sup'Com")
        trial_ends_at: Trial end date in ISO format
        frontend_url: Base URL for login link (default: https://tenderai.io)
    
    Returns:
        EmailJob created (NOT committed)
    
    Example:
        >>> job = create_welcome_email_job(
        ...     db=db,
        ...     user_id=uuid4(),
        ...     user_email="user@example.com",
        ...     first_name="Jean",
        ...     last_name="Dupont",
        ...     tenant_id=uuid4(),
        ...     tenant_name="Sup'Com",
        ...     trial_ends_at="2026-04-26T15:30:00+00:00",
        ...     frontend_url="https://tenderai.io"
        ... )
        >>> db.add(job)  # Already added, but shown for clarity
        >>> db.commit()  # Happens at endpoint level
    """
    
    subject, html_body = create_welcome_email(
        first_name=first_name,
        last_name=last_name,
        tenant_name=tenant_name,
        trial_ends_at=trial_ends_at,
        user_email=user_email,
        frontend_url=frontend_url
    )
    
    email_job = EmailJob(
        tenant_id=tenant_id,
        job_type=EmailJobType.WELCOME_EMAIL,
        recipient_email=user_email,
        subject=subject,
        html_body=html_body,
        status=EmailJobStatus.PENDING,
        attempts=0,
        next_retry_at=None  # Send immediately (next scheduler run)
    )
    
    db.add(email_job)
    logger.info(
        f"✅ Welcome email job created | user_id={user_id} | "
        f"email={user_email} | tenant_name={tenant_name}"
    )
    
    return email_job
