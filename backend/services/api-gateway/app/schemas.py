# ==============================================================================
# SCHEMAS.PY — Validation des données entrantes et sortantes
# ==============================================================================

from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID


# ==============================================================================
# TENANT (Organisation / Client)
# ==============================================================================


class TenantCreate(BaseModel):
    """
    Données pour créer une organisation.
    Utilisé par : POST /api/v1/tenants (admin système uniquement)
    """
    name: str = Field(..., min_length=1, max_length=255,
                      description="Nom de l'organisation")
    email: EmailStr = Field(..., description="Email principal de contact")
    subscription_plan: str = Field(
        default="free",
        pattern="^(free|starter|professional|enterprise)$",
        description="Plan tarifaire. Doit être exactement l'un de ces 4 mots."
    )
    # Fields for 4-step registration wizard
    sector: Optional[str] = None
    org_size: Optional[str] = None
    country: Optional[str] = Field(default="TN", max_length=2)
    portals: Optional[List[str]] = None
    plan: Optional[str] = None
    billing: Optional[str] = Field(default="annual")
    trial_ends_at: Optional[datetime] = None


class TenantUpdate(BaseModel):
    """
    Données pour modifier une organisation.
    Tous les champs sont optionnels → on envoie seulement ce qu'on veut changer.
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    subscription_plan: Optional[str] = Field(
        None, pattern="^(free|starter|professional|enterprise)$"
    )
    is_active: Optional[bool] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    tenant_metadata: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    """
    Données d'une organisation envoyées au client.
    Config.from_attributes = True permet de convertir directement un objet
    SQLAlchemy (résultat de db.query()) en réponse JSON sans étape manuelle.
    """
    id: UUID
    name: str
    email: str
    subscription_plan: str
    is_active: bool
    sector: Optional[str] = None
    country: Optional[str] = None
    tenant_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  


# ==============================================================================
# ROLE (Contrôle d'accès RBAC)
# ==============================================================================


class RoleCreate(BaseModel):
    """Données pour créer un rôle."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: Union[Dict[str, Any], List[str]] = Field(
        default_factory=list,
        description="Permissions au format dict ou liste. Ex: {'documents': 'read'} ou ['documents.read']"
    )


class RoleUpdate(BaseModel):
    """Données pour modifier un rôle (tous les champs optionnels)."""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Union[Dict[str, Any], List[str]]] = None


