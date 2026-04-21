# ==============================================================================
# app/security/auth/vault_manager.py — HashiCorp Vault OSS Client
# ==============================================================================

import os
import logging
import threading
from typing import Optional, Dict, Any
from datetime import datetime, timezone

import hvac
from hvac.exceptions import VaultError, InvalidPath, Forbidden

logger = logging.getLogger(__name__)

# Chemins dans Vault KV v2
VAULT_MOUNT_POINT = "secret"
KEY_PATH_CURRENT  = "tenderai/jwt-keys/current"
KEY_PATH_PREVIOUS = "tenderai/jwt-keys/previous"


class VaultManager:
    """
    Client HashiCorp Vault OSS pour la gestion des clés EdDSA.

    Authentification :
      Dev  : token simple (VAULT_TOKEN)
      Prod : AppRole (VAULT_ROLE_ID + VAULT_SECRET_ID)

    Usage :
      manager = VaultManager()
      keys = manager.get_current_keys()
    """

    def __init__(self):
        self.vault_addr = os.getenv("VAULT_ADDR", "http://vault:8200")
        self.rotation_interval_days = int(
            os.getenv("VAULT_KEY_ROTATION_INTERVAL_DAYS", "30")
        )
        self.client = self._init_client()

    def _init_client(self) -> hvac.Client:
        """
        Initialise et authentifie le client Vault.
        Priorité : AppRole > Token
        """
        client = hvac.Client(url=self.vault_addr)

        role_id   = os.getenv("VAULT_ROLE_ID", "").strip()
        secret_id = os.getenv("VAULT_SECRET_ID", "").strip()
        token     = os.getenv("VAULT_TOKEN", "").strip()

        try:
            if role_id and secret_id:
               
                response = client.auth.approle.login(
                    role_id=role_id,
                    secret_id=secret_id,
                )
                client.token = response["auth"]["client_token"]
                logger.info("✅ Vault authentifié via AppRole")

            elif token:
                # ⚠️  Développement uniquement — Token authentication
                client.token = token
                logger.warning(
                    "⚠️  Vault authentifié via token root — "
                    "utiliser AppRole en production"
                )

            else:
                raise ValueError(
                    "Vault: aucune méthode d'auth configurée. "
                    "Définir VAULT_ROLE_ID+VAULT_SECRET_ID (prod) "
                    "ou VAULT_TOKEN (dev)."
                )

            if not client.is_authenticated():
                raise VaultError("Vault: authentification échouée")

            logger.info("🔑 Vault client initialisé | addr=%s", self.vault_addr)
            return client

        except Exception as e:
            logger.error("❌ Impossible d'initialiser Vault : %s", e)
            raise

    def _read_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Lit un secret depuis KV v2.
        Retourne les données du secret ou None si inexistant.
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=VAULT_MOUNT_POINT,
            )
            return response.get("data", {}).get("data")
        except InvalidPath:
            logger.debug("Vault: chemin inexistant — %s", path)
            return None
        except Forbidden:
            logger.error("Vault: accès refusé — %s (vérifier les policies)", path)
            return None
        except Exception as e:
            logger.error("Vault: erreur lecture %s — %s", path, e)
            return None

    def _write_secret(self, path: str, data: Dict[str, str]) -> bool:
        """
        Écrit un secret dans KV v2.
        Retourne True si succès, False sinon.
        """
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point=VAULT_MOUNT_POINT,
            )
            logger.info("✅ Vault: secret écrit — %s", path)
            return True
        except Forbidden:
            logger.error(
                "Vault: accès refusé en écriture — %s "
                "(vérifier les policies AppRole)", path
            )
            return False
        except Exception as e:
            logger.error("Vault: erreur écriture %s — %s", path, e)
            return False

    def get_current_keys(self) -> Optional[Dict[str, str]]:
        """
        Récupère la paire de clés EdDSA courante.

        Returns:
            Dict avec 'private_key' et 'public_key' (PEM), ou None
        """
        data = self._read_secret(KEY_PATH_CURRENT)
        if not data:
            return None

        private_key = data.get("private_key", "").strip()
        public_key  = data.get("public_key", "").strip()

        if not private_key or not public_key:
            logger.warning("Vault: clés courantes incomplètes")
            return None

        return {
            "private_key":  private_key,
            "public_key":   public_key,
            "created_time": data.get("created_time"),
        }

    def get_previous_keys(self) -> Optional[Dict[str, str]]:
        """
        Récupère uniquement la clé publique précédente.
        Utilisée pour valider les tokens émis avant la dernière rotation.

        ⚠️  Retourne UNIQUEMENT public_key — jamais la clé privée précédente.

        Returns:
            Dict avec 'public_key' (PEM), ou None
        """
        data = self._read_secret(KEY_PATH_PREVIOUS)
        if not data:
            return None

        public_key = data.get("public_key", "").strip()
        if not public_key:
            return None

        return {"public_key": public_key}

    def save_keys_to_vault(
        self,
        private_key: str,
        public_key: str,
        backup_previous: bool = True,
    ) -> bool:
        """
        Sauvegarde la nouvelle paire de clés EdDSA dans Vault.

        Si backup_previous=True :
          1. Lire la clé publique courante
          2. La sauvegarder dans KEY_PATH_PREVIOUS (public_key uniquement)
          3. Écrire la nouvelle paire dans KEY_PATH_CURRENT

        ⚠️  Ne sauvegarde JAMAIS la clé privée précédente.

        Args:
            private_key     : Nouvelle clé privée EdDSA (PEM)
            public_key      : Nouvelle clé publique EdDSA (PEM)
            backup_previous : Archiver la clé publique courante comme "previous"

        Returns:
            True si succès complet, False si une étape échoue
        """
        if backup_previous:
            current = self.get_current_keys()
            if current and current.get("public_key"):
                backup_ok = self._write_secret(
                    KEY_PATH_PREVIOUS,
                    {
                        "public_key":  current["public_key"],
                        "archived_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                if backup_ok:
                    logger.info(
                        "✅ Vault: clé publique précédente archivée "
                        "dans %s", KEY_PATH_PREVIOUS
                    )
                else:
                    logger.warning(
                        "⚠️  Vault: échec archivage clé précédente — "
                        "rotation continue quand même"
                    )

        success = self._write_secret(
            KEY_PATH_CURRENT,
            {
                "private_key":  private_key,
                "public_key":   public_key,
                "created_time": datetime.now(timezone.utc).isoformat(),
            }
        )

        if success:
            logger.info(
                "✅ Vault: nouvelle paire EdDSA sauvegardée | "
                "path=%s", KEY_PATH_CURRENT
            )

        return success

   
    def read_scheduler_secret(self) -> Optional[str]:
        """
        Lit SCHEDULER_SECRET depuis Vault.
        
        Chemin: secret/tenderai/scheduler → scheduler_secret
        
        Returns:
            String du secret, ou None si inexistant
        """
        try:
            secret_data = self._read_secret("tenderai/scheduler")
            if secret_data:
                return secret_data.get("scheduler_secret")
            logger.debug("Vault: SCHEDULER_SECRET ne existe pas (OK en dev)")
            return None
        except Exception as e:
            logger.error(f"Vault: erreur lecture SCHEDULER_SECRET : {e}")
            return None




_vault_manager: Optional[VaultManager] = None
_lock = threading.Lock()


def get_vault_manager() -> VaultManager:
    """
    Retourne l'instance singleton du VaultManager (thread-safe).
    Appelé par VaultBackend.__init__() dans key_manager.py.

    ⚠️  En cas d'expiration du token AppRole (TTL 1h), appeler
        reset_vault_manager() puis get_vault_manager() pour se
        ré-authentifier sans redémarrer l'application.
    """
    global _vault_manager
    if _vault_manager is None:
        with _lock:
            if _vault_manager is None:  # double-check après acquisition du lock
                _vault_manager = VaultManager()
    return _vault_manager


def reset_vault_manager() -> None:
    """
    Réinitialise le singleton (thread-safe).
    Cas d'usage :
      - Token AppRole expiré (TTL 1h atteint)
      - Après rotation de secret_id en prod
      - En tests unitaires (isolation)
    """
    global _vault_manager
    with _lock:
        _vault_manager = None
    logger.info("🔄 VaultManager réinitialisé")