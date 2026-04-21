# ==============================================================================
# scheduler/jobs.py - Définition des jobs de planification
# ==============================================================================

import logging
import httpx
from typing import Optional
from config import settings
from logger import logger


class KeyRotationJob:
    """
    Job de rotation des clés EdDSA.
    
    Appelé par APScheduler à l'heure configurée.
    Lance un appel HTTP à l'api-gateway pour effectuer la rotation.
    """
    
    def __init__(self, api_gateway_url: str, api_secret: Optional[str] = None):
        """
        Args:
            api_gateway_url: URL de base de l'API Gateway
            api_secret: Secret pour l'endpoint privé (optionnel)
        """
        self.api_gateway_url = api_gateway_url
        self.api_secret = api_secret
    
    def run(self) -> None:
        """
        Exécute la rotation des clés.
        
        Effectue un appel HTTP POST à l'endpoint privé :
        POST /api/v1/internal/scheduler/rotate-keys
        
        Gère les erreurs gracieusement pour ne pas bloquer le scheduler.
        """
        logger.info("🔑 Démarrage du job de rotation des clés EdDSA...")
        
        try:
            endpoint = f"{self.api_gateway_url}/api/v1/internal/scheduler/rotate-keys"
            headers = {}
            
            # Ajouter le header secret si configuré
            if self.api_secret:
                headers["X-Scheduler-Secret"] = self.api_secret
            
            logger.debug(f"📤 Appel HTTP POST : {endpoint}")
            
            with httpx.Client() as client:
                response = client.post(
                    endpoint,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info("✅ Rotation des clés EdDSA complétée avec succès")
                    result = response.json()
                    logger.info(f"📊 Détails : {result}")
                else:
                    logger.error(
                        f"❌ Erreur lors de la rotation : "
                        f"HTTP {response.status_code} - {response.text}"
                    )
        
        except httpx.ConnectError as e:
            logger.error(f"❌ Impossible de se connecter à l'API Gateway : {e}")
            logger.info("⏳ Nouvelle tentative au prochain cycle du scheduler")
        
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors du job : {e}", exc_info=True)
            logger.info("⏳ Nouvelle tentative au prochain cycle du scheduler")


def run_key_rotation_job() -> None:
    """
    Wrapper pour APScheduler.
    
    À utiliser comme func= dans scheduler.add_job()
    """
    job = KeyRotationJob(
        api_gateway_url=settings.API_GATEWAY_URL,
        api_secret=settings.API_GATEWAY_SECRET
    )
    job.run()


# ==============================================================================
# SESSION CLEANUP JOB
# ==============================================================================

class SessionCleanupJob:
    """
    Job de nettoyage des sessions expirées.
    
    Appelé par APScheduler toutes les heures.
    Lance un appel HTTP à l'api-gateway pour supprimer les vieilles sessions.
    """
    
    def __init__(self, api_gateway_url: str, scheduler_secret: Optional[str] = None):
        """
        Args:
            api_gateway_url: URL de base de l'API Gateway
            scheduler_secret: Secret pour l'endpoint privé
        """
        self.api_gateway_url = api_gateway_url
        if not scheduler_secret:
            raise ValueError(
                "SCHEDULER_SECRET is required and must be set in environment variables. "
                "No fallback secret allowed."
            )
        self.scheduler_secret = scheduler_secret
    
    def run(self) -> None:
        """
        Exécute le nettoyage des sessions expirées.
        
        Effectue un appel HTTP POST à l'endpoint privé :
        POST /api/v1/internal/cleanup/sessions
        
        Supprime :
        - Access tokens expirés depuis > 1 jour
        - Refresh tokens révoqués depuis > 30 jours
        - Partial tokens (2FA) expirés depuis > 1 heure
        
        ⚠️ SÉCURITÉ :
        - Header X-Scheduler-Secret obligatoire (verification côté API)
        - IP whitelist (127.0.0.1 + Docker networks 172.17-20.0.0/16)
        - Timeout court (30s) pour éviter les attaques de ressource
        """
        logger.info("🧹 Démarrage du job de nettoyage des sessions...")
        
        try:
            endpoint = f"{self.api_gateway_url}/api/v1/internal/cleanup/sessions"
            headers = {
                "X-Scheduler-Secret": self.scheduler_secret,
                "User-Agent": "TenderAI-Scheduler/1.0",
            }
            
            logger.debug(f"📤 Appel HTTP POST : {endpoint}")
            logger.debug(f"🔐 Headers : X-Scheduler-Secret={self.scheduler_secret[:10]}***")
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    endpoint,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info("✅ Nettoyage des sessions complété avec succès")
                    result = response.json()
                    
                    # Log le résumé de manière lisible
                    total = result.get('total_deleted', 0)
                    access_count = result.get('deleted_access', 0)
                    refresh_count = result.get('deleted_refresh_old', 0)
                    partial_count = result.get('deleted_partial', 0)
                    
                    if total > 0:
                        logger.warning(
                            f"📊 CLEANUP SUMMARY: {total} sessions supprimées\n"
                            f"   • Access tokens (>1j exp): {access_count}\n"
                            f"   • Refresh tokens (>30j rev): {refresh_count}\n"
                            f"   • Partial tokens (>1h exp): {partial_count}"
                        )
                    else:
                        logger.info("📊 Aucune session à nettoyer")
                
                elif response.status_code == 403:
                    logger.error(
                        f"❌ Accès refusé au nettoyage (403) : {response.text}\n"
                        f"   Vérifiez le secret SCHEDULER_SECRET et l'IP du serveur scheduler"
                    )
                
                else:
                    logger.error(
                        f"❌ Erreur lors du nettoyage : "
                        f"HTTP {response.status_code} - {response.text}"
                    )
        
        except httpx.ConnectError as e:
            logger.error(f"❌ Impossible de se connecter à l'API Gateway : {e}")
            logger.info("   Vérifiez API_GATEWAY_URL et que le service est en cours d'exécution")
            logger.info("⏳ Nouvelle tentative à la prochaine heure")
        
        except httpx.TimeoutException as e:
            logger.error(f"❌ Timeout lors de l'appel cleanup (30s) : {e}")
            logger.info("⏳ Nouvelle tentative à la prochaine heure")
        
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors du job : {e}", exc_info=True)
            logger.info("⏳ Nouvelle tentative à la prochaine heure")


def run_session_cleanup_job() -> None:
    """
    Wrapper pour APScheduler.
    
    À utiliser comme func= dans scheduler.add_job()
    """
    job = SessionCleanupJob(
        api_gateway_url=settings.API_GATEWAY_URL,
        scheduler_secret=settings.SCHEDULER_SECRET
    )
    job.run()


# ==============================================================================
# EMAIL PROCESSING JOB
# ==============================================================================

class EmailProcessJob:
    """
    Job de traitement des emails en attente via SMTP.
    
    Appelé par APScheduler toutes les 30 secondes.
    Lance un appel HTTP à l'api-gateway pour traiter les emails pending.
    
    🎯 Architecture :
    1. API Gateway traite max 50 emails par run
    2. SMTP envoie chaque email via smtplib
    3. Succès → status='sent', sent_at=now()
    4. Échec (attempts < 3) → next_retry_at = now() + backoff
    5. Échec (attempts >= 3) → status='failed', archivé
    6. Retour: { "processed": N, "sent": N, "failed": N, "retried": N }
    """
    
    def __init__(self, api_gateway_url: str, scheduler_secret: Optional[str] = None):
        """
        Args:
            api_gateway_url: URL de base de l'API Gateway
            scheduler_secret: Secret pour l'endpoint privé
        """
        self.api_gateway_url = api_gateway_url
        if not scheduler_secret:
            raise ValueError(
                "SCHEDULER_SECRET is required and must be set in environment variables. "
                "No fallback secret allowed."
            )
        self.scheduler_secret = scheduler_secret
    
    def run(self) -> None:
        """
        Exécute le traitement des emails en attente.
        
        Effectue un appel HTTP POST à l'endpoint privé :
        POST /api/v1/internal/email/process
        
        ⚠️ SÉCURITÉ :
        - Header X-Scheduler-Secret obligatoire (verification côté API)
        - Timeout court (30s) pour éviter les attaques de ressource
        - Pas d'exposition d'erreurs sensibles aux logs non-admin
        """
        logger.info("📧 Démarrage du job de traitement des emails...")
        
        try:
            endpoint = f"{self.api_gateway_url}/api/v1/internal/email/process"
            headers = {
                "X-Scheduler-Secret": self.scheduler_secret,
                "User-Agent": "TenderAI-Scheduler/1.0",
            }
            
            logger.debug(f"📤 Appel HTTP POST : {endpoint}")
            logger.debug(f"🔐 Headers : X-Scheduler-Secret={self.scheduler_secret[:10]}***")
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    endpoint,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info("✅ Traitement des emails complété")
                    result = response.json()
                    
                    # Log le résumé de manière lisible
                    processed = result.get('processed', 0)
                    sent = result.get('sent', 0)
                    failed = result.get('failed', 0)
                    retried = result.get('retried', 0)
                    
                    if processed > 0:
                        logger.info(
                            f"📧 EMAIL PROCESSING SUMMARY: {processed} emails traités\n"
                            f"   • Envoyés: {sent}\n"
                            f"   • Échecs définitifs: {failed}\n"
                            f"   • En retry: {retried}"
                        )
                    else:
                        logger.debug("📧 Aucun email à traiter")
                
                elif response.status_code == 403:
                    logger.error(
                        f"❌ Accès refusé au traitement email (403) : {response.text}\n"
                        f"   Vérifiez le secret SCHEDULER_SECRET et l'IP du serveur scheduler"
                    )
                
                else:
                    logger.error(
                        f"❌ Erreur lors du traitement des emails : "
                        f"HTTP {response.status_code} - {response.text}"
                    )
        
        except httpx.ConnectError as e:
            logger.error(f"❌ Impossible de se connecter à l'API Gateway : {e}")
            logger.info("   Vérifiez API_GATEWAY_URL et que le service est en cours d'exécution")
            logger.info("⏳ Nouvelle tentative dans 30 secondes")
        
        except httpx.TimeoutException as e:
            logger.error(f"❌ Timeout lors de l'appel email (30s) : {e}")
            logger.info("⏳ Nouvelle tentative dans 30 secondes")
        
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors du job : {e}", exc_info=True)
            logger.info("⏳ Nouvelle tentative dans 30 secondes")


def run_email_process_job() -> None:
    """
    Wrapper pour APScheduler.
    
    À utiliser comme func= dans scheduler.add_job()
    """
    job = EmailProcessJob(
        api_gateway_url=settings.API_GATEWAY_URL,
        scheduler_secret=settings.SCHEDULER_SECRET
    )
    job.run()