class RoleResponse(BaseModel):
    """Données d'un rôle envoyées au client."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    permissions: Optional[Union[Dict[str, Any], List[str]]] = None
    is_system: bool  # True = rôle créé par le système (immuable). False = créé par l'admin.
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
#  USER (Utilisateur)
# ==============================================================================

class UserCreate(BaseModel):
    """
    Données pour créer un utilisateur.
    Accepte SOIT role_id (UUID), SOIT role (nom de rôle string).
    Si role (string) est fourni, l'API cherchera le rôle par son nom.
    """
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8,
                          description="Minimum 8 caractères. Sera hashé (Argon2id) avant stockage.")
    role_id: Optional[UUID] = None  # Si fourni, UUID du rôle
    role: Optional[str] = None  # Si fourni (ex: 'analyst', 'admin'), sera résolu par le backend


class UserLogin(BaseModel):
    """
    Credentials pour se connecter.
    Envoyé par le frontend sur POST /api/v1/auth/login.
    """
    email: EmailStr
    password: str  


class UserUpdate(BaseModel):
    """
    Données pour modifier un utilisateur.
    Tous optionnels → on ne met à jour que ce qui est envoyé.
    """
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8,
                                    description="Si fourni, sera hashé avant stockage")
    is_active: Optional[bool] = None
    role_id: Optional[UUID] = None


class UserResponse(BaseModel):
    """
    Données utilisateur de base envoyées au client.

     Inclut : id, email, full_name, tenant_id, role_id, is_active
     N'inclut JAMAIS : hashed_password, tokens, clés secrètes

    Règle d'or : un schema Response ne doit JAMAIS exposer de données
    qui permettraient de compromettre la sécurité.
    """
    id: UUID
    tenant_id: UUID
    role_id: Optional[UUID]
    email: str
    full_name: Optional[str]
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """
    Données utilisateur avec son rôle inclus (jointure).
    Hérite de UserResponse + ajoute l'objet rôle complet.
    """
    role: Optional[RoleResponse] = None


class UserProfileResponse(BaseModel):
  
    # ── Champs de l'utilisateur ────────────────────────────────────────────────
    id: UUID
    email: str
    full_name: Optional[str]
    role: Optional[str] = None    
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime

    # ── Champs du tenant (attendus par AuthContext.jsx) ────────────────────────
    tenant_id: UUID
    tenant_name: str               # ← "BuildCorp International" affiché dans la sidebar
    subscription_plan: str         # ← "professional" affiché dans le badge RLS
    tenant_color: Optional[str] = None  # ← "#D4A84B" (or) ou "#4B9FD4" (bleu)

    # ── Statut 2FA (pour afficher/masquer les boutons 2FA dans settings) ────────
    totp_enabled: bool = False     # ← True si l'utilisateur a 2FA activée

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """
    Request pour PATCH /api/v1/auth/me
    Modification du profil utilisateur (full_name uniquement).
    Email ne peut être modifié ici — flow séparé nécessaire.
    """
    full_name: Optional[str] = Field(None, min_length=2, max_length=255, description="Nom complet")

    class Config:
        from_attributes = True


# ==============================================================================
#  AUTH (Tokens & Sessions)
# ==============================================================================

class TokenResponse(BaseModel):
    """
    Réponse après un login réussi ou un refresh réussi.

    Le client doit :
    1. Sauvegarder access_token  → l'envoyer dans Authorization: Bearer <token>
    2. Sauvegarder refresh_token → l'envoyer sur /auth/refresh quand access_token expire
    3. expires_in : le client peut calculer quand refresh le token (en secondes)
    """
    access_token: str    # JWT court terme (30 min) pour toutes les requêtes
    refresh_token: str   # JWT long terme (7 jours) pour renouveler access_token
    token_type: str = "bearer"  # Standard OAuth2 : toujours "bearer"
    expires_in: int = 1800      # 30 min en secondes


class RefreshRequest(BaseModel):
    """
    Body pour POST /api/v1/auth/refresh.
    Le client envoie son refresh_token pour obtenir un nouvel access_token.
    """
    refresh_token: str


# ==============================================================================
#  PASSWORD RESET (Recovery Flow)
# ==============================================================================

class PasswordResetRequest(BaseModel):
    """
    Request pour POST /api/v1/auth/password-reset/request
    
    No user enumeration:
    - Endpoint toujours retourne 200 OK (même si email inexistant)
    - Email est envoyé seulement si l'email existe
    - Attaquant ne peut pas deviner les utilisateurs par pattern
    
    Pattern: "Nous t'avons envoyé un lien de réinitialisation par email"
    """
    email: EmailStr = Field(
        ...,
        description="Email de l'utilisateur (si existe, un lien sera envoyé)"
    )


class PasswordResetConfirm(BaseModel):
    """
    Request pour POST /api/v1/auth/password-reset/confirm
    
     Token lifecycle:
    - Redis key: f"pwd_reset:{token}"
    - TTL: 1 heure
    - Contient: user_id
    - Validation: Token trouvé + pas expiré + pas révoqué
    
     Nouveau mot de passe:
    - Min 8 caractères
    - Sera hashé via Argon2id (voir SecurePasswordManager)
    """
    token: str = Field(
        ...,
        min_length=10,
        description="Token de réinitialisation depuis l'email"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Nouveau mot de passe (min 8 caractères)"
    )


class PasswordResetResponse(BaseModel):
    """
    Response pour POST /api/v1/auth/password-reset/confirm
    """
    status: str = Field(..., description="always 'success'")
    message: str = Field(..., description="Password updated successfully")


class ChangePasswordRequest(BaseModel):
    """
    Request pour POST /api/v1/auth/change-password
    Changement de mot de passe avec vérification de l'ancien mot de passe.
    """
    current_password: str = Field(..., min_length=1, description="Mot de passe actuel pour vérification")
    new_password: str = Field(..., min_length=8, max_length=128, description="Nouveau mot de passe (min 8 caractères)")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Confirmation du nouveau mot de passe")

    def validate_passwords(self) -> 'ChangePasswordRequest':
        if self.new_password != self.confirm_password:
            raise ValueError('Les mots de passe ne correspondent pas')
        if self.current_password == self.new_password:
            raise ValueError('Le nouveau mot de passe doit être différent de l\'ancien')
        return self


class ChangePasswordResponse(BaseModel):
    """
    Response pour POST /api/v1/auth/change-password
    """
    message: str = Field(..., description="Mot de passe modifié avec succès")


# ==============================================================================
# 👥 USER INVITATION (P0 feature)
# ==============================================================================

class UserInvitationRequest(BaseModel):
    """
    Request pour POST /api/v1/admin/users/invite
    
     Admin/Superadmin can invite new users to their organization
    
     Token lifecycle:
    - Redis key: f"invite:{token}"
    - TTL: 7 days
    - Contient: inviter_id|recipient_email|role|timestamp
    """
    email: EmailStr = Field(
        ...,
        description="Email de l'utilisateur à inviter"
    )
    role: str = Field(
        default="user",
        description="Role for the new user (user/analyst/admin)"
    )


class AcceptInvitationRequest(BaseModel):
    """
    Request pour POST /api/v1/auth/invite/accept
    
    Nouvel utilisateur accepte l'invitation et crée son compte
    """
    token: str = Field(
        ...,
        min_length=10,
        description="Token d'invitation depuis l'email"
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full name of the new user"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 characters)"
    )


class AcceptInvitationResponse(BaseModel):
    """
    Response pour POST /api/v1/auth/invite/accept
    """
    status: str = Field(..., description="always 'success'")
    message: str = Field(..., description="Account created successfully")


class AuthSessionCreate(BaseModel):
    """Métadonnées optionnelles lors du login (pour l'audit de sécurité)."""
    user_agent: Optional[str] = None   # Ex: "Mozilla/5.0 (Windows NT...)"
    ip_address: Optional[str] = None   # Ex: "192.168.1.100"


class AuthSessionResponse(BaseModel):
    """
    Représentation d'une session active (un appareil connecté).

    Utile pour afficher "Sessions actives" dans les paramètres de compte :
    - "Chrome sur Windows — connecté depuis 192.168.1.100"
    - revoked_at = None → session active
    - revoked_at non nul → session terminée (logout)
    """
    id: UUID
    user_id: UUID
    tenant_id: UUID
    jti: UUID           # Identifiant du JWT associé à cette session
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime]  # None si session active, date si révoquée
    last_used_at: Optional[datetime]
    is_current: bool = False

    @field_validator('ip_address', mode='before')
    @classmethod
    def coerce_ip(cls, v: Any) -> Optional[str]:
        return str(v) if v is not None else None

    class Config:
        from_attributes = True


