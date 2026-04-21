# ==============================================================================
# scheduler/main.py - Point d'entrée du service Scheduler
# ==============================================================================


import logging
import signal
import sys
from datetime import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import settings
from logger import logger
from jobs import run_key_rotation_job, run_session_cleanup_job, run_email_process_job


class SchedulerService:
    """Service principal de planification."""
    
    def __init__(self):
        """Initialise le scheduler APScheduler."""
        self.scheduler = BackgroundScheduler(
            timezone=timezone.utc
        )
        self.running = False
    
    def setup_jobs(self) -> None:
        """Configure tous les jobs de planification."""
        
        logger.info("📋 Configuration des jobs de planification...")
        
        # Job : Rotation des clés EdDSA
        self.scheduler.add_job(
            func=run_key_rotation_job,
            trigger=CronTrigger(
                hour=settings.KEY_ROTATION_SCHEDULE_HOUR,
                minute=settings.KEY_ROTATION_SCHEDULE_MINUTE,
                timezone=timezone.utc
            ),
            id="rotate_eddsa_keys",
            name="🔑 Rotation des clés EdDSA",
            replace_existing=True,
            misfire_grace_time=60,  # Tolérance 1min si le job rate l'heure
        )
        
        logger.info(
            f"✅ Job configué : Rotation EdDSA chaque nuit "
            f"à {settings.KEY_ROTATION_SCHEDULE_HOUR:02d}:"
            f"{settings.KEY_ROTATION_SCHEDULE_MINUTE:02d} UTC"
        )
        
        # Job : Nettoyage des sessions expirées (toutes les heures)
        self.scheduler.add_job(
            func=run_session_cleanup_job,
            trigger=CronTrigger(
                minute=0,  # À chaque heure juste
                timezone=timezone.utc
            ),
            id="cleanup_expired_sessions",
            name="🧹 Nettoyage des sessions expirées",
            replace_existing=True,
            misfire_grace_time=60,  # Tolérance 1min
        )
        
        logger.info("✅ Job configué : Nettoyage des sessions chaque heure")
        
        # Job : Traitement des emails en attente (toutes les 30 secondes)
        self.scheduler.add_job(
            func=run_email_process_job,
            trigger=IntervalTrigger(
                seconds=30,  # Toutes les 30 secondes
                timezone=timezone.utc
            ),
            id="process_email_jobs",
            name="📧 Traitement des emails en attente",
            replace_existing=True,
            misfire_grace_time=60,  # Tolérance 1min si délai
        )
        
        logger.info("✅ Job configué : Traitement des emails toutes les 30 secondes")
    
    def start(self) -> None:
        """Démarre le scheduler."""
        if self.running:
            logger.warning("⚠️  Scheduler déjà en cours d'exécution")
            return
        
        logger.info("🚀 Démarrage du Scheduler...")
        
        self.setup_jobs()
        self.scheduler.start()
        self.running = True
        
        logger.info("✅ Scheduler démarré avec succès")
        logger.info("📅 En attente des jobs programmés...")
    
    def stop(self) -> None:
        """Arrête le scheduler proprement."""
        if not self.running:
            logger.info("ℹ️  Scheduler n'est pas en cours d'exécution")
            return
        
        logger.info("🛑 Arrêt du Scheduler...")
        
        try:
            self.scheduler.shutdown(wait=True)
            self.running = False
            logger.info("✅ Scheduler arrêté proprement")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'arrêt : {e}", exc_info=True)


# Instance globale du service
_scheduler_service: SchedulerService = None


def get_scheduler_service() -> SchedulerService:
    """Obtient l'instance unique du service scheduler."""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service


def handle_shutdown(signum, frame):
    """Gestionnaire pour les signaux SIGTERM/SIGINT."""
    logger.info(f"📌 Signal reçu ({signum}), arrêt gracieux en cours...")
    service = get_scheduler_service()
    service.stop()
    
    # Marquer le fichier de santé
    try:
        import os
        if os.path.exists("/tmp/scheduler_running"):
            os.remove("/tmp/scheduler_running")
    except:
        pass
    
    sys.exit(0)


def main():
    """Point d'entrée principal."""
    
    logger.info("=" * 80)
    logger.info("🎯 TenderAI Scheduler Service v0.1.0")
    logger.info("=" * 80)
    
    # Configuration
    logger.info(f"📡 API Gateway URL: {settings.API_GATEWAY_URL}")
    logger.info(f"🌍 Timezone: {settings.SCHEDULER_TIMEZONE}")
    logger.info(f"📊 Log Level: {settings.LOG_LEVEL}")
    
    # Démarrer le scheduler
    service = get_scheduler_service()
    service.start()
    
    # Créer fichier de santé
    try:
        with open("/tmp/scheduler_running", "w") as f:
            f.write("1")
    except:
        pass
    
    # Installer les gestionnaires de signaux
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    logger.info("✅ Service prêt. En attente des tâches planifiées...")
    
    # Boucle principale (APScheduler tourne en arrière-plan)
    try:
        while True:
            signal.pause()  # Attend les signaux
    except KeyboardInterrupt:
        logger.info("👋 Intéruption clavier reçue")
        service.stop()


if __name__ == "__main__":
    main()
