# ==============================================================================
# app/scheduler/scheduler.py — APScheduler Background Tasks
# ==============================================================================


import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import timezone

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    """
    Démarre le scheduler APScheduler avec les jobs configurés.
    
    À appeler dans le lifespan FastAPI (on_startup).
    """
    if scheduler.running:
        logger.info("✅ Scheduler déjà en cours d'exécution")
        return

    # Job : Rotation des clés EdDSA chaque nuit à 2h UTC
    scheduler.add_job(
        func=_rotate_keys_job,
        trigger=CronTrigger(hour=2, minute=0, timezone=timezone.utc),
        id="rotate_eddsa_keys",
        name="Rotation des clés EdDSA",
        replace_existing=True,
        misfire_grace_time=60,  # Tolérance 1min si le job ne peut pas démarrer à l'heure prévue
    )

    # Job : Nettoyage des sessions orphelines chaque nuit à 3h UTC
    scheduler.add_job(
        func=_cleanup_orphaned_sessions_job,
        trigger=CronTrigger(hour=3, minute=0, timezone=timezone.utc),
        id="cleanup_orphaned_sessions",
        name="Nettoyage des sessions orphelines",
        replace_existing=True,
        misfire_grace_time=60,
    )

    # Job : Purge des documents supprimés chaque nuit à 4h UTC
    scheduler.add_job(
        func=_purge_expired_documents_job,
        trigger=CronTrigger(hour=4, minute=0, timezone=timezone.utc),
        id="purge_expired_documents",
        name="Purge des documents expirés (hard delete)",
        replace_existing=True,
        misfire_grace_time=60,
    )

    scheduler.start()
    logger.info("🚀 Scheduler APScheduler démarré")
    logger.info("📅 Job programmé : Rotation EdDSA chaque nuit à 2h UTC")
    logger.info("📅 Job programmé : Nettoyage sessions à 3h UTC")
    logger.info("📅 Job programmé : Purge documents chaque nuit à 4h UTC")


def stop_scheduler() -> None:
    """
    Arrête le scheduler proprement.
    
    À appeler dans le lifespan FastAPI (on_shutdown).
    """
    if not scheduler.running:
        logger.info("ℹ️  Scheduler n'est pas en cours d'exécution")
        return

    scheduler.shutdown(wait=True)
    logger.info("🛑 Scheduler APScheduler arrêté")


def _rotate_keys_job() -> None:
    """
    Job interne : rotation des clés EdDSA.

    Appelé par APScheduler à 2h UTC chaque nuit.
    """
    try:
        logger.info("🔑 Démarrage du job de rotation des clés...")
        from app.security.auth.key_manager import check_and_rotate_keys
        check_and_rotate_keys()
        logger.info("✅ Job de rotation complété")
    except Exception as e:
        logger.error(f"❌ Erreur lors du job de rotation : {e}", exc_info=True)


def _cleanup_orphaned_sessions_job() -> None:
    """
    Job interne : nettoyage des sessions orphelines.

    Supprime les sessions qui :
    - Ont été révoquées (revoked_at IS NOT NULL)
    - N'ont jamais été utilisées (last_used_at IS NULL)
    - Ont expiré depuis plus de 24 heures

    Cela nettoie les sessions dupliquées créées en cas d'appel double
    de l'endpoint /auth/login ou /auth/refresh.

    Appelé par APScheduler à 3h UTC chaque nuit (après rotation des clés à 2h).
    """
    try:
        logger.info("🧹 Démarrage du nettoyage des sessions orphelines...")
        from datetime import datetime, timedelta, timezone as tz
        from app.database import SessionLocal
        from app.models import AuthSession

        db = SessionLocal()
        try:
            cutoff_time = datetime.now(tz.utc) - timedelta(hours=24)

            # Compter les sessions avant suppression (pour log)
            count_before = db.query(AuthSession).filter(
                AuthSession.revoked_at.isnot(None),
                AuthSession.last_used_at.is_(None),
                AuthSession.expires_at < cutoff_time,
            ).count()

            # Supprimer les sessions orphelines
            deleted = db.query(AuthSession).filter(
                AuthSession.revoked_at.isnot(None),
                AuthSession.last_used_at.is_(None),
                AuthSession.expires_at < cutoff_time,
            ).delete()

            db.commit()

            if deleted > 0:
                logger.info(f"✅ Nettoyage complété : {deleted} sessions orphelines supprimées")
            else:
                logger.debug("ℹ️  Aucune session orpheline à nettoyer")

        except Exception as job_error:
            db.rollback()
            logger.error(f"❌ Erreur lors du nettoyage : {job_error}", exc_info=True)
        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Erreur lors du job de nettoyage : {e}", exc_info=True)


def _purge_expired_documents_job() -> None:
    """
    Job interne : purge des documents supprimés (hard delete de MinIO).

    Trouve tous les documents où :
    - is_deleted = True
    - purge_after < now (la période de rétention de 30 jours est expirée)
    - purged_at IS NULL (pas encore purgés)

    Pour chaque document :
    1. Appelle minio_client.delete_file(document.storage_path)
    2. Set purged_at = now
    3. Commit

    Permet une période d'audit/recovery de 30 jours avant suppression définitive.

    Appelé par APScheduler à 4h UTC chaque nuit (après nettoyage des sessions à 3h).
    """
    try:
        logger.info("🧹 Démarrage de la purge des documents expirés...")
        from datetime import datetime, timezone as tz
        from app.database import SessionLocal
        from app.models import Document
        from app.storage import minio_client

        db = SessionLocal()
        try:
            now = datetime.now(tz.utc)

            # Trouver les documents à purger
            expired_docs = db.query(Document).filter(
                Document.is_deleted == True,
                Document.purge_after.isnot(None),
                Document.purge_after < now,
                Document.purged_at.is_(None),
            ).all()

            if not expired_docs:
                logger.debug("ℹ️  Aucun document à purger")
                return

            logger.info(f"📄 {len(expired_docs)} documents expirés trouvés pour purge")

            purged_count = 0
            error_count = 0

            for doc in expired_docs:
                try:
                    # Supprimer le fichier de MinIO
                    logger.debug(f"🗑️  Suppression MinIO : {doc.storage_path}")
                    minio_client.delete_file(doc.storage_path)

                    # Marquer comme purgé
                    doc.purged_at = now
                    db.add(doc)

                    purged_count += 1
                    logger.debug(f"✅ Document {doc.id} purgé (fichier supprimé de MinIO)")

                except Exception as delete_error:
                    logger.error(
                        f"❌ Erreur suppression MinIO pour {doc.id} ({doc.storage_path}) : {delete_error}",
                        exc_info=True
                    )
                    error_count += 1
                    # Continuer avec les autres documents même en cas d'erreur
                    continue

            # Commit tous les changements
            db.commit()

            logger.info(
                f"✅ Purge complétée : {purged_count} documents supprimés de MinIO, "
                f"{error_count} erreurs"
            )

        except Exception as job_error:
            db.rollback()
            logger.error(f"❌ Erreur lors de la purge : {job_error}", exc_info=True)
        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Erreur lors du job de purge : {e}", exc_info=True)
