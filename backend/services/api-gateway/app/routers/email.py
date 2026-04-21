# ==============================================================================
# app/routers/email.py - Endpoint interne pour traitement des emails
# ==============================================================================


import logging
import hmac
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Header, Depends
from sqlalchemy.orm import Session
import os

from ..database import get_db
from ..models import EmailJob, EmailJobStatus
from ..services import get_email_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/internal/email",
    tags=["Email Processing (Internal)"],
)

# ============================================================================
# BATCH PROCESSING CONFIG
# ============================================================================
BATCH_SIZE = 50  # Traiter max 50 emails par scheduler run


# ============================================================================
# SECURITY: VERIFY SCHEDULER SECRET
# ============================================================================

def verify_scheduler_secret(x_scheduler_secret: Optional[str] = Header(None)) -> None:
    """
    Vérifie que le header secret est valide.
    
     Pattern: constant-time comparison (hmac.compare_digest)
    prevents timing attacks
    
    Utilise la variable d'environnement SCHEDULER_SECRET.
    """
    expected_secret = os.getenv("SCHEDULER_SECRET", "")
    
    # Si aucun secret configuré et pas de header, refuser
    if not expected_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scheduler secret not configured on server"
        )
    
    # Vérifier le header avec comparaison constant-time
    if not x_scheduler_secret or not hmac.compare_digest(
        x_scheduler_secret.encode(), expected_secret.encode()
    ):
        logger.warning("❌ Email processor: tentative d'authentification du scheduler échouée")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing scheduler secret"
        )


# ============================================================================
# EMAIL BATCH PROCESSOR
# ============================================================================

@router.post("/process")
def process_pending_emails(
    _: None = Depends(verify_scheduler_secret),
    db: Session = Depends(get_db)
) -> dict:
    """
    Traiter les emails en attente via SMTP.
    
    Workflow:
    1. SELECT EmailJob WHERE status='pending' AND (next_retry_at IS NULL OR <= now())
    2. Pour chaque email (max BATCH_SIZE):
       a. Appeler smtplib.SMTP.sendmail()
       b. Succès → UPDATE status='sent', sent_at=now()
       c. Échec (attempts < 3) → UPDATE attempts++, next_retry_at=backoff
       d. Échec (attempts >= 3) → UPDATE status='failed'
    3. Retourner statistiques de traitement
    
    **Authentification** : Header `X-Scheduler-Secret` requis
    
    **Retour** :
    ```json
    {
        "status": "success",
        "processed": 25,
        "sent": 23,
        "failed": 2,
        "retried": 0,
        "timestamp": "2024-03-27T02:15:30Z"
    }
    ```
    
    **Cas d'erreur** :
    - 403: Invalid scheduler secret
    - 500: Database error, service initialization error
    """
    try:
        logger.info("📧 Email processor: starting batch processing...")
        
        # ====================================================================
        # 1. QUERY PENDING EMAILS
        # ====================================================================
        # Note: RLS is NOT applied here (internal endpoint)
        # We're reading all pending emails for all tenants
        pending_emails = (
            db.query(EmailJob)
            .filter(
                EmailJob.status == EmailJobStatus.PENDING,
                (
                    (EmailJob.next_retry_at.is_(None)) |
                    (EmailJob.next_retry_at <= datetime.now(timezone.utc))
                )
            )
            .order_by(EmailJob.created_at.asc())  # FIFO order
            .limit(BATCH_SIZE)
            .all()
        )
        
        total_processed = 0
        total_sent = 0
        total_failed = 0
        total_retried = 0
        
        # ====================================================================
        # 2. PROCESS EACH EMAIL
        # ====================================================================
        email_service = get_email_service()
        
        logger.info(
            f"📧 Processing {len(pending_emails)} pending emails (batch size: {BATCH_SIZE})"
        )
        
        for email_job in pending_emails:
            total_processed += 1
            
            logger.debug(
                f"📧 Processing email | job_id={email_job.id} | "
                f"type={email_job.job_type.value} | to={email_job.recipient_email} | "
                f"attempt={email_job.attempts + 1}/3"
            )
            
            try:
                # ================================================================
                # Send via Resend
                # ================================================================
                success, detail = email_service.send_email(
                    to=email_job.recipient_email,
                    subject=email_job.subject,
                    html=email_job.html_body
                )
                
                if success:
                    # ================================================================
                    # SUCCESS: Update status to sent
                    # ================================================================
                    email_job.status = EmailJobStatus.SENT
                    email_job.sent_at = datetime.now(timezone.utc)
                    db.add(email_job)
                    total_sent += 1
                    
                    logger.info(
                        f"✅ Email sent | job_id={email_job.id} | "
                        f"recipient={email_job.recipient_email} | "
                        f"type={email_job.job_type.value} | resend_id={detail}"
                    )
                
                else:
                    # ================================================================
                    # FAILURE: Retry or mark as failed (3 attempts max)
                    # ================================================================
                    email_job.attempts += 1
                    email_job.error_message = detail
                    
                    if email_job.attempts < 3:
                        # Schedule retry with exponential backoff
                        retry_delay = email_service.get_retry_delay(email_job.attempts)
                        email_job.next_retry_at = (
                            datetime.now(timezone.utc) + retry_delay
                        )
                        db.add(email_job)
                        total_retried += 1
                        
                        logger.warning(
                            f"⚠️ Email failed, retry scheduled | job_id={email_job.id} | "
                            f"attempt={email_job.attempts} | error={detail[:100]} | "
                            f"retry_at={email_job.next_retry_at}"
                        )
                    
                    else:
                        # Max retries exceeded: mark as failed
                        email_job.status = EmailJobStatus.FAILED
                        db.add(email_job)
                        total_failed += 1
                        
                        logger.error(
                            f"❌ Email failed permanently | job_id={email_job.id} | "
                            f"recipient={email_job.recipient_email} | "
                            f"attempts={email_job.attempts} | error={detail}"
                        )
            
            except Exception as e:
                # Unexpected error during email processing
                logger.error(
                    f"❌ Unexpected error processing email job | job_id={email_job.id} | "
                    f"error={str(e)}",
                    exc_info=True
                )
                
                # Update error and attempts, same retry logic
                email_job.attempts += 1
                email_job.error_message = str(e)
                
                if email_job.attempts < 3:
                    retry_delay = email_service.get_retry_delay(email_job.attempts)
                    email_job.next_retry_at = (
                        datetime.now(timezone.utc) + retry_delay
                    )
                    db.add(email_job)
                    total_retried += 1
                else:
                    email_job.status = EmailJobStatus.FAILED
                    db.add(email_job)
                    total_failed += 1
        
        # ====================================================================
        # 3. COMMIT CHANGES
        # ====================================================================
        db.commit()
        
        logger.info(
            f"📧 Batch processing complete | processed={total_processed} | "
            f"sent={total_sent} | failed={total_failed} | retried={total_retried}"
        )
        
        return {
            "status": "success",
            "processed": total_processed,
            "sent": total_sent,
            "failed": total_failed,
            "retried": total_retried,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        logger.error(
            f"❌ Email processor error | error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email processing failed: {str(e)}"
        )
