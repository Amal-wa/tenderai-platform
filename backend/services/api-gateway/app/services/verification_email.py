# ==============================================================================
# services/verification_email.py — Gestion de l'email de vérification
# ==============================================================================

from uuid import UUID
from sqlalchemy.orm import Session

from app.models.email_job import EmailJob, EmailJobType, EmailJobStatus


def create_verification_email_job(
    db: Session,
    user_id: UUID,
    user_email: str,
    first_name: str,
    verification_token: str,
    frontend_url: str,
    tenant_id: UUID,
) -> EmailJob:
    """
    Crée un EmailJob pour l'email de vérification d'adresse email.
    
     EMAIL STRUCTURE:
    - Subject: Vérifiez votre adresse email — TenderAI
    - Body: HTML avec:
      - Greeting personnalisé (first_name)
      - Lien de vérification (valide 24h)
      - Message de sécurité
      - Support link
    
     LIEN:
    {frontend_url}/register/verify-email?token={verification_token}
    
    ⏱ RETRY STRATEGY:
    - Status: PENDING (envoyer immédiatement)
    - Retries: 0 (pas d'essais précédents)
    - Next retry: NULL (envoyer tout de suite)
    - Exponential backoff: 1m → 5m → 30m (max 3 retries)
    
    Args:
        db: Database session
        user_id: UUID de l'utilisateur
        user_email: Email destinataire
        first_name: Prénom pour personnalisation
        verification_token: JWT avec TTL 24h
        frontend_url: Base URL du frontend (ex: https://tenderai.io)
        tenant_id: Organization ID (must NOT be None — DB constraint)
    
    Returns:
        EmailJob créé et persisté
    """
    
    verification_link = f"{frontend_url}/register/verify-email?token={verification_token}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'IBM Plex Sans', Arial, sans-serif; color: #0F1C35; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #0F1C35; color: #F5F3EE; padding: 20px; text-align: center; border-radius: 4px 4px 0 0; }}
            .content {{ background-color: #F5F3EE; padding: 30px; border-radius: 0 0 4px 4px; }}
            .button {{ display: inline-block; background-color: #C4962A; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; margin: 20px 0; }}
            .footer {{ font-size: 12px; color: #999; text-align: center; margin-top: 20px; }}
            .urgent {{ background-color: #FFE5E5; padding: 12px; border-left: 4px solid #E74C3C; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">TenderAI</h1>
            </div>
            <div class="content">
                <p>Bonjour {first_name},</p>
                
                <p>Merci de votre inscription sur <strong>TenderAI</strong> ! Avant de commencer, veuillez vérifier votre adresse email en cliquant le lien ci-dessous :</p>
                
                <center>
                    <a href="{verification_link}" class="button">Vérifier mon email</a>
                </center>
                
                <p>ou copiez-collez ce lien :</p>
                <p style="background-color: #EEE; padding: 10px; border-radius: 4px; word-break: break-all; font-size: 12px;">
                    {verification_link}
                </p>
                
                <div class="urgent">
                    <strong>⏰ Ce lien expire dans 24 heures.</strong>
                </div>
                
                <p>Une fois votre email vérifié, vous devrez configurer votre authentification 2FA pour sécuriser votre compte.</p>
                
                <p>Si vous n'avez pas créé ce compte, veuillez ignorer cet email.</p>
                
                <div class="footer">
                    <p>© 2026 TenderAI. Tous droits réservés.</p>
                    <p>Support: <a href="mailto:support@tenderai.io">support@tenderai.io</a></p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    job = EmailJob(
        tenant_id=tenant_id,  # ✅ NOW REQUIRED: Registration passes this after tenant creation
        job_type=EmailJobType.EMAIL_VERIFICATION,
        recipient_email=user_email,
        subject="Vérifiez votre adresse email — TenderAI",
        html_body=html_body,
        status=EmailJobStatus.PENDING,
        attempts=0,
        next_retry_at=None,  # Send immediately
    )
    
    db.add(job)
    db.flush()  
    
    return job

