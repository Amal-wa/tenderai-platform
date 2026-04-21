# ==============================================================================
# app/security/auth/key_manager.py — Unified EdDSA Key Management
# ==============================================================================

import os
import logging
import redis
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from dotenv import set_key

logger = logging.getLogger(__name__)


class KeyAlgorithm(str, Enum):
    """Algorithmes de signature supportés."""
    EdDSA = "EdDSA"  # ED25519 — recommandé
    RS256 = "RS256"
    HS256 = "HS256"


class KeyBackend(ABC):
    """
    Interface abstraite pour les backends de gestion des clés.
    
    Deux implémentations :
    - VaultBackend : HashiCorp Vault (production)
    - EnvBackend : Variables d'environnement (développement)
    """

    @abstractmethod
    def get_current_keys(self) -> Optional[Dict[str, str]]:
        """
        Récupère les clés EdDSA courantes.
        
        Returns:
            Dict avec 'private_key' et 'public_key' (format PEM), ou None
        """
        pass

    @abstractmethod
    def get_previous_keys(self) -> Optional[Dict[str, str]]:
        """
        Récupère les clés publiques précédentes (pour validation anciens tokens).
        
        ⚠️ Retourne UNIQUEMENT 'public_key', jamais la clé privée précédente
           (elle n'est jamais sauvegardée par sécurité).
        
        Returns:
            Dict avec 'public_key' (format PEM), ou None si pas de rotation
        """
        pass

    @abstractmethod
    def save_current_keys(
        self,
        private_key: str,
        public_key: str,
        backup_previous: bool = True,
    ) -> bool:
        """
        Sauvegarde la nouvelle paire de clés courantes avec backup optionnel.
        
        ⚠️ Si backup_previous=True, ne sauvegarde que la clé publique précédente
        
        Args:
            private_key : Clé privée PEM
            public_key : Clé publique PEM
            backup_previous : Archiver les clés courantes comme "previous"
        
        Returns:
            True si succès, False sinon
        """
        pass

    @abstractmethod
    def read_key_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les métadonnées de la dernière rotation (date création, intervalle, etc.).
        
        Returns:
            Dict avec 'created_at', 'rotation_interval_days', 'algorithm', ou None
        """
        pass


class EnvBackend(KeyBackend):
    """
    Backend simple : stockage des clés dans .env (développement).
    """

    @staticmethod
    def _get_env_file_path() -> Path:
        """Retourne le chemin du fichier .env (racine du projet)."""
        return Path(__file__).parent.parent.parent.parent / ".env"

    def get_current_keys(self) -> Optional[Dict[str, str]]:
        """Récupère les clés depuis les variables d'environnement."""
        private_key = os.getenv("ED25519_PRIVATE_KEY", "").strip()
        public_key = os.getenv("ED25519_PUBLIC_KEY", "").strip()

        if private_key and public_key:
            return {
                "private_key": private_key,
                "public_key": public_key,
            }
        return None

    def get_previous_keys(self) -> Optional[Dict[str, str]]:
        """Récupère uniquement la clé publique précédente."""
        public_key_prev = os.getenv("ED25519_PUBLIC_KEY_PREVIOUS", "").strip()

        if public_key_prev:
            return {"public_key": public_key_prev}
        return None

    def save_current_keys(
        self,
        private_key: str,
        public_key: str,
        backup_previous: bool = True,
    ) -> bool:
        """Sauvegarde les clés dans .env."""
        try:
            env_file = self._get_env_file_path()

            # Backup des clés courantes comme "previous"
            if backup_previous:
                current_public = os.getenv("ED25519_PUBLIC_KEY", "").strip()
                if current_public:
                    set_key(env_file, "ED25519_PUBLIC_KEY_PREVIOUS", current_public)
                    os.environ["ED25519_PUBLIC_KEY_PREVIOUS"] = current_public
                    logger.info("✅ Clé publique courante sauvegardée comme PREVIOUS")

            # Écrire les nouvelles clés
            set_key(env_file, "ED25519_PRIVATE_KEY", private_key)
            set_key(env_file, "ED25519_PUBLIC_KEY", public_key)

            # Mettre à jour os.environ pour le process courant
            os.environ["ED25519_PRIVATE_KEY"] = private_key
            os.environ["ED25519_PUBLIC_KEY"] = public_key

            logger.info("✅ Clés EdDSA sauvegardées dans .env")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde des clés en .env : {e}")
            return False

    def read_key_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Lis les métadonnées depuis les variables d'environnement.
        
        Si KEY_ROTATION_LAST_ROTATED est défini, calcule le timestamp de dernière rotation.
        """
        try:
            last_rotated_str = os.getenv("KEY_ROTATION_LAST_ROTATED", "")
            interval_days = int(os.getenv("VAULT_KEY_ROTATION_INTERVAL_DAYS", "30"))

            if not last_rotated_str:
                return None

            created_at = datetime.fromisoformat(last_rotated_str.replace('Z', '+00:00'))
            return {
                "created_at": created_at.isoformat(),
                "rotation_interval_days": interval_days,
                "algorithm": "EdDSA",
            }
        except Exception as e:
            logger.warning(f"⚠️  Impossible de lire les métadonnées : {e}")
            return None


class VaultBackend(KeyBackend):
    """
    Backend sécurisé : stockage des clés dans HashiCorp Vault (production).
    """

    def __init__(self):
        """Initialise la connexion Vault."""
        from .vault_manager import get_vault_manager
        self.vault = get_vault_manager()

    def get_current_keys(self) -> Optional[Dict[str, str]]:
        """Charge les clés depuis Vault KV v2."""
        return self.vault.get_current_keys()

    def get_previous_keys(self) -> Optional[Dict[str, str]]:
        """Charge les clés publiques précédentes depuis Vault."""
        return self.vault.get_previous_keys()

    def save_current_keys(
        self,
        private_key: str,
        public_key: str,
        backup_previous: bool = True,
    ) -> bool:
        """Sauvegarde les clés dans Vault avec backup optionnel."""
        return self.vault.save_keys_to_vault(private_key, public_key, backup_previous)

    def read_key_metadata(self) -> Optional[Dict[str, Any]]:
        """Récupère les métadonnées depuis Vault."""
        keys = self.vault.get_current_keys()
        if keys:
            return {
                "created_at": keys.get("created_time"),
                "rotation_interval_days": self.vault.rotation_interval_days,
                "algorithm": "EdDSA",
            }
        return None


class KeyManager:
    """
    Manager centralisé pour la gestion des clés EdDSA.
    
    Délègue au backend configuré (Vault ou Env) via USE_VAULT.
    Gère la rotation automatique et le lock Redis anti-race condition.
    """

    def __init__(self):
        """Initialise le manager et choisit le backend."""
        self.use_vault = os.getenv("USE_VAULT", "false").lower() == "true"
        self.backend: KeyBackend = (
            VaultBackend() if self.use_vault else EnvBackend()
        )

        # Client Redis pour le lock anti-race condition
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Redis client initialisé")
        except Exception as e:
            logger.warning(f"⚠️  Redis non disponible : {e}")
            self.redis_client = None

        logger.info(f"🔑 KeyManager utilise backend : {'Vault' if self.use_vault else 'Env'}")

    def get_current_keys(self) -> Optional[Dict[str, str]]:
        """Récupère les clés EdDSA courantes du backend."""
        return self.backend.get_current_keys()

    def get_previous_keys(self) -> Optional[Dict[str, str]]:
        """
        Récupère uniquement la clé publique précédente.
        
        Utilisée pour valider les tokens émis juste avant une rotation.
        """
        return self.backend.get_previous_keys()

    def should_rotate_keys(self) -> bool:
        """
        Vérifie si une rotation des clés est nécessaire.
        
        Compare : date_création + intervalle vs. maintenant
        """
        try:
            metadata = self.backend.read_key_metadata()
            if not metadata or "created_at" not in metadata:
                logger.info("🔑 Pas de métadonnées. Rotation déclenchée.")
                return True

            created_at_str = metadata["created_at"]
            interval_days = metadata.get("rotation_interval_days", 30)

            try:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                logger.warning(f"⚠️  Timestamp invalide : {created_at_str}. Rotation déclenchée.")
                return True

            # ✅ TIMEZONE FIX: Ensure created_at is timezone-aware before comparison
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            rotation_due_date = created_at + timedelta(days=interval_days)
            is_due = now >= rotation_due_date

            if is_due:
                days_overdue = (now - rotation_due_date).days
                logger.warning(
                    f"🔑 Rotation due ({days_overdue}j de retard). "
                    f"Créées : {created_at.date()}, intervalle : {interval_days}j"
                )
            else:
                days_until = (rotation_due_date - now).days
                logger.info(f"🔑 Prochaine rotation dans {days_until}j ({rotation_due_date.date()})")

            return is_due

        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification de rotation : {e}")
            return False

    def rotate_keys(self) -> bool:
        """
        Effectue la rotation des clés EdDSA.
        
        ⚠️ Acquiert un lock Redis pour éviter les race conditions en multi-instances.
        
        Étapes :
        1. Acquérir le lock Redis (30s timeout)
        2. Générer nouvelle paire EdDSA
        3. Sauvegarder avec backup de la clé publique seule
        4. Réinitialiser le JWTHandler
        5. Libérer le lock (finally)
        
        Returns:
            True si succès, False si échec ou lock non acquis
        """
        lock_key = "key_rotation_lock"
        lock_acquired = False

        try:
            # Essayer d'acquérir le lock Redis
            if self.redis_client:
                lock_acquired = self.redis_client.set(
                    lock_key, "1", nx=True, ex=30
                )
                if not lock_acquired:
                    logger.info(
                        "ℹ️  Rotation déjà en cours ailleurs. "
                        "Skipping cette instance."
                    )
                    return False
            else:
                logger.warning("⚠️  Redis indisponible → pas de lock. Risque de race condition.")

            logger.warning("🔑 Début de rotation des clés EdDSA...")

            # Générer nouvelle paire EdDSA
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()

            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()

            # Sauvegarder avec backup (UNIQUEMENT clé publique précédente)
            if not self.backend.save_current_keys(private_pem, public_pem, backup_previous=True):
                logger.error("❌ Impossible de sauvegarder les nouvelles clés")
                return False

            # Réinitialiser le JWTHandler avec les nouvelles clés
            from .jwt_handler import reset_jwt_handler
            reset_jwt_handler()

            # Forcer le rechargement du .env pour synchroniser os.environ
            from dotenv import load_dotenv
            load_dotenv(override=True)

            # Mettre à jour le timestamp de rotation dans .env
            if isinstance(self.backend, EnvBackend):
                now_iso = datetime.now(timezone.utc).date().isoformat()
                env_file = EnvBackend._get_env_file_path()
                set_key(env_file, "KEY_ROTATION_LAST_ROTATED", now_iso)

            logger.warning(
                "✅ ROTATION COMPLÈTE\n"
                "   • Nouvelle paire EdDSA générée\n"
                "   • Clé publique précédente archivée (validation anciens tokens)\n"
                "   • JWTHandler réinitialisé"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Erreur lors de la rotation : {e}")
            return False

        finally:
            # Libérer le lock Redis
            if lock_acquired and self.redis_client:
                try:
                    self.redis_client.delete(lock_key)
                    logger.debug("🔓 Lock Redis libéré")
                except Exception as e:
                    logger.warning(f"⚠️  Impossible de libérer le lock : {e}")


# Singleton global
_key_manager: Optional[KeyManager] = None


def get_key_manager() -> KeyManager:
    """
    Retourne l'instance singleton du KeyManager (lazy initialization).
    
    Returns:
        Instance partagée du KeyManager
    """
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyManager()
    return _key_manager


def reset_key_manager() -> None:
    """
    Réinitialise le singleton KeyManager.
    
    Utile pour les tests ou après changement de configuration.
    """
    global _key_manager
    _key_manager = None
    logger.info("🔄 KeyManager réinitialisé")


# API publique — fonctions de compatibilité
def check_and_rotate_keys() -> None:
    """
    Vérifie et effectue la rotation des clés si nécessaire.
    
    À appeler régulièrement (via APScheduler ou autre).
    """
    manager = get_key_manager()
    if manager.should_rotate_keys():
        manager.rotate_keys()
    else:
        logger.debug("✅ Clés EdDSA à jour — aucune rotation nécessaire")
