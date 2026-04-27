# ==============================================================================
# AUTH.PY — Authentification & Sécurité
# ==============================================================================


import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import Depends, HTTPException, status,Request
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError as JWTError
from sqlalchemy.orm import Session
from sqlalchemy import and_
from argon2 import PasswordHasher, Type          # type: ignore
from argon2.exceptions import VerifyMismatchError, InvalidHash  # type: ignore

from .database import get_db, set_tenant_context
from .models import User, AuthSession
from .security.auth.jwt_handler import get_jwt_handler

# Logger configuration
import logging
logger = logging.getLogger(__name__)


ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS   = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS",   "7"))
MAX_SESSIONS                = int(os.getenv("MAX_SESSIONS", "5"))

# Algorithme de signature : EdDSA (asymétrique, sécurisé)
# - PRIVÉ  : utilisé pour SIGNER les tokens → gardé secret sur le serveur
# - PUBLIC : utilisé pour VÉRIFIER les tokens → peut être public
ALGORITHM = "EdDSA"

def _load_or_generate_keys() -> tuple[str, str]:
    """
    Charge les clés EdDSA depuis .env ou les génère si manquantes.
    
    EdDSA (ED25519) est un algorithme asymétrique :
    - Clé privée signe les tokens (seul le serveur la connaît)
    - Clé publique vérifie les signatures (peut être distribuée)
    
    Si les clés manquent dans .env :
    - Génère une nouvelle paire
    - Écrit dans .env (safely avec set_key)
    - Charge dans os.environ pour utilisation immédiate
    - Continue sans redémarrage
    
    Retourne : (private_key_pem, public_key_pem)
    """
    private_key_env = os.getenv("ED25519_PRIVATE_KEY")
    public_key_env = os.getenv("ED25519_PUBLIC_KEY")
    
    if private_key_env and public_key_env:
       
        private_key_env = private_key_env.replace("\\n", "\n")
        public_key_env = public_key_env.replace("\\n", "\n")
        
       
        if "BEGIN" not in private_key_env and private_key_env:
            private_key_env = f"-----BEGIN PRIVATE KEY-----\n{private_key_env}\n-----END PRIVATE KEY-----"
        
        if "BEGIN" not in public_key_env and public_key_env:
            public_key_env = f"-----BEGIN PUBLIC KEY-----\n{public_key_env}\n-----END PUBLIC KEY-----"
        
        return private_key_env, public_key_env
    
    # ⚠️ Les clés manquent → générer une nouvelle paire
    from pathlib import Path
    from dotenv import set_key
    
    logger.warning(
        "⚠️  EdDSA keys not found in .env! Generating new key pair..."
    )
    
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    
    # Générer la paire de clés
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
    
    # Trouver le fichier .env (au répertoire racine du projet, même que alembic.ini)
    # On remonte depuis app/ → services/api-gateway/
    app_dir = Path(__file__).parent
    project_root = app_dir.parent.parent
    env_file = project_root / ".env"
    
    logger.warning(f"💾 Writing keys to {env_file}")
    
    # Écrire les clés dans .env avec set_key (safely, preserve other entries)
    set_key(env_file, "ED25519_PRIVATE_KEY", private_pem)
    set_key(env_file, "ED25519_PUBLIC_KEY", public_pem)
    
    # Charger dans os.environ pour utilisation immédiate (pas de redémarrage nécessaire)
    os.environ["ED25519_PRIVATE_KEY"] = private_pem
    os.environ["ED25519_PUBLIC_KEY"] = public_pem
    
    logger.info(f"✅ EdDSA keys written to {env_file}")
    logger.info("✅ Keys loaded into environment - application can continue without restart")
    
    return private_pem, public_pem


# Charger les clés EdDSA
ED25519_PRIVATE_KEY, ED25519_PUBLIC_KEY = _load_or_generate_keys()

# oauth2_scheme : dit à FastAPI comment extraire le token des requêtes.
# Il cherche automatiquement le header : Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    description="JWT Bearer token",
    auto_error=False
)


# ==============================================================================
#  PARTIE 1 : GESTION DES MOTS DE PASSE (Argon2id)
# ==============================================================================


