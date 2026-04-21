# ==============================================================================
# MODEL: USER -  Utilisateurs du système multi-tenant
# ==============================================================================

from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import TenantModel  # ⚠️ TenantModel (car User a un tenant_id)


class User(TenantModel):  # 🏗️ Hérite de TenantModel → tenant_id, created_at, updated_at automatiques
   
    __tablename__ = "users"  # 📊 Table PostgreSQL
    
    # ==========================================================================
    # 🆔IDENTIFICATION
    # ==========================================================================
    
    id = Column(
        UUID(as_uuid=True),                 # Type UUID
        primary_key=True,                   #  Clé primaire
        default=uuid4,                      #  UUID aléatoire auto-généré
        comment="Identifiant unique (empêche énumération)"
    )
   
    
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),    # 🔗 Lien vers roles
                                                         # SET NULL = si role supprimé → role_id = NULL
        nullable=True,                                   # ✅ Optionnel
        index=True,                                      # 🚀 Index pour performance
        comment="Rôle RBAC (NULL = pas de rôle spécifique)"
    )
    #  RBAC (Role-Based Access Control) :
    
    
    # ==========================================================================
    #  AUTHENTICATION - Données de connexion
    # ==========================================================================
    
    email = Column(
        String(255),
        nullable=False,                     # OBLIGATOIRE
        index=True,                         #  Index pour recherches rapides
        comment="Email (login identifier, unique par tenant)"
    )
   
    
    hashed_password = Column(
        String(255),
        nullable=False,                     # OBLIGATOIRE
        comment="Mot de passe hashé (argon2/bcrypt) - JAMAIS plaintext"
    )
   
    
    # ==========================================================================
    #  PROFILE - Informations utilisateur
    # ==========================================================================
    
    full_name = Column(
        String(255),
        nullable=True,                      # ✅ Optionnel
        comment="Nom complet de l'utilisateur"
    )
  
    # ==========================================================================
    #  STATUS - État du compte
    # ==========================================================================
    
    is_active = Column(
        Boolean,
        nullable=False,                     # OBLIGATOIRE
        default=True,                       #  Actif par défaut
        index=True,                         #  Index (requêtes fréquentes)
        comment="Compte actif ou désactivé (soft-disable)"
    )
    
    
    is_deleted = Column(
        Boolean,
        nullable=False,                     # OBLIGATOIRE
        default=False,                      #  Non supprimé par défaut
        index=True,                         #  Index (filtrage fréquent)
        comment="Soft-delete pour audit trail (JAMAIS de hard delete)"
    )
   

    email_verified = Column(
        Boolean,
        nullable=False,                     # OBLIGATOIRE
        default=False,                      # Non vérifié par défaut
        index=True,                         # Index (filtrage fréquent)
        comment="Email vérifié via confirmation link (TTL 24h)"
    )
    
    
    # ==========================================================================
    # SECURITY AUDIT - Traçabilité
    # ==========================================================================
    
    last_login_at = Column(
        DateTime(timezone=True),            # DateTime avec timezone
        nullable=True,                      # Optionnel (NULL si jamais connecté)
        comment="Dernière connexion (NULL si jamais connecté)"
    )
    
    
    # ==========================================================================
    #  CONFIGURATION FLEXIBLE - Paramètres personnalisés
    # ==========================================================================
    
    user_metadata = Column(
        "metadata",
        JSONB,                              # JSON binaire PostgreSQL
        nullable=False,                     # Ne peut pas être NULL
        default={},                         # {} par défaut
        server_default="'{}'::jsonb",       # Valeur par défaut au niveau DB
        comment="Configuration flexible : préférences, paramètres, etc."
    )
   
    # ==========================================================================
    #  RELATIONSHIPS - Relations avec autres tables
    # ==========================================================================
    
    tenant = relationship(
        "Tenant",                           #  Tenant propriétaire
        back_populates="users",             # Bidirectionnel
        foreign_keys="[User.tenant_id]"     # Référence correcte à User.tenant_id
    )
   
    
    role = relationship(
        "Role",                            
        back_populates="users",
        foreign_keys=[role_id]
    )
   
    
    auth_sessions = relationship(
        "AuthSession",                      # Sessions actives
        back_populates="user",
        cascade="all, delete-orphan",       # Si user supprimé → sessions supprimées
        foreign_keys="AuthSession.user_id"
    )
   
    
    login_attempts = relationship(
        "LoginAttempt",                     #  Tentatives de connexion
        back_populates="user",
        foreign_keys="LoginAttempt.user_id"
    )
 
    
    audit_logs = relationship(
        "AuditLog",                         # Logs d'audit
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="AuditLog.user_id"
    )
   
    
    uploaded_documents = relationship(
        "Document",                         # Documents uploadés
        back_populates="uploaded_by_user",
        foreign_keys="Document.uploaded_by"
    )
    
    # ==========================================================================
    #  TABLE CONSTRAINTS - Contraintes au niveau table
    # ==========================================================================
    
    __table_args__ = (
        
        Index(
            'idx_users_tenant_email_unique',
            'tenant_id', 'email',
            unique=True
        ),
      
    )


