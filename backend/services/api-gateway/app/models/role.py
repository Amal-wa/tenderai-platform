# ==============================================================================
# MODEL: ROLE - Gestion des permissions et rôles (RBAC)
# ==============================================================================


from uuid import uuid4
from sqlalchemy import Column, String, Text, Boolean, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import TenantModel  


class Role(TenantModel):  # Hérite de TenantModel → aura tenant_id, created_at, updated_at
    """
    Modèle Role - RBAC (Role-Based Access Control)
    """
    
    __tablename__ = "roles"  # Table PostgreSQL
    
    # ==========================================================================
    # IDENTIFICATION
    # ==========================================================================
    
    id = Column(
        UUID(as_uuid=True),                 # Type UUID
        primary_key=True,                   # Clé primaire
        default=uuid4,                      # Génération automatique
        comment="Role ID"
    )
    
    # tenant_id est fourni par TenantModel (TenantMixin) — NE PAS redéclarer ici
    # (évite duplication de colonne lorsque l'on hérite de TenantModel)
    
    # ==========================================================================
    # INFORMATIONS DU RÔLE
    # ==========================================================================
    
    name = Column(
        String(100),                        # Limité à 100 caractères
        nullable=False,                     # OBLIGATOIRE (un rôle doit avoir un nom)
        comment="Nom du rôle: admin, user, viewer, analyst, custom_name"
    )
   
    
    description = Column(
        Text,                               # Texte illimité (contrairement à String)
        nullable=True,                      # OPTIONNEL (mais recommandé pour la documentation)
        comment="Description du rôle pour UI/documentation"
    )
  
    
    # ==========================================================================
    # PERMISSIONS - Le cœur du système RBAC
    # ==========================================================================
    
    permissions = Column(
        JSONB,
        nullable=False,
        default=[],
        server_default="'[]'::jsonb",
        comment="Permissions flat array: ['documents:read', 'admin:all', ...]"
    )
  
    
    # ==========================================================================
    # RÔLE SYSTÈME vs CUSTOM
    # ==========================================================================
    
    is_system = Column(
        Boolean,
        nullable=False,                     # OBLIGATOIRE
        default=False,                      # Par défaut = rôle custom (modifiable)
        index=True,
        comment="true = rôle système (immuable), false = custom (modifiable)"
    )
    
    # ==========================================================================
    # RELATIONSHIPS - Relations avec les autres tables
    # ==========================================================================
    
    tenant = relationship(
        "Tenant",                           #  Relation vers le Tenant
        back_populates="roles",             # Bidirectionnel : tenant.roles
        foreign_keys="[Role.tenant_id]"
    )
   
    users = relationship(
        "User",                             # Relation vers les Users
        back_populates="role",              # Bidirectionnel : user.role
        foreign_keys="User.role_id"         # Colonne de liaison dans la table users
    )
    
    
    # ==========================================================================
    #  CONTRAINTES DE TABLE
    # ==========================================================================
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_roles_tenant_name'),
        Index('ix_roles_tenant', 'tenant_id'),
        Index('ix_roles_tenant_system', 'tenant_id', 'is_system'),
        {"sqlite_autoincrement": True},
    )
    