class SecurePasswordManager:
    """Gestionnaire de mots de passe sécurisé avec Argon2id."""

    def __init__(self):
        # Paramètres recommandés par la RFC 9106
        self.hasher = PasswordHasher(
            time_cost=2,       # 2 itérations de calcul (~0.5s sur CPU moderne)
            memory_cost=65536, # 64 MB de RAM requis → résiste aux attaques GPU
            parallelism=4,     # 4 threads parallèles
            hash_len=32,       # Taille du hash : 256 bits
            salt_len=16,       # Taille du salt : 128 bits aléatoires
            type=Type.ID,      # Argon2id = mode hybride (le plus sécurisé)
        )

    def hash_password(self, password: str) -> str:
        """
        Transforme un mot de passe en clair en hash sécurisé.

        Exemple :
            hash_password("monmotdepasse")
            → "$argon2id$v=19$m=65536,t=2,p=4$c2FsdHJhbmRvbQ$aGFzaGVk..."

        Ce hash contient :
        - L'algorithme utilisé (argon2id)
        - Les paramètres (m=65536, t=2, p=4)
        - Le salt (aléatoire, différent à chaque appel)
        - Le hash résultant
        """
        if not password:
            raise ValueError("Le mot de passe ne peut pas être vide")
        return self.hasher.hash(password)

    def verify_password(self, hashed_password: str, plain_password: str) -> bool:
        """
        Vérifie si un mot de passe correspond à son hash.

        Important : comparison en temps constant
        → prend le même temps que le mot de passe soit bon ou mauvais.
        Cela empêche les attaques "timing" où un attaquant mesure le temps
        de réponse pour deviner des caractères.

        Retourne True si correct, False sinon.
        Ne lève JAMAIS d'exception (fail-safe).
        """
        try:
            self.hasher.verify(hashed_password, plain_password)
            return True
        except (VerifyMismatchError, InvalidHash):
            return False  # Mot de passe incorrect ou hash corrompu

    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Vérifie si le hash doit être recalculé.
        Utile quand on augmente les paramètres de sécurité :
        les anciens hashs sont recalculés au prochain login.
        """
        try:
            return self.hasher.check_needs_rehash(hashed_password)
        except Exception:
            return True  # En cas de doute, on recalcule


# Instance unique réutilisée partout dans l'application
_password_manager = SecurePasswordManager()


def get_password_hash(password: str) -> str:
    """
    Fonction publique pour hasher un mot de passe.

    ✅ À appeler lors de l'inscription ou du changement de mot de passe.
    ❌ Ne JAMAIS stocker le mot de passe en clair en base de données.

    Exemple d'usage :
        user.hashed_password = get_password_hash(request.password)
        db.add(user)
        db.commit()
    """
    return _password_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Fonction publique pour vérifier un mot de passe.

    ✅ À appeler lors du login.
    Note : l'ordre des paramètres est (plain, hashed) — attention à ne pas inverser.

    Exemple d'usage :
        if not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(401, "Mot de passe incorrect")
    """
    return _password_manager.verify_password(hashed_password, plain_password)


def password_needs_rehash(hashed_password: str) -> bool:
    """
    Vérifie si un hash de mot de passe doit être recalculé.

    ✅ À appeler après une vérification réussie du mot de passe au login.
    Utile quand on augmente les paramètres de sécurité Argon2id.

    Si True : le mot de passe doit être rehashé avec les nouveaux paramètres.
    → Cela se fait transparemment au prochain login de l'utilisateur.

    Exemple d'usage :
        if verify_password(credentials.password, user.hashed_password):
            if password_needs_rehash(user.hashed_password):
                user.hashed_password = get_password_hash(credentials.password)
                db.commit()
    """
    return _password_manager.needs_rehash(hashed_password)


# ==============================================================================
#  PARTIE 2 : GESTION DES JWT
# ==============================================================================

def verify_token(token: str) -> Dict[str, Any]:
    """
    Vérifie un JWT et retourne son contenu (payload).

    Délègue à l'implémentation centralisée dans jwt_handler qui gère
    correctement les clés EdDSA (et autres algorithmes) en les chargeant
    comme des objets cryptographiques plutôt que des strings.

    Returns:
        dict : Payload décodé du token (contient sub, tenant_id, type, exp, iat, jti)

    Raises:
        JWTError : Si le token est invalide, expiré ou tampered
    """
    try:
        return get_jwt_handler().verify_token(token)
    except Exception as e:
        raise JWTError(f"JWT invalide : {e}")


# ==============================================================================
#  PARTIE 2b : GESTION DES SESSIONS EN BASE DE DONNÉES
# ==============================================================================

