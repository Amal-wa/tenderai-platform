# ==============================================================================
# MODEL: TENANT -  Organisation/Client dans le système multi-tenant
# ==============================================================================


from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel  # ⚠️ BaseModel, PAS TenantModel (tenant n'a pas de tenant_id)


class Tenant(BaseModel):  # Hérite de BaseModel (avec timestamps mais SANS tenant_id)
    
    
    __tablename__ = "tenants"  # Nom de la table PostgreSQL
    
    # ==========================================================================
    # IDENTIFICATION
    # ==========================================================================
    
    id = Column(
        UUID(as_uuid=True),         # Type UUID (ex: "123e4567-e89b-12d3-a456-426614174000")
        primary_key=True,           # Clé primaire
        default=uuid4,              #  Génère automatiquement un UUID aléatoire
        comment="Identifiant unique du tenant"
    )
   
    
    name = Column(
        String(255),                # Texte limité à 255 caractères
        nullable=False,             # OBLIGATOIRE
        unique=True,                #UNIQUE : un seul tenant par nom
        comment="Nom de l'organisation"
    )
    
    email = Column(
        String(255),
        nullable=False,             # OBLIGATOIRE
        unique=True,                # Un email = un seul tenant
        comment="Email principal pour notifications et contact"
    )
  
    
    # ==========================================================================
    # SUBSCRIPTION & STATUS - Gestion commerciale
    # ==========================================================================
    
    subscription_plan = Column(
        String(50),                 # Plan d'abonnement
        nullable=False,             # OBLIGATOIRE
        default="free",             
        comment="Plan: free, starter, professional, enterprise"
    )
    
    # ==========================================================================
    # REGISTRATION WIZARD FIELDS (added in migration 0009)
    # ==========================================================================
    
    sector = Column(
        String(255),
        nullable=True,
        comment="Secteur d'activité (ex: Energie, Telecom, Construction)"
    )
    
    org_size = Column(
        String(50),
        nullable=True,
        comment="Taille organisation: small, medium, large, enterprise"
    )
    
    country = Column(
        String(2),
        nullable=False,
        default="TN",
        comment="Code pays ISO 2 (ex: TN, DZ, MA)"
    )
    
    portals = Column(
        "portals",
        JSONB,
        nullable=True,
        default=[],
        server_default="'[]'::jsonb",
        comment="Liste des portals sélectionnés (JSONB array)"
    )
    
    plan = Column(
        String(100),
        nullable=False,
        default="Avancée",
        comment="Plan tarifaire: Fondements, Avancée, Entreprise"
    )
    
    billing = Column(
        String(20),
        nullable=False,
        default="annual",
        comment="Facturation: monthly ou annual"
    )
    
    trial_ends_at = Column(
        "trial_ends_at",
        DateTime(timezone=True),
        nullable=True,
        comment="Date fin essai gratuit (14 jours après création)"
    )
   
    
    is_active = Column(
        Boolean,                    # Type booléen (True/False)
        nullable=False,             # OBLIGATOIRE
        default=True,               # Par défaut = actif
        comment="Statut actif/inactif (soft-delete pattern)"
    )
   
    
    # =========================================================================
    # CONFIGURATION FLEXIBLE - JSONB pour paramètres personnalisés
    # ==========================================================================
    
    tenant_metadata = Column(
        "metadata",                        # Nom de la colonne dans la table
        JSONB,                              # Type JSON binaire PostgreSQL (indexable)
        nullable=False,                     # Ne peut pas être NULL
        default={},                         # Par défaut = dictionnaire vide
        server_default="'{}'::jsonb",       # Valeur par défaut au niveau DB
        comment="Configuration flexible: quotas, features, paramètres personnalisés"
    )
    
    # ==========================================================================
    # RELATIONSHIPS - Relations avec les autres tables
    # ==========================================================================
    # IMPORTANT : Les relationships sont pour SQLAlchemy ORM uniquement
    # Elles ne créent PAS de colonnes dans la table !
    # Elles permettent de faire : tenant.users, tenant.documents, etc.
    
    roles = relationship("Role", back_populates="tenant", foreign_keys="[Role.tenant_id]")
    # Usage : tenant.roles → Liste des rôles de ce tenant
    
    users = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",       # Si tenant supprimé → supprime ses users
        foreign_keys="User.tenant_id"
    )
    # Usage : tenant.users → Liste des utilisateurs de ce tenant
    
    documents = relationship(
        "Document",
        back_populates="tenant",
        cascade="all, delete-orphan",       # Si tenant supprimé → supprime ses documents
        foreign_keys="Document.tenant_id"
    )
    # Usage : tenant.documents → Tous les documents uploadés par ce tenant
    
    auth_sessions = relationship(
        "AuthSession",
        back_populates="tenant",
        cascade="all, delete-orphan",
        foreign_keys="AuthSession.tenant_id"
    )
    # Usage : tenant.auth_sessions → Sessions actives des utilisateurs
    # Permet de déconnecter tous les users d'un tenant si nécessaire
    
    audit_logs = relationship(
        "AuditLog",
        back_populates="tenant",
        cascade="all, delete-orphan",
        foreign_keys="AuditLog.tenant_id"
    )
    # Usage : tenant.audit_logs → Historique de TOUTES les actions
    # Essentiel pour la conformité (traçabilité complète)


