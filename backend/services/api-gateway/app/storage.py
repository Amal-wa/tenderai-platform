# ==============================================================================
# STORAGE.PY — Client MinIO pour le stockage des fichiers
# ==============================================================================
# Importations des bibliothèques nécessaires
import os                    # Pour lire les variables d'environnement (configuration)
import uuid                  # Pour générer des identifiants uniques (éviter les conflits)
from datetime import datetime, timedelta, timezone  # Pour gérer les dates et les durées d'expiration
from typing import BinaryIO     # Pour le typage (meilleure lisibilité du code)
from minio import Minio      # La bibliothèque cliente pour communiquer avec MinIO
from minio.error import S3Error  # Les erreurs spécifiques à MinIO/S3
import logging               # Pour écrire des logs (utile pour debugging)

# Création d'un logger pour ce module
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION DE MINIO
# =============================================================================


MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")      # Adresse du serveur MinIO
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "")            # Nom d'utilisateur MinIO  
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "")      # Mot de passe MinIO
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "tenderai-documents")  # "Dossier" principal
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true" # HTTPS ou HTTP (false = HTTP)

if not MINIO_ACCESS_KEY or not MINIO_SECRET_KEY:
    raise RuntimeError(
        "MINIO_ROOT_USER and MINIO_ROOT_PASSWORD must be set."
    )