class SessionRevokeResponse(BaseModel):
    """
    Response pour DELETE /api/v1/auth/sessions/{session_id}
    Confirmation de révocation d'une session.
    """
    message: str = Field(..., description="Session révoquée avec succès")
    session_id: str = Field(..., description="ID de la session révoquée")
    revoked_at: datetime = Field(..., description="Timestamp de révocation")


class LoginAttemptResponse(BaseModel):
    """
    Tentative de login (succès ou échec) — journal d'audit immuable.

    Utile pour détecter les attaques brute-force :
    5 échecs consécutifs → bloquer le compte temporairement.
    """
    id: int
    user_id: Optional[UUID]
    email: str
    ip_address: Optional[str]
    success: bool                  # True = login réussi, False = échec
    failure_reason: Optional[str]  # "bad_password", "user_not_found", "account_inactive"
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
#  DOCUMENT (Appel d'offres)
# ==============================================================================

class DocumentCreate(BaseModel):
    """
    Données pour uploader un document.
    Le tenant_id N'EST PAS ici → il est pris depuis le JWT dans la route.
    """
    filename: str = Field(..., min_length=1, max_length=255)
    storage_path: str      # Chemin sur le serveur ou S3
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    language: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None
    # document_metadata peut contenir :
    # { "compliance_score": 87, "budget_eur": 5000000, "deadline": "2026-06-01",
    #   "ref": "AO-2026-001", "category": "Infrastructure" }


class DocumentResponse(BaseModel):
    """Données d'un document envoyées au client."""
    id: UUID
    tenant_id: UUID      # Inclus pour le frontend (affichage du badge RLS)
    filename: str
    file_size: Optional[int]
    mime_type: Optional[str]
    language: Optional[str]
    status: str          # "uploaded", "processing", "completed", etc.
    document_metadata: Dict[str, Any]
    uploaded_by: Optional[UUID]
    created_by: Optional[UUID]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    download_url: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    """Document avec l'objet User de l'uploadeur inclus (jointure)."""
    uploaded_by_user: Optional[UserResponse] = None
