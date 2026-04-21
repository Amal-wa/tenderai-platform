# ==============================================================================
# app/security/auth/jwt_handler.py — Gestionnaire JWT multi-algorithmes
# ==============================================================================
import os
import logging
import secrets 
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum
from uuid import uuid4

import jwt
from jwt.exceptions import InvalidTokenError as JWTError
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import (
    load_pem_public_key,
    load_pem_private_key,
)
from dotenv import set_key

logger = logging.getLogger(__name__)


class JWTAlgorithm(str, Enum):
    """
    Enum des algorithmes JWT supportés.
    Hérite de str pour pouvoir faire JWTAlgorithm.EdDSA == "EdDSA" directement.
    """
    EdDSA = "EdDSA"  # ED25519 — recommandé
    RS256 = "RS256"  # RSA asymétrique
    HS256 = "HS256"  # HMAC symétrique


class JWTHandler:
    """
    Gestionnaire centralisé des JWT.

    À l'initialisation, il lit JWT_ALGORITHM dans .env pour savoir quel
    algorithme utiliser, puis charge les clés correspondantes.

    Tous les tokens (access + refresh) passent par cette classe.
    """

    def __init__(self):
        """
        Initialise le handler : lit l'algorithme et charge les clés.
        Les clés sont stockées dans des attributs d'instance pour être
        réutilisées à chaque création/vérification de token.
        """
        self.algorithm_str = os.getenv("JWT_ALGORITHM", "EdDSA").strip()

        try:
            self.algorithm = JWTAlgorithm(self.algorithm_str)
        except ValueError:
            # Si la valeur dans .env est invalide, on replie sur EdDSA
            logger.warning(
                f"JWT_ALGORITHM invalide : '{self.algorithm_str}'. Utilisation de EdDSA par défaut."
            )
            self.algorithm = JWTAlgorithm.EdDSA

        self.signing_key: Any = None
        self.verification_key: Any = None
        self.verification_key_previous: Optional[str] = None

        logger.info(f"🔐 Initialisation JWT avec l'algorithme : {self.algorithm.value}")

        # Charge les clés selon l'algorithme choisi
        if self.algorithm == JWTAlgorithm.EdDSA:
            self._load_eddsa_keys()
        elif self.algorithm == JWTAlgorithm.RS256:
            self._load_rsa_keys()
        elif self.algorithm == JWTAlgorithm.HS256:
            self._load_hmac_secret()

    # ──────────────────────────────────────────────────────────────────────────
    # Chargement des clés EdDSA
    # ──────────────────────────────────────────────────────────────────────────

    def _get_keys_directory(self) -> Path:
        """
        Get the directory where EdDSA keys are stored.
        
        Priority:
        1. ED25519_KEY_PATH environment variable
        2. Falls back to /app/keys (Docker)
        3. Falls back to .keys in current directory (local dev)
        
        Returns:
            Path to the keys directory
        """
        key_path_env = os.getenv("ED25519_KEY_PATH")
        if key_path_env:
            return Path(key_path_env)
        
        # Check if we're in Docker
        if Path("/app").exists():
            return Path("/app/keys")
        
        # Local development
        return Path.cwd() / ".keys"

    def _load_eddsa_keys(self) -> None:
        """
        Loads EdDSA keys from disk (PEM format) or generates new ones if missing.
        
        Keys are stored in:
        - /app/keys/ed25519_private.pem (mode 600)
        - /app/keys/ed25519_public.pem (mode 644)
        
        Falls back to environment variables for backwards compatibility.
        """
        keys_dir = self._get_keys_directory()
        private_key_path = keys_dir / "ed25519_private.pem"
        public_key_path = keys_dir / "ed25519_public.pem"
        previous_key_path = keys_dir / "ed25519_public_previous.pem"
        
        # Try to load from disk first
        if private_key_path.exists() and public_key_path.exists():
            try:
                with open(private_key_path, "r") as f:
                    private_pem = f.read().strip()
                with open(public_key_path, "r") as f:
                    public_pem = f.read().strip()
                
                self.signing_key = load_pem_private_key(private_pem.encode(), password=None)
                self.verification_key = load_pem_public_key(public_pem.encode())
                
                # Load previous key if it exists (for rotation)
                if previous_key_path.exists():
                    try:
                        with open(previous_key_path, "r") as f:
                            prev_pem = f.read().strip()
                        self.verification_key_previous = load_pem_public_key(prev_pem.encode())
                    except Exception as e:
                        logger.warning(f"⚠️  Could not load previous key: {e}")
                        self.verification_key_previous = None
                else:
                    self.verification_key_previous = None
                
                logger.info(f"🔑 EdDSA keys loaded from disk: {private_key_path}")
                return
            except Exception as e:
                logger.warning(f"⚠️  Failed to load keys from disk: {e}")
        
        # Fallback: try to load from environment variables (backwards compatibility)
        private_key_pem = os.getenv("ED25519_PRIVATE_KEY", "").strip()
        public_key_pem = os.getenv("ED25519_PUBLIC_KEY", "").strip()
        
        if private_key_pem and public_key_pem:
            try:
                self.signing_key = load_pem_private_key(private_key_pem.encode(), password=None)
                self.verification_key = load_pem_public_key(public_key_pem.encode())
                
                prev = os.getenv("ED25519_PUBLIC_KEY_PREVIOUS", "").strip()
                self.verification_key_previous = (
                    load_pem_public_key(prev.encode()) if prev else None
                )
                
                logger.info("🔑 EdDSA keys loaded from environment (legacy)")
                # Save to disk for future use
                self._save_eddsa_keys_to_disk()
                return
            except Exception as e:
                logger.warning(f"⚠️  Failed to load keys from environment: {e}")
        
        # No keys found — generate new ones
        logger.warning("⚠️  EdDSA keys not found. Generating new pair...")
        self._generate_and_save_eddsa_keys()

    def _save_eddsa_keys_to_disk(self) -> None:
        """
        Save current EdDSA keys to disk in PEM format.
        
        Sets file permissions:
        - 600 (rw-------) for private key
        - 644 (rw-r--r--) for public key
        """
        keys_dir = self._get_keys_directory()
        keys_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.signing_key or not self.verification_key:
            raise RuntimeError("No EdDSA keys to save")
        
        private_pem = self.signing_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        
        public_pem = self.verification_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
        private_key_path = keys_dir / "ed25519_private.pem"
        public_key_path = keys_dir / "ed25519_public.pem"
        
        # Write private key with secure permissions (600)
        with open(private_key_path, "w") as f:
            f.write(private_pem)
        os.chmod(private_key_path, stat.S_IRUSR | stat.S_IWUSR)  # 600
        
        # Write public key with standard permissions (644)
        with open(public_key_path, "w") as f:
            f.write(public_pem)
        os.chmod(public_key_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 644
        
        logger.info(f"💾 EdDSA keys saved to disk: {private_key_path}")

    def _generate_and_save_eddsa_keys(self) -> None:
        """
        Génère une nouvelle paire de clés EdDSA et la sauvegarde sur le disque (PEM format).
        L'ancienne paire (si elle existe) est sauvegardée dans un fichier PREVIOUS
        pour assurer la continuité de validation pendant la transition.
        """
        keys_dir = self._get_keys_directory()
        keys_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if directory is writable
        if not os.access(keys_dir, os.W_OK):
            raise RuntimeError(
                f"EdDSA keys directory {keys_dir} is not writable. "
                "Check permissions and ensure the volume is mounted correctly."
            )
        
        # Sauvegarde des clés actuelles avant écrasement
        private_key_path = keys_dir / "ed25519_private.pem"
        public_key_path = keys_dir / "ed25519_public.pem"
        previous_key_path = keys_dir / "ed25519_public_previous.pem"
        
        # Save current keys as PREVIOUS if they exist
        if private_key_path.exists() and public_key_path.exists() and self.verification_key:
            try:
                old_public_pem = self.verification_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode()
                with open(previous_key_path, "w") as f:
                    f.write(old_public_pem)
                os.chmod(previous_key_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 644
                logger.info(f"💾 Previous key backed up: {previous_key_path}")
            except Exception as e:
                logger.warning(f"⚠️  Could not back up previous key: {e}")

        # Génération de la nouvelle paire
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

        # Écriture des nouvelles clés sur le disque
        with open(private_key_path, "w") as f:
            f.write(private_pem)
        os.chmod(private_key_path, stat.S_IRUSR | stat.S_IWUSR)  # 600 (rw-------)
        
        with open(public_key_path, "w") as f:
            f.write(public_pem)
        os.chmod(public_key_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 644 (rw-r--r--)

        # Store actual key objects
        self.signing_key = private_key
        self.verification_key = public_key
        
        # Load previous key if it was backed up
        if previous_key_path.exists():
            try:
                with open(previous_key_path, "r") as f:
                    prev_pem = f.read().strip()
                self.verification_key_previous = load_pem_public_key(prev_pem.encode())
            except Exception as e:
                logger.warning(f"⚠️  Could not load previous key: {e}")
                self.verification_key_previous = None
        else:
            self.verification_key_previous = None

        logger.info(f"✅ New EdDSA keys generated and saved to: {private_key_path}")


    # ──────────────────────────────────────────────────────────────────────────
    # Chargement des clés RSA
    # ──────────────────────────────────────────────────────────────────────────

    def _load_rsa_keys(self) -> None:
        """
        Charge les clés RSA depuis les variables d'environnement.
        Les clés doivent être au format PEM (PKCS#1 ou PKCS#8).
        """
        private_key_pem = os.getenv("RSA_PRIVATE_KEY")
        public_key_pem = os.getenv("RSA_PUBLIC_KEY")

        if not private_key_pem or not public_key_pem:
            logger.warning("⚠️  Clés RSA absentes. Génération d'une paire RSA 2048 bits...")
            self._generate_and_save_rsa_keys()
            return

        
        try:
            self.signing_key = load_pem_private_key(private_key_pem.encode(), password=None)
            self.verification_key = load_pem_public_key(public_key_pem.encode())
        except Exception as e:
            logger.error(f"Erreur lors du chargement des clés RSA : {e}")
            raise
        
        # Ancienne clé publique (optionnelle) — utilisée pendant la rotation
        previous_key_pem = os.getenv("RSA_PUBLIC_KEY_PREVIOUS")
        if previous_key_pem:
            try:
                self.verification_key_previous = load_pem_public_key(previous_key_pem.encode())
            except Exception as e:
                logger.warning(f"Avertissement : impossible de charger la clé RSA PREVIOUS : {e}")
                self.verification_key_previous = None
        else:
            self.verification_key_previous = None

        logger.info("✅ Clés RSA chargées avec succès")

    def _generate_and_save_rsa_keys(self) -> None:
        """
        Génère une nouvelle paire RSA 2048 bits et la sauvegarde dans .env.
        """
        current_private = os.getenv("RSA_PRIVATE_KEY")
        current_public = os.getenv("RSA_PUBLIC_KEY")

        # RSA 2048 bits — minimum recommandé pour la sécurité
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
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

        env_file = self._get_env_file_path()

        if current_public:
            set_key(env_file, "RSA_PUBLIC_KEY_PREVIOUS", current_public)
        if current_private:
            set_key(env_file, "RSA_PRIVATE_KEY_PREVIOUS", current_private)

        set_key(env_file, "RSA_PRIVATE_KEY", private_pem)
        set_key(env_file, "RSA_PUBLIC_KEY", public_pem)

        os.environ["RSA_PRIVATE_KEY"] = private_pem
        os.environ["RSA_PUBLIC_KEY"] = public_pem
        os.environ["RSA_PUBLIC_KEY_PREVIOUS"] = current_public or ""

       
        self.signing_key = private_key  # Using the generated key object
        self.verification_key = public_key  # Using the generated key object
        if current_public:
            try:
                self.verification_key_previous = load_pem_public_key(current_public.encode())
            except Exception as e:
                logger.warning(f"Avertissement : impossible de charger la clé RSA PREVIOUS : {e}")
                self.verification_key_previous = None
        else:
            self.verification_key_previous = None

        logger.info("✅ Nouvelles clés RSA générées et sauvegardées dans .env")

    # ──────────────────────────────────────────────────────────────────────────
    # Chargement du secret HMAC (HS256)
    # ──────────────────────────────────────────────────────────────────────────

    def _load_hmac_secret(self) -> None:
        """
        Charge le secret HMAC depuis l'environnement pour HS256.
        Le secret doit faire au minimum 32 caractères.

        ⚠️  AVERTISSEMENT : HS256 avec un secret partagé n'est adapté que
        pour les déploiements mono-serveur. En multi-serveurs, préférez EdDSA.
        """
        secret = os.getenv("JWT_SECRET_KEY")

        if not secret or len(secret) < 32:
            logger.warning(
                "⚠️  JWT_SECRET_KEY absent ou trop court (min 32 cars). Génération automatique..."
            )
            self._generate_and_save_hmac_secret()
            return

        # Pour HS256 : même valeur pour signer et vérifier (clé symétrique)
        self.signing_key = secret
        self.verification_key = secret
        self.verification_key_previous = None  # Pas de rotation pour HS256

        logger.info("✅ Secret HMAC chargé avec succès")

    def _generate_and_save_hmac_secret(self) -> None:
        """
        Génère un secret HMAC sécurisé de 64 caractères et le sauvegarde dans .env.

        ✅ Utilise `secrets.token_urlsafe` — cryptographiquement sûr.
        ❌ N'utilise PAS `random` qui n'est PAS sécurisé pour la cryptographie.
        """
        # secrets.token_urlsafe(48) génère ~64 caractères base64 aléatoires
        secret = secrets.token_urlsafe(48)

        env_file = self._get_env_file_path()
        set_key(env_file, "JWT_SECRET_KEY", secret)
        os.environ["JWT_SECRET_KEY"] = secret

        self.signing_key = secret
        self.verification_key = secret
        self.verification_key_previous = None

        logger.warning(
            f"💾 Nouveau secret HMAC écrit dans {env_file}. "
            "Sauvegardez-le dans un endroit sécurisé !"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Utilitaires
    # ──────────────────────────────────────────────────────────────────────────

    def _get_env_file_path(self) -> Path:
        """
        Retourne le chemin vers le fichier .env à la racine du projet.

        Structure supposée :
            project_root/
            ├── .env                   ← ici
            └── app/
                └── security/
                    └── auth/
                        └── jwt_handler.py  ← ce fichier (4 niveaux au-dessus)

        Returns:
            Path vers le fichier .env
        """
        # __file__ = chemin de ce fichier python
        # .parent x4 = remonte jusqu'à la racine du projet
        return Path("/app/.env")

    # ──────────────────────────────────────────────────────────────────────────
    # Création et vérification des tokens
    # ──────────────────────────────────────────────────────────────────────────

    def create_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
        token_type: str = "access"
    ) -> str:
        """
        Crée et signe un token JWT.

        Un token JWT contient des "claims" (informations) :
        - sub    : identifiant de l'utilisateur
        - exp    : date d'expiration (Unix timestamp)
        - iat    : date d'émission
        - jti    : identifiant unique du token (pour la révocation)
        - type   : "access", "refresh", "partial", ou "email_verification"

        Args:
            data         : Claims personnalisés (ex: {"sub": "user_id"})
            expires_delta: Durée de validité personnalisée
            token_type   : "access" (15min), "refresh" (7j), "partial" (2FA), "email_verification" (24h)

        Returns:
            Token JWT signé en format string

        Raises:
            ValueError   : Si token_type est invalide
            RuntimeError : Si la signature échoue
        """
        if token_type not in ("access", "refresh", "partial", "email_verification"):
            raise ValueError(f"token_type invalide : '{token_type}'. Valeurs acceptées : 'access', 'refresh', 'partial', 'email_verification'")

        # Copie des données sans 'type' pour éviter les conflits avec notre claim
        payload = {k: v for k, v in data.items() if k != "type"}

        now = datetime.now(timezone.utc)

        # Durées par défaut : 15 min pour access, 30 jours pour refresh
        if expires_delta:
            expiry = now + expires_delta
        elif token_type == "access":
            expiry = now + timedelta(minutes=15)
        else:
            expiry = now + timedelta(days=30)

        # Ajout des claims standards
        payload.update({
            "exp": int(expiry.timestamp()),   # Expiration (vérifié automatiquement par jose)
            "iat": int(now.timestamp()),       # Issued At
            "jti": str(uuid4()),               # JWT ID unique (utile pour la révocation)
            "type": token_type,
        })

        try:
            logger.info(f"[KEY DEBUG] Creating {token_type} token with algorithm={self.algorithm.value}")
            token = jwt.encode(payload, self.signing_key, algorithm=self.algorithm.value)
            
            
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            
            logger.info(f"[KEY DEBUG] Token created successfully (type: {type(token).__name__})")
            return token
        except Exception as e:
            logger.error(f"[KEY DEBUG] Token creation failed: {e}")
            raise RuntimeError(f"Échec de création du JWT : {e}")

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Vérifie la signature d'un JWT et retourne son contenu décodé.

        Logique de fallback pour la rotation de clés :
        1. Essaie avec la clé ACTUELLE
        2. Si échec et qu'une clé PRÉCÉDENTE (disque) existe → essaie avec l'ancienne
        3. Si échec aussi, charge les clés précédentes depuis Vault et essaie
        4. Si les trois échouent → lève JWTError

        Args:
            token : Chaîne JWT à vérifier (accepte str ou bytes)

        Returns:
            Payload décodé (dict)

        Raises:
            JWTError : Si le token est invalide, expiré ou tampered
        """
        
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        try:
            # Tentative 1 : clé courante
            logger.info(f"[KEY DEBUG] Attempting verification with CURRENT key (algorithm={self.algorithm.value})")
            result = jwt.decode(token, self.verification_key, algorithms=[self.algorithm.value], options={"verify_exp": True})
            logger.info(f"[KEY DEBUG] ✅ Token verified with CURRENT key")
            return result
        except JWTError as e:
            logger.warning(f"[KEY DEBUG] Current key verification failed: {str(e)[:100]}")
            # Tentative 2 : clé précédente depuis disque
            if self.verification_key_previous:
                try:
                    logger.warning("[KEY DEBUG] Attempting verification with PREVIOUS key from disk...")
                    payload = jwt.decode(
                        token,
                        self.verification_key_previous,
                        algorithms=[self.algorithm.value],
                        options={"verify_exp": True}
                    )
                    logger.warning("[KEY DEBUG] ✅ Token verified with PREVIOUS key from disk")
                    return payload
                except JWTError as disk_err:
                    logger.warning(f"[KEY DEBUG] Previous key (disk) verification failed: {str(disk_err)[:100]}")
                    pass  # Clé de disque a échoué aussi → essayer Vault
            
            # Tentative 3 : clés précédentes depuis le backend (Vault ou .env)
            try:
                from .key_manager import get_key_manager
                
                manager = get_key_manager()
                previous_keys = manager.get_previous_keys()
                if previous_keys and previous_keys.get("public_key"):
                    try:
                        prev_public_pem = previous_keys["public_key"]
                        prev_public_key = load_pem_public_key(prev_public_pem.encode())
                        
                        logger.warning("[KEY DEBUG] Attempting verification with PREVIOUS key from backend (Vault/Env)...")
                        payload = jwt.decode(
                            token,
                            prev_public_key,
                            algorithms=[self.algorithm.value],
                            options={"verify_exp": True}
                        )
                        logger.warning("[KEY DEBUG] ✅ Token verified with PREVIOUS key from backend")
                        return payload
                    except (JWTError, Exception) as backend_verify_err:
                        logger.warning(f"[KEY DEBUG] Backend previous key verification failed: {str(backend_verify_err)[:100]}")
                        pass  # Clé backend a échoué aussi
            except Exception as backend_err:
                logger.debug(f"[KEY DEBUG] Could not load previous keys from backend: {backend_err}")

            # Toutes les tentatives ont échoué → lever l'erreur
            logger.error(f"[KEY DEBUG] ALL VERIFICATION ATTEMPTS FAILED: {str(e)[:100]}")
            raise JWTError(f"Vérification JWT échouée : {e}")

    def algorithm_value(self) -> str:
        """Retourne le nom de l'algorithme tel qu'attendu par la librairie jose."""
        return self.algorithm.value


# ── Singleton global du JWT Handler ──────────────────────────────────────────
#
# On utilise un singleton pour éviter de recharger les clés depuis .env
# à chaque requête. Le handler est initialisé une seule fois au démarrage.
#

_jwt_handler: Optional[JWTHandler] = None


def get_jwt_handler() -> JWTHandler:
    """
    Retourne l'instance globale du JWTHandler (lazy initialization).

    "Lazy" signifie qu'il n'est créé qu'au premier appel, pas au démarrage.
    Cela garantit que les variables d'environnement sont bien chargées avant.

    Returns:
        Instance partagée du JWTHandler
    """
    global _jwt_handler
    if _jwt_handler is None:
        _jwt_handler = JWTHandler()
    return _jwt_handler


def reset_jwt_handler() -> None:
    """
    Réinitialise le singleton du JWTHandler.

    ✅ À appeler OBLIGATOIREMENT après une rotation de clés pour que
    le handler en mémoire recharge les nouvelles clés depuis .env.

    Sans cet appel, le handler continuerait à signer avec les ANCIENNES clés
    même si .env a été mis à jour.
    """
    global _jwt_handler
    _jwt_handler = None
    logger.info("🔄 JWTHandler réinitialisé — sera rechargé au prochain appel")


# ── API publique (compatibilité rétrograde) ───────────────────────────────────
#
# Ces fonctions standalone permettent d'appeler le handler sans l'instancier
# directement. Les fichiers existants (auth.py, routes, etc.) peuvent continuer
# à utiliser ces fonctions sans modification.


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Crée un token d'accès (courte durée — 15 min par défaut).

    C'est le token envoyé dans le header Authorization: Bearer <token>
    à chaque requête API protégée.

    Args:
        data         : Claims (ex: {"sub": "user_id", "tenant_id": "abc"})
        expires_delta: Durée personnalisée

    Returns:
        JWT signé
    """
    return get_jwt_handler().create_token(data, expires_delta, token_type="access")


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Crée un token de rafraîchissement (longue durée — 7 jours par défaut).

    Ce token est utilisé pour obtenir un nouvel access token sans se reconnecter.
    Il doit être stocké côté client de manière sécurisée (httpOnly cookie recommandé).

    Args:
        data         : Claims
        expires_delta: Durée personnalisée

    Returns:
        JWT signé
    """
    return get_jwt_handler().create_token(data, expires_delta, token_type="refresh")


def create_partial_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Crée un token partiel pour l'authentification 2FA (courte durée — 5 min par défaut).

    Ce token est retourné au client quand 2FA est activée.
    Le client l'utilise pour appeler /api/v1/auth/2fa/login avec le code TOTP.
    Durée courte (5 min) réduit la fenêtre d'attaque si le token est intercepté.

    Args:
        data         : Claims (sub, tenant_id, email)
        expires_delta: Durée personnalisée (défaut: 5 min)

    Returns:
        JWT signé (type="partial")
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=5)
    return get_jwt_handler().create_token(data, expires_delta, token_type="partial")


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Vérifie un token JWT et retourne son contenu.

    Args:
        token : Token JWT à vérifier

    Returns:
        Payload décodé

    Raises:
        JWTError : Si le token est invalide ou expiré
    """
    return get_jwt_handler().verify_token(token)