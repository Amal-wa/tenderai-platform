# ==============================================================================
# BASE MODEL - Classe de base pour tous les modèles SQLAlchemy
# ==============================================================================

# ==============================================================================

from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID

# ==============================================================================
#  BASE DECLARATIVE - Parent de tous les modèles SQLAlchemy
# ==============================================================================
# Tous vos modèles (User, Tenant, Document, etc.) hériteront de cette base
Base = declarative_base()


# ==============================================================================
# TIMESTAMP MIXIN - Ajoute des timestamps automatiques
# ==============================================================================
class TimestampMixin:
    """
    Mixin pour ajouter des timestamps à tous les modèles
    
    """
    
    #  DATE DE CRÉATION
    created_at = Column(
        DateTime(timezone=True),           # Type : DateTime avec fuseau horaire
        nullable=False,                     # Obligatoire
        server_default=func.now(),          # PostgreSQL remplit automatiquement
        comment="Date de création de l'enregistrement"
    )
    
    #  DATE DE DERNIÈRE MODIFICATION
    updated_at = Column(
        DateTime(timezone=True),           # Type : DateTime avec fuseau horaire
        nullable=False,                     # Obligatoire
        server_default=func.now(),          # Valeur initiale = maintenant
        onupdate=func.now(),                #  Se met à jour automatiquement lors des UPDATE
        comment="Date de dernière modification"
    )


# ==============================================================================
#  TENANT MIXIN - Support du multi-tenancy (isolation par client)
# ==============================================================================
class TenantMixin:
    """
    Mixin pour ajouter l'isolation multi-tenant

    """
    
    #  ID DU TENANT PROPRIÉTAIRE
    tenant_id = Column(
        UUID(as_uuid=True),                # Type UUID pour IDs uniques
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,                     # Obligatoire : chaque ligne appartient à un tenant
        index=True,                         # Index pour accélérer les requêtes WHERE tenant_id = X
        comment="ID du tenant propriétaire (pour isolation RLS)"
    )


# ==============================================================================
#  BASE MODEL - Modèle de base SANS multi-tenancy
# ==============================================================================
class BaseModel(Base, TimestampMixin):
    """
    Modèle de base avec timestamps uniquement
    
    
    """
    __abstract__ = True  #  Pas de table créée - juste un modèle de base
    
    #  CONVERTIR EN DICTIONNAIRE (pour les réponses API JSON)
    def to_dict(self):
        """
        Convertit l'objet SQLAlchemy en dictionnaire Python
        
         Utilité : Transformer les modèles en JSON pour l'API
        
        
         Attention : Les relations ne sont pas incluses automatiquement
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    #  REPRÉSENTATION STRING (pour le debugging)
    def __repr__(self):
        """
        Affichage lisible du modèle
        
         Utilité : Debugging et logs
        
        
        """
        pk_value = getattr(self, 'id', 'N/A')
        return f"<{self.__class__.__name__}(id={pk_value})>"


# ==============================================================================
#  TENANT MODEL - Modèle de base AVEC multi-tenancy
# ==============================================================================
class TenantModel(BaseModel, TenantMixin):
    """
    Modèle de base multi-tenant avec timestamps
    

    """
    __abstract__ = True  #  Modèle abstrait - pas de table créée