#################################################################################

class DocumentDeleteRequest(BaseModel):
    """Requête de suppression avec raison optionnelle."""
    reason: Optional[str] = None
    
class DocumentDeleteResponse(BaseModel):
    """Réponse de suppression."""
    id: UUID
    filename: str
    deleted_at: datetime
    deleted_by: UUID
    reason: Optional[str]
    message: str
###############################################################################


# ==============================================================================
#  STATS DASHBOARD
# ==============================================================================

class DocumentStatsResponse(BaseModel):
    """
    Statistiques agrégées pour le tableau de bord.
    Retournées par GET /api/v1/me/documents/stats.

    Le tenant_id est extrait du JWT → les stats sont automatiquement
    celles du bon tenant (isolation garantie par RLS).
    """
    total: int                              # Nombre total de documents
    completed: int                          # Documents avec status="completed"
    processing: int                         # Documents en cours de traitement
    avg_score: Optional[float]              # Score moyen de conformité (0-100)
    total_budget_eur: Optional[float]       # Somme des budgets en euros
    next_deadline: Optional[Dict[str, Any]] # Prochain appel d'offres à échéance
    # next_deadline = {"ref": "AO-2026-001", "deadline": "2026-06-01", "days_remaining": 15}


# ==============================================================================
#  COMPLIANCE REPORT
# ==============================================================================

class ComplianceReportResponse(BaseModel):
    """
    Rapport de conformité générée automatiquement lors de l'analyse d'un document.
    
    Retourné par : dashboard endpoints
    """
    id: UUID = Field(..., description="Compliance report ID")
    tenant_id: UUID = Field(..., description="Tenant propriétaire")
    document_id: UUID = Field(..., description="Document analysé")
    compliance_score: Optional[float] = Field(None,description="Score 0-100")
    status: str = Field(default="pending", description="pending, completed, or error")
    summary: Optional[Dict[str, Any]] = Field(None, description="Résumé du rapport")
    findings: Optional[List[str]] = Field(None, description="Conclusion de l'analyse")
    created_at: datetime = Field(..., description="Création du rapport")
    
    class Config:
        from_attributes = True


# ==============================================================================
#  AUDIT LOG (Journal immuable)
# ==============================================================================

class AuditLogResponse(BaseModel):
    """
    Entrée du journal d'audit — READ ONLY.

     PROPRIÉTÉ CLÉ : ce journal est IMMUABLE.
    Les logs ne peuvent être qu'ajoutés (INSERT), jamais modifiés (UPDATE/DELETE).
    Un hash chain (chaque entrée contient le hash de la précédente) permet
    de détecter toute tentative de falsification rétroactive.

    Utile pour répondre à : "Qui a supprimé ce document le 14 février ?"
    
     CHAMPS JOINTS (depuis users) :
    - user_email : email de l'utilisateur (NULL si action système/scheduler)
    - user_name : "{first_name} {last_name}" (NULL si action système)
    """
    id: int
    tenant_id: UUID
    user_id: Optional[UUID] = None
    action: str          # "create", "read", "update", "delete", "login", "logout"
    resource_type: str   # "document", "user", "role", "tenant"
    resource_id: Optional[UUID] = None
    old_value: Optional[Dict[str, Any]] = None  # État avant modification
    new_value: Optional[Dict[str, Any]] = None  # État après modification
    status: str = "success"          # "success" ou "failure"
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    hash: Optional[str] = None         # SHA256 de ce log + hash précédent
    previous_hash: Optional[str] = None  # Hash du log précédent (chaîne d'intégrité)
    # Champs joints (depuis users table)
    user_email: Optional[str] = None      # email de l'utilisateur (NULL si système)
    user_name: Optional[str] = None       # "{first_name} {last_name}" (NULL si système)

    class Config:
        from_attributes = True


# ==============================================================================
#   DASHBOARD (Vue agrégée)
# ==============================================================================

class DashboardResponse(BaseModel):
    """
    Réponse complète pour le tableau de bord.
    Retournée par GET /api/v1/me/dashboard.

    Contient tout ce dont le frontend a besoin en une seule requête :
    - Infos du tenant (pour la sidebar)
    - Profil de l'utilisateur
    - Liste des documents récents (10 derniers)
    - Activité récente (5 derniers logs d'audit)
    - Compteur total de documents

     ISOLATION : les données sont celles du tenant de l'utilisateur
    connecté uniquement (filtrées par RLS).
    """
    tenant: TenantResponse
    user: UserResponse
    documents: List[DocumentResponse]
    total_documents: int
    recent_audits: List[AuditLogResponse]

    class Config:
        from_attributes = True