class MinIOClient:
    """
    Client singleton pour interagir avec MinIO.
    
     QU'EST-CE QU'UN SINGLETON ?
        C'est un pattern qui garantit qu'il n'y a qu'UNE SEULE instance
        de cette classe dans toute l'application.
        
     ANALOGIE :
        C'est comme avoir un seul maître d'hôtel dans un restaurant.
        Même si 100 clients l'appellent, c'est toujours la même personne
        qui répond. Évite d'avoir 100 maîtres d'hôtel !
        
    AVANTAGES :
        - Économie de mémoire (une seule connexion)
        - Performance (pas de reconnexion à chaque fois)
        - Stabilité (évite les problèmes de connexions multiples)
    """
    
    # Variable de classe pour stocker l'unique instance
    _instance = None
    
    def __new__(cls):
        """
        Méthode appelée AVANT __init__ lors de la création d'instance.
        C'est ici qu'on implémente la logique singleton.
        """
        if cls._instance is None:
            # Première fois qu'on crée l'instance
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False  # Marqueur pour éviter réinitialisation
        return cls._instance  # Retourne toujours la même instance
    
    def __init__(self):
        """
        Initialisation du client MinIO.
        Le if self._initialized évite de réinitialiser plusieurs fois.
        """
        if self._initialized:
            return  # Déjà initialisé, on sort tout de suite
            
        # Création du client MinIO avec les paramètres de configuration
        self.client = Minio(
            MINIO_ENDPOINT,      # Adresse du serveur (ex: localhost:9000)
            access_key=MINIO_ACCESS_KEY,    # Nom d'utilisateur
            secret_key=MINIO_SECRET_KEY,    # Mot de passe
            secure=MINIO_SECURE    # True = HTTPS, False = HTTP
        )
        self.bucket_name = MINIO_BUCKET_NAME
        self._ensure_bucket_exists()  # Vérifie/crée le bucket au démarrage
        self._initialized = True  # Marque comme initialisé pour éviter futures réinitialisations
    
    def _ensure_bucket_exists(self):
        """
        Vérifie si le bucket existe, sinon le crée.
        SÉCURITÉ :
            Le bucket est créé automatiquement seulement s'il n'existe pas.
            Évite les erreurs au premier démarrage de l'application.
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                # Le bucket n'existe pas → on le crée
                self.client.make_bucket(self.bucket_name)
                logger.info(f"✅ Bucket '{self.bucket_name}' créé avec succès")
            else:
                # Le bucket existe déjà → tout est bon
                logger.info(f"✅ Bucket '{self.bucket_name}' existe déjà")
        except S3Error as e:
            logger.error(f"❌ Erreur lors de la création du bucket: {e}")
            raise  # Relance l'erreur pour que l'app s'arrête si problème critique
    
    def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: str,
        tenant_id: str,
        user_id: str,
    ) -> dict:
        """
        Upload un fichier dans MinIO avec une structure organisée.
        
        Structure : {tenant_id}/{year}/{month}/{uuid}_{filename}
        
        Retourne :
            {
                "storage_path": "tenant-uuid/2026/02/doc-uuid_file.pdf",
                "file_size": 1234567,
                "mime_type": "application/pdf",
                "bucket": "tenderai-documents"
            }
        """
        try:
            # Générer un nom de fichier unique
            file_uuid = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            # Structure : raw/tenant_id/year/month/uuid.pdf
            object_name = f"raw/{tenant_id}/{now.year}/{now.month:02d}/{file_uuid}.pdf"
            
            # Obtenir la taille du fichier
            file_data.seek(0, 2)  # Aller à la fin
            file_size = file_data.tell()
            file_data.seek(0)  # Retour au début
            
            # Upload vers MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type,
            )
            
            logger.info(f"✅ Fichier uploadé: {object_name} ({file_size} bytes)")
            
            return {
                "storage_path": object_name,
                "file_size": file_size,
                "mime_type": content_type,
                "bucket": self.bucket_name,
            }
            
        except S3Error as e:
            logger.error(f"❌ Erreur upload MinIO: {e}")
            raise Exception(f"Erreur lors de l'upload: {str(e)}")
    
    def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Génère une URL signée temporaire pour télécharger un fichier.
        Utile pour que le frontend puisse télécharger sans credentials.
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires,
            )
            return url
        except S3Error as e:
            logger.error(f"❌ Erreur génération URL: {e}")
            raise
    
    def delete_file(self, object_name: str):
        """Supprime un fichier de MinIO."""
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            logger.info(f"✅ Fichier supprimé: {object_name}")
        except S3Error as e:
            logger.error(f"❌ Erreur suppression: {e}")
            raise
    
    def upload_logo(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: str,
        tenant_id: str,
    ) -> dict:
        """
        Upload tenant logo to MinIO.
        
        Structure: logos/{tenant_id}/logo.{ext}
        Validates: image MIME types only, max 2MB
        
        Raises ValueError if invalid file type or size > 2MB
        
        Returns:
            {
                "storage_path": "logos/tenant-uuid/logo.png",
                "file_size": 45678,
                "mime_type": "image/png",
                "bucket": "tenderai-documents"
            }
        """
        try:
            # Allowed image MIME types
            ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp", "image/svg+xml"}
            if content_type not in ALLOWED_TYPES:
                raise ValueError(
                    f"Invalid MIME type '{content_type}'. Allowed: {', '.join(ALLOWED_TYPES)}"
                )
            
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Seek to start
            
            # Check max size (2MB)
            MAX_SIZE = 2 * 1024 * 1024  # 2 MB
            if file_size > MAX_SIZE:
                raise ValueError(f"Logo file too large. Max size: 2MB, Got: {file_size // (1024*1024)}MB")
            
            # Extract file extension
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'png'
            if ext not in {'png', 'jpg', 'jpeg', 'webp', 'svg'}:
                ext = 'png'  # Default to png if unknown
            
            # Build object name
            object_name = f"logos/{tenant_id}/logo.{ext}"
            
            # Upload to MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type,
            )
            
            logger.info(f"✅ Logo uploaded: {object_name} ({file_size} bytes)")
            
            return {
                "storage_path": object_name,
                "file_size": file_size,
                "mime_type": content_type,
                "bucket": self.bucket_name,
            }
            
        except ValueError as e:
            logger.error(f"❌ Logo validation error: {e}")
            raise
        except S3Error as e:
            logger.error(f"❌ MinIO error during logo upload: {e}")
            raise Exception(f"Error uploading logo: {str(e)}")


# Instance singleton
minio_client = MinIOClient()