def create_auth_session(
    db: Session,
    user_id: UUID,
    tenant_id: UUID,
    jti: str,
    token_type: str = "access",
    expires_delta: Optional[timedelta] = None,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuthSession:
    """
    Enregistre une nouvelle session en base de données.

    Appelé à chaque login pour tracker les appareils connectés.
    Permet le logout sélectif (révoquer un appareil sans affecter les autres).

    Paramètres :
        jti       : L'identifiant unique du JWT (contenu dans le token)
        user_agent: Le navigateur/app qui se connecte (ex: "Chrome/120")
        ip_address: L'adresse IP du client
        token_type: "access" (15 min), "refresh" (7 jours), ou "partial" (2FA)
        expires_delta: Durée personnalisée (sinon utilise les defaults)
    """
    now = datetime.now(timezone.utc)
    if token_type == "access":
        expires_delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expires_delta = expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    
    session = AuthSession(
        user_id=user_id,
        tenant_id=tenant_id,
        jti=jti,                    # ← Le lien entre la session DB et le JWT
        token_type=token_type,      # ← Type du token : "access", "refresh", "partial"
        user_agent=user_agent,      # ← FIXED: Store client user-agent
        ip_address=ip_address,      # ← FIXED: Store client IP address
        created_at=now,
        expires_at=now + expires_delta,
        revoked_at=None,            # NULL = session active. Non-NULL = révoquée.
        last_used_at=None,          # Sera mis à jour au premier usage
    )
    db.add(session)
    # ⚠️ REMOVED db.commit() HERE — will be committed by caller
    # db.commit()
    # db.refresh(session)
    return session


def revoke_auth_session(db: Session, jti: str) -> Optional[AuthSession]:
    """
    Révoque une session (logout d'un appareil).

    Définit revoked_at = maintenant sur la session correspondant au JTI.
    Après ça, les requêtes avec ce token seront rejetées par get_current_user().
    
    ⚠️  PROBLÈME 4 : Ne modifie QUE revoked_at (jamais replaced_by).
                     Le commit()) appartient à l'endpoint, pas au helper.

    Retourne la session révoquée, ou None si le JTI est introuvable.
    """
    session = db.query(AuthSession).filter(AuthSession.jti == jti).first()
    if not session:
        return None

    session.revoked_at = datetime.now(timezone.utc)
    # ⚠️ REMOVED db.commit() — commit belongs to the calling endpoint
    # db.commit()
    return session


def enforce_session_limit(
    db: Session,
    user_id: UUID,
    tenant_id: UUID,
    max_sessions: int = MAX_SESSIONS
) -> int:
    """
    Vérifie le nombre de sessions actives de l'utilisateur.
    Si la limite est atteinte, révoque la plus ancienne (last_used_at le plus ancien).
    Retourne le nombre de sessions révoquées (0 ou 1).
    
    Règle : révoquer la PLUS ANCIENNE seulement, jamais toutes.
    """
    now = datetime.now(timezone.utc)

    # Récupérer toutes les sessions refresh actives et non expirées
    # (on compte uniquement les refresh tokens — ce sont les sessions "appareils")
    active_sessions = (
        db.query(AuthSession)
        .filter(
            AuthSession.user_id == user_id,
            AuthSession.tenant_id == tenant_id,
            AuthSession.token_type == "refresh",
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
        .order_by(AuthSession.last_used_at.asc().nullsfirst())
        .all()
    )

    if len(active_sessions) < max_sessions:
        return 0  # Pas encore à la limite

    # Révoquer uniquement la plus ancienne (premier élément après tri asc)
    oldest_session = active_sessions[0]
    oldest_session.revoked_at = now
    db.commit()

    logger.info(
        "🔒 Session limit reached | user=%s | sessions=%d/%d | "
        "revoked_session=%s (last_used=%s)",
        user_id,
        len(active_sessions),
        max_sessions,
        oldest_session.jti,
        oldest_session.last_used_at,
    )

    return 1


# ==============================================================================
#  HELPER INTERNE : Vérification du JTI (évite la redondance)
# ==============================================================================

def _check_jti_valid(db: Session, jti: str) -> Optional[AuthSession]:
    """
    Vérifie qu'un JTI est valide et n'a pas été révoqué.
    
    Logique consolidée pour éviter la redondance dans get_current_user()
    et verify_jti_not_revoked().
    
    Retourne la session si valide, None si révoquée/expirée/inexistante.
    """
    if not jti:
        return None
    
    now = datetime.now(timezone.utc)
    session = db.query(AuthSession).filter(
        and_(
            AuthSession.jti == jti,
            AuthSession.revoked_at == None,  # noqa: E711
            AuthSession.expires_at > now,
        )
    ).first()
    
    if session:
        session.ensure_timezone_aware()
    
    return session


# ==============================================================================
#  PARTIE 3 : DÉPENDANCES FASTAPI (le cœur de la sécurité)
# ==============================================================================


async def get_current_user(
    request: Request,  # ← ADD to access cookies
    token: Optional[str] = Depends(oauth2_scheme),  # Make optional since token may come from cookie
    db: Session = Depends(get_db)
) -> User:
    """
    🔑 LA DÉPENDANCE LA PLUS IMPORTANTE DU PROJET.

    Appelée automatiquement sur CHAQUE endpoint qui utilise Depends(get_current_user).

    FLUX EN 4 ÉTAPES :
    ──────────────────
    Étape 1 : Vérification du JWT
        → Signature valide ? Token non expiré ? Claims présents ?
        → Type = "access" ? (on n'accepte pas les refresh tokens ici)
        → Lecture depuis: 1) Header Authorization (priorité) ou 2) Cookie access_token

    Étape 2 : Vérification de la révocation du JTI
        → Le JTI est-il dans auth_sessions avec revoked_at IS NULL ?
        → Si la session a été révoquée (logout) → 401 immédiat
        → Sans cette vérification, un token restait valide 30 min après logout !

    Étape 3 : Chargement de l'utilisateur depuis la DB
        → Récupère l'objet User complet (avec tenant_id, role_id, etc.)

    Étape 4 : Vérification que le compte est actif
        → is_active = False → 403 (admin peut désactiver un compte)

    Si toutes les étapes passent → retourne l'objet User.
    Sinon → lève HTTPException (401 ou 403) → FastAPI répond automatiquement.
    """
    # Message d'erreur générique (on ne dit pas CE qui est invalide → sécurité)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ── Étape 0 : Récupérer le token (header ou cookie) ──────────────────────
    # Priorité 1 : Header Authorization (pour API clients)
    # Priorité 2 : Cookie access_token (pour frontend navigateur)
    final_token = token
    if not final_token:
        final_token = request.cookies.get("access_token")
    
    if not final_token:
        raise credentials_exception

    # ── ÉTAPE 1 : Vérifier la signature et les claims ──────────────────────────
    try:
        payload    = verify_token(final_token)
        user_id    = payload.get("sub")       # "sub" = subject = identifiant user
        tenant_id  = payload.get("tenant_id") # Extrait du JWT (signé par le serveur)
        token_type = payload.get("type", "access")

        if not user_id:
            raise credentials_exception

        # On n'accepte QUE les access tokens pour accéder aux ressources.
        # Les refresh tokens ne servent qu'à /auth/refresh.
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisez votre access token (pas le refresh token).",
                headers={"WWW-Authenticate": "Bearer"},
            )

        
            set_tenant_context(db, UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id)

    except JWTError:
        raise credentials_exception

    # ── ÉTAPE 2 : Vérifier que le JTI n'est pas révoqué ───────────────────────
    jti = payload.get("jti")
    if jti:
        session = _check_jti_valid(db, jti)
        if not session:
            # Pas de session active → token révoqué (logout) ou jamais enregistré
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session révoquée. Veuillez vous reconnecter.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        
        try:
            session.last_used_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to update session.last_used_at: {e}")

    # ── ÉTAPE 3 : Charger l'utilisateur depuis la base de données ─────────────
    try:
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, TypeError):
        raise credentials_exception  # user_id malformé

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise credentials_exception  # Utilisateur supprimé depuis l'émission du token

    # ── ÉTAPE 4 : Vérifier que le compte est toujours actif ───────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé. Contactez votre administrateur.",
        )

    
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),  # Hérite de get_current_user
    db: Session = Depends(get_db)
) -> User:
    """
    Dépendance pour les endpoints ADMIN uniquement.

    Construit sur get_current_user : d'abord on vérifie le JWT,
    puis on vérifie en plus que l'utilisateur a un rôle admin.

    Usage :
        @app.delete("/admin/users/{id}")
        async def delete_user(admin: User = Depends(get_current_admin)):
            ...  # Seuls les admins arrivent ici
    """
    if not current_user.role_id:
        raise HTTPException(status_code=403, detail="Aucun rôle assigné")

    from .models import Role
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    if not role:
        raise HTTPException(status_code=403, detail="Rôle introuvable")

    permissions = role.permissions or []
    # Un utilisateur est admin si :
    # - Son rôle système s'appelle "admin", "superadmin", "system_admin", ou "tenant_admin"
    # - Ou ses permissions contiennent "*" ou "admin:all"
    is_admin = (
        (role.is_system and role.name in ["admin", "superadmin", "system_admin", "tenant_admin"]) or
        "*" in permissions or
        "admin:all" in permissions
    )

    if not is_admin:
        raise HTTPException(status_code=403, detail="Rôle admin requis")

    return current_user


async def verify_jti_not_revoked(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> str:
    """
    Vérifie uniquement que le JTI du token courant n'est pas révoqué.

    Utilisé comme dépendance légère pour les endpoints /logout et /refresh
    qui n'ont pas besoin de charger l'objet User complet.

    Retourne le JTI si valide, lève 401 sinon.
    """
    try:
        payload = verify_token(token)
        jti     = payload.get("jti")
        tenant_id = payload.get("tenant_id")

        if not jti:
            raise HTTPException(status_code=401, detail="Token invalide (JTI absent)")

       
        if tenant_id:
            set_tenant_context(db, UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id)

        session = _check_jti_valid(db, jti)
        if not session:
            raise HTTPException(status_code=401, detail="Token révoqué ou expiré.")

        return jti

    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