# ==============================================================================
#  NOTIFICATIONS
# ==============================================================================

class NotificationResponse(BaseModel):
    """
    Notification envoyée à un utilisateur ou au tenant entier.
    
    Utilisée par : GET /api/v1/me/notifications, GET /api/v1/me/dashboard/*
    """
    id: UUID = Field(..., description="Notification ID")
    tenant_id: UUID = Field(..., description="Tenant propriétaire")
    user_id: Optional[UUID] = Field(None, description="User destinataire (NULL = broadcast)")
    type: str = Field(..., description="Type: urgent, info, success")
    message: str = Field(..., description="Texte du message")
    is_read: bool = Field(default=False, description="A été lue?")
    created_at: datetime = Field(..., description="Timestamp création")
    
    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    """
    Données pour marquer une notification comme lue.
    Utilisée par : PATCH /api/v1/me/notifications/{id}/read
    """
    is_read: bool = Field(default=True, description="Marquer comme lue?")


# ==============================================================================
#  ENRICHED DASHBOARD RESPONSES
# ==============================================================================

class KPIData(BaseModel):
    """KPI metrics for dashboard (admin or user view)."""
    # Admin KPIs
    active_documents: Optional[int] = Field(None, description="Documents en cours de traitement")
    avg_compliance_score: Optional[float] = Field(None, description="Score moyen de conformité")
    total_documents: Optional[int] = Field(None, description="Total des documents")
    win_rate: Optional[float] = Field(None, description="Taux de succès (%)")
    # User KPIs
    my_documents: Optional[int] = Field(None, description="Mes documents (user view)")
    my_completed: Optional[int] = Field(None, description="Mes documents complétés (user view)")
    my_avg_score: Optional[float] = Field(None, description="Mon score moyen de conformité (user view)")


class StatusDistribution(BaseModel):
    """Distribution des statuts de documents."""
    pending: int = Field(default=0, description="En attente")
    processing: int = Field(default=0, description="En cours")
    completed: int = Field(default=0, description="Complétés")
    failed: int = Field(default=0, description="Échoués")


class TeamActivityItem(BaseModel):
    """Activité d'un membre de l'équipe."""
    user_id: UUID = Field(..., description="ID de l'utilisateur")
    full_name: str = Field(..., description="Nom complet")
    action: str = Field(..., description="Action effectuée")
    resource_type: str = Field(..., description="Type de ressource")
    resource_id: Optional[UUID] = Field(None, description="ID de la ressource")
    timestamp: datetime = Field(..., description="Quand?")


class LastAnalysisItem(BaseModel):
    """Last compliance analysis result (user dashboard)."""
    document: DocumentResponse = Field(..., description="Document analysé")
    report: "ComplianceReportResponse" = Field(..., description="Rapport de conformité")


class AdminDashboardResponse(BaseModel):
    """
    Dashboard pour les administrateurs (tenant_admin role).
    
    Contient des stats agrégées du tenant entier.
    Utilisée par : GET /api/v1/me/dashboard/admin
    """
    tenant: TenantResponse = Field(..., description="Infos du tenant")
    user: UserResponse = Field(..., description="Profil utilisateur")
    
    kpis: KPIData = Field(..., description="KPIs tenant-wide")
    recent_documents: List[DocumentResponse] = Field(..., description="5 derniers documents")
    status_distribution: StatusDistribution = Field(..., description="Distribution des statuts")
    team_activity: List[TeamActivityItem] = Field(..., description="5 dernières actions")
    notifications: List[NotificationResponse] = Field(..., description="5 dernières notifications")
    
    class Config:
        from_attributes = True


class UserDashboardResponse(BaseModel):
    """
    Dashboard pour les utilisateurs réguliers (analyst, viewer, etc).
    
    Contient des stats personnelles de l'utilisateur.
    Utilisée par : GET /api/v1/me/dashboard/user
    """
    tenant: TenantResponse = Field(..., description="Infos du tenant")
    user: UserResponse = Field(..., description="Profil utilisateur")
    
    kpis: KPIData = Field(..., description="KPIs personnels")
    my_documents: List[DocumentResponse] = Field(..., description="Mes 10 derniers documents")
    upcoming_deadlines: List[DocumentResponse] = Field(..., description="3 prochaines échéances")
    last_analysis: Optional[LastAnalysisItem] = Field(None, description="Dernière analyse")
    notifications: List[NotificationResponse] = Field(..., description="5 dernières notifications")
    
    class Config:
        from_attributes = True


