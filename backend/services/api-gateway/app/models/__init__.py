# ==============================================================================
# MODELS - Imports centraux des modèles SQLAlchemy
# ==============================================================================


from .base import Base, BaseModel, TenantModel, TimestampMixin, TenantMixin
from .enums import (
    SubscriptionPlan,
    DocumentStatus,
    LoginFailureReason,
    AuditAction,
    AuditResourceType,
    AuditStatus
)
from .tenant import Tenant
from .role import Role
from .user import User

from .document import Document
from .chunk import Chunk
from .proposal import Proposal
from .compliance_report import ComplianceReport
from .company_asset import CompanyAsset

from .auth_session import AuthSession
from .login_attempt import LoginAttempt
from .audit_log import AuditLog
from .user_totp import UserTOTP
from .api_key_model import APIKey
from .notification import Notification
from .email_job import EmailJob, EmailJobType, EmailJobStatus


__all__ = [
    # ==========================================================================
    #  BASE CLASSES - Classes de base pour tous les modèles
    # ==========================================================================
    "Base",              # Classe parent SQLAlchemy (tous les modèles en héritent)
    "BaseModel",         # Modèle avec timestamps (sans multi-tenant)
    "TenantModel",       # Modèle avec timestamps + tenant_id (multi-tenant)
    "TimestampMixin",    # Mixin pour created_at, updated_at
    "TenantMixin",       # Mixin pour tenant_id (isolation multi-tenant)
    
    # ==========================================================================
    #  ENUMS - Types énumérés pour validation
    # ==========================================================================
    "SubscriptionPlan",      # Plans : free, starter, professional, enterprise
    "DocumentStatus",        # Statuts documents : uploaded, processing, ready, error
    "LoginFailureReason",    # Raisons d'échec login : invalid_credentials, account_disabled, etc.
    "AuditAction",           # Actions auditées : create, read, update, delete, login, etc.
    "AuditResourceType",     # Types de ressources : user, document, tenant, etc.
    "AuditStatus",           # Statuts audit : success, failure, warning
    
    # ==========================================================================
    #  CORE MODELS - Modèles essentiels multi-tenant
    # ==========================================================================
    "Tenant",            #  Organisation/Client (racine de l'isolation)
    "Role",              #  Rôles RBAC (permissions)
    "User",              #  Utilisateurs du système
    
    # ==========================================================================
    #  DOCUMENT MANAGEMENT - Gestion documentaire et rapports
    # ==========================================================================
    "Document",          #  Documents uploadés (appels d'offres, etc.)
    "Chunk",             #  Fragments de document pour recherche (full-text, embeddings)
    "Proposal",          # Propositions générées à partir de documents
    "ComplianceReport",  #  Rapports de conformité (analyse automatique)
    
    # ==========================================================================
    #  COMPANY ASSETS - Ressources/Actifs de l'entreprise
    # ==========================================================================
    "CompanyAsset",      #  Ressources réutilisables (templates, policies, guidelines)
    
    # ==========================================================================
    # AUTHENTICATION & SECURITY - Auth et sécurité
    # ==========================================================================
    "AuthSession",       #  Sessions d'authentification actives (JWT)
    "LoginAttempt",      #  Tentatives de connexion (succès/échecs)
    "UserTOTP",          #  TOTP secrets for 2FA
    "AuditLog",          #  Logs d'audit (traçabilité complète)
    "APIKey",            #  Clés API pour authentification service-to-service
    
    # ==========================================================================
    #  NOTIFICATIONS - Système de notifications multi-tenant
    # ==========================================================================
    "Notification",      #  Notifications pour users/tenants
    
    # ==========================================================================
    #  EMAIL SERVICE - Système de gestion des emails asynchrones
    # ==========================================================================
    "EmailJob",          #  Queue persistante pour courriers électroniques
    "EmailJobType",      # Enum: password_reset, invitation, totp_confirmation, welcome_email
    "EmailJobStatus",    # Enum: pending, sent, failed
]