# ==============================================================================
#   UTILITAIRES
# ==============================================================================

class ErrorResponse(BaseModel):
    """
    Format standardisé pour toutes les erreurs API.

    Exemples :
        400 → {"detail": "Email déjà utilisé",       "error_code": "duplicate_email"}
        401 → {"detail": "Token invalide ou expiré", "error_code": "invalid_token"}
        403 → {"detail": "Rôle admin requis",        "error_code": "forbidden"}
        404 → {"detail": "Document non trouvé",      "error_code": "not_found"}
    """
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel):
    """
    Réponse paginée standardisée pour les listes.

    Toutes les routes qui retournent une liste utilisent ce format.
    Le frontend peut ainsi générer la pagination de façon cohérente.

    Exemple de réponse JSON :
        {
            "items": [{...}, {...}, ...],   ← éléments de la page courante
            "total": 237,                   ← nombre total d'éléments
            "page": 2,                      ← page courante
            "page_size": 10,                ← éléments par page
            "pages": 24                     ← nombre total de pages
        }

    Utilisation frontend :
        - Désactiver "Précédent" si page == 1
        - Désactiver "Suivant" si page >= pages
        - Afficher "Résultats 11-20 sur 237"
    """
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


# ==============================================================================
#  REGISTRATION (4-Step Wizard)
# ==============================================================================

class RegisterRequest(BaseModel):
    """
    Payload envoyé par le frontend lors de l'inscription (Step 4: confirmation).

    Ce schema fusionne les données des 4 étapes :
    - Step 1: Account (first_name, last_name, email, password)
    - Step 2: Organization (org_name, sector, country, org_size, portals)
    - Step 3: Plan (plan, billing)
    - Step 4: Confirmation (envoi du formulaire)

     VALIDATION (effectuée par le frontend + le backend) :
        - first_name, last_name : 2-100 chars, pas vides
        - email : EmailStr valide, pas de @gmail.com/@yahoo.fr
        - password : 12-128 chars, ≥1 majuscule, ≥1 minuscule, ≥1 digit, ≥1 spécial
        - org_name : 2-200 chars
        - sector : string (ex: "Energie", "Telecom", "Construction")
        - country : 2 chars ISO (ex: "TN", "DZ", "MA")
        - org_size : enum ("small", "medium", "large", "enterprise")
        - portals : list[str], min 1 item (ex: ["TUNEPS", "SOENEWS"])
        - plan : enum ("Fondements", "Avancée", "Entreprise")
        - billing : enum ("monthly", "annual"), default "annual"
    """
    first_name: str = Field(..., min_length=2, max_length=100,
                            description="Prénom de l'utilisateur")
    last_name: str = Field(..., min_length=2, max_length=100,
                           description="Nom de famille")
    email: EmailStr = Field(..., description="Email unique (pas gmail/yahoo)")
    password: str = Field(..., min_length=12, max_length=128,
                          description="Mot de passe (min 12 chars, spécial required)")

    org_name: str = Field(..., min_length=2, max_length=200,
                          description="Nom de l'organisation")
    sector: str = Field(..., description="Secteur d'activité (ex: 'Energie')")
    country: str = Field(default="TN", max_length=2,
                        description="Code ISO (ex: 'TN' pour Tunisie)")
    org_size: str = Field(..., description="Taille org: 'small', 'medium', 'large', 'enterprise'")
    portals: List[str] = Field(..., min_items=1,
                              description="Portals sélectionnés (ex: ['TUNEPS', 'SOENEWS'])")
    plan: str = Field(..., description="Plan: 'Fondements', 'Avancée', 'Entreprise'")
    billing: str = Field(default="annual", description="Facturation: 'monthly' ou 'annual'")


class RegisterResponse(BaseModel):
    """
    Réponse du backend après inscription réussie.

    Retournée par POST /api/v1/auth/register (201 Created).

    FLUX (email verification + 2FA) :
    1. Frontend reçoit RegisterResponse avec email_verified = false
    2. Frontend NE doit PAS utiliser access_token/refresh_token
    3. Frontend redirige vers /register/verify-email?email=...
    4. User clique lien dans email → frontend appelle GET /api/v1/auth/verify-email?token=xxx
    5. Backend valide token, set email_verified = true, retourne setup-2fa redirect URL
    6. Frontend redirige vers /register/setup-2fa
    7. User valide code TOTP → frontend appelle POST /api/v1/auth/2fa/verify
    8. Success → frontend utilise tokens pour accéder à /dashboard

     SÉCURITÉ :
        - password n'est JAMAIS retourné
        - Tokens retournés mais ne sont valides que si email verified + 2FA setup
        - tenant_id inclus pour validation du frontend
        - trial_ends_at calculé côté backend (14 jours)
        - email_verified flag indique état verification
    """
    access_token: str = Field(..., description="JWT court terme (15 min) — valide que si email_verified=true ET 2FA setup")
    refresh_token: str = Field(..., description="JWT long terme (7 jours) — valide que si email_verified=true ET 2FA setup")
    token_type: str = Field(default="bearer", description="Toujours 'bearer'")
    expires_in: int = Field(default=900, description="Validité access_token en secondes (15 min)")

    user_id: UUID = Field(..., description="ID du nouvel utilisateur")
    tenant_id: UUID = Field(..., description="ID du nouvel tenant")
    email: str = Field(..., description="Email confirmé")
    tenant_name: str = Field(..., description="Nom du tenant créé")
    trial_ends_at: datetime = Field(..., description="Date fin essai (14 jours)")
    
    email_verified: bool = Field(default=False, description="Email vérifié via lien confirmation (TTL 24h)")

    class Config:
        from_attributes = True


# ==============================================================================
#  ANALYSE IA (Appels d'offres Analysis)
# ==============================================================================

class AnalyseStatsResponse(BaseModel):
    """
    Statistiques d'analyse du mois/trimestre courant.
    Retournée par GET /api/v1/analyse/stats.
    """
    total_analysed: int = Field(..., description="AOs analysés ce mois")
    avg_conformite: int = Field(..., description="Conformité moyenne %")
    hours_saved: int = Field(..., description="Heures économisées ce trimestre")
    success_rate: int = Field(..., description="Taux de succès %")
    delta_analysed: int = Field(..., description="Changement vs mois précédent")
    delta_conformite: int = Field(..., description="Points de conformité gagnés")
    delta_success_rate: Optional[int] = Field(None, description="Points de taux de succès gagnés vs marché")


class AnalyseRequestSchema(BaseModel):
    """
    Payload pour lancer une analyse.
    Utilisé par POST /api/v1/analyse/run.
    """
    tender_id: Optional[str] = Field(None, description="ID de l'appel d'offres")
    document_url: Optional[str] = Field(None, description="URL du document pour analyse externalisée")
    type: str = Field(..., description="conformite, technique, financier, complet")
    lang: str = Field(..., description="FR, AR, EN")
    scope: List[str] = Field(..., description="criteres, risques, reponse, score")
    detail: str = Field(..., description="synthese ou approfondi")


class AnalyseResultResponse(BaseModel):
    """
    Résultat d'une analyse IA.
    Retourné par POST /api/v1/analyse/run, GET /api/v1/analyse/{id}.
    """
    id: str = Field(..., description="Analyse ID")
    score_conformite: float = Field(..., description="Score de conformité 0-100")
    score_technique: float = Field(..., description="Score technique 0-100")
    score_risque: float = Field(..., description="Score risque 0-100")
    resume: str = Field(..., description="Résumé de l'analyse")
    criteres_manquants: List[str] = Field(..., description="Critères non remplis")
    risques: List[str] = Field(..., description="Risques identifiés")
    reponse_generee: str = Field(..., description="Réponse générée par l'IA")
    recommandations: List[str] = Field(..., description="Recommandations")
    created_at: str = Field(..., description="ISO timestamp")


class AnalyseHistoryItemResponse(BaseModel):
    """
    Élément de l'historique des analyses.
    Retourné par GET /api/v1/analyse/history.
    """
    id: str = Field(..., description="Analyse ID")
    file_name: str = Field(..., description="Nom du fichier analysé")
    created_at: str = Field(..., description="ISO timestamp")
    type: str = Field(..., description="Type d'analyse")
    score_conformite: float = Field(..., description="Score de conformité")
    lang: str = Field(..., description="Langue FR/AR/EN")


