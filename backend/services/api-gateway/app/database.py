# ==============================================================================
# DATABASE - Configuration de la connexion PostgreSQL et gestion RLS
# ==============================================================================


import os
from uuid import UUID
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# ==============================================================================
# IMPORTS DES MODÈLES
# ==============================================================================

from app.models import Base

# ==============================================================================
# DATABASE CONFIGURATION - Connexion PostgreSQL
# ==============================================================================


DATABASE_URL = os.getenv(
    "DATABASE_URL",  # Variable d'environnement (production/docker)
    # Valeur par défaut pour développement local ⬇
    "postgresql+psycopg://app_role:app_secure_pwd_2026@tenderai-postgres:5432/tenderai_db"
    #  Format : postgresql+psycopg://username:password@host:port/database_name
    # - postgresql+psycopg : Driver PostgreSQL (psycopg3, moderne)
    # - app_role : User PostgreSQL
    # - app_secure_pwd_2026 : Password
    # - tenderai-postgres : Hostname (service Docker ou localhost)
    # - 5432 : Port PostgreSQL par défaut
    # - tenderai_db : Nom de la base de données
)

# ==============================================================================
# ENGINE - Moteur de connexion à PostgreSQL
# ==============================================================================
engine = create_engine(
    DATABASE_URL,
    
    # POOL DE CONNEXIONS - Réutilise les connexions (performance)
    poolclass=QueuePool,        # Pool avec file d'attente
    pool_size=5,                # 5 connexions permanentes
    max_overflow=10,            # + 10 connexions supplémentaires si pic de charge
                                # → Maximum total = 15 connexions simultanées
    
    # HEALTH CHECK - Vérifie que la connexion est vivante
    pool_pre_ping=True,         # Envoie "SELECT 1" avant chaque utilisation
                                # Si PostgreSQL ne répond pas → nouvelle connexion
                                # Évite les erreurs "connection already closed"
    
    #  DEBUG SQL - Affiche les requêtes SQL dans les logs
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  
    # Par défaut désactivé
    # Pour activer : export SQL_ECHO=true
    # Utile en dev pour voir ce que fait SQLAlchemy
)



# ==============================================================================
#  SESSION FACTORY - Créer des sessions de base de données
# ==============================================================================
SessionLocal = sessionmaker(
    # CONTRÔLE DES TRANSACTIONS
    autocommit=False,           # Pas de commit automatique
                                # On doit appeler db.commit() explicitement
                                # Permet de faire des rollback en cas d'erreur
    
    autoflush=False,            # Pas d'envoi automatique à la DB
                                # Les changements sont envoyés au commit()
                                # Plus de contrôle, moins de requêtes
    
    bind=engine                 # Lie à notre engine PostgreSQL
)



# ==============================================================================
#  DEPENDENCY INJECTION - Session DB pour FastAPI
# ==============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency FastAPI pour obtenir une session de base de données
    
     OBJECTIF : 
    → Créer une nouvelle session pour chaque requête HTTP
    → Garantir la fermeture de la session (même en cas d'erreur)
    
     CYCLE DE VIE :
    1. Requête arrive → get_db() crée une session
    2. Route utilise la session → db.query(User).all()
    3. Réponse envoyée → finally: db.close() nettoie
    
    Usage dans FastAPI:
```python
    from fastapi import Depends
    from sqlalchemy.orm import Session
    
    @app.get("/users")
    async def list_users(db: Session = Depends(get_db)):
        # FastAPI appelle automatiquement get_db()
        # et injecte la session dans 'db'
        users = db.query(User).all()
        return users
```
    
     Avantages :
    - Pas de gestion manuelle de session
    - Nettoyage automatique
    - Code propre et DRY (Don't Repeat Yourself)
    
    Yields:
        Session: Session SQLAlchemy active
    """
    db = SessionLocal()  #  Créer une nouvelle session
    try:
        yield db          #  Donner la session à la route
                          # La route s'exécute ici
    finally:
        db.close()        #  Fermer TOUJOURS la session
                          # Libère la connexion dans le pool


# ==============================================================================
#  MULTI-TENANT RLS (Row-Level Security) - ISOLATION DES DONNÉES
# ==============================================================================

def set_tenant_context(db: Session, tenant_id: UUID) -> None:
    """
    Définit le contexte tenant pour RLS PostgreSQL
    
     RLS (Row-Level Security) ?
    → Fonctionnalité PostgreSQL qui filtre automatiquement les lignes
    → Empêche un tenant de voir les données d'un autre tenant
    → Sécurité au niveau DATABASE (pas juste application)
    
     Exemple de RLS Policy PostgreSQL :
```sql
    CREATE POLICY tenant_isolation ON documents
    USING (tenant_id::text = current_setting('app.current_tenant', true));
```
    
     WORKFLOW :
    1. User se connecte → JWT contient son tenant_id
    2. Middleware décode JWT → récupère tenant_id
    3. set_tenant_context(db, tenant_id) → définit le contexte
    4. db.query(Document).all() → RLS filtre automatiquement !
       User voit SEULEMENT ses documents
    
     Usage dans les routes :
```python
    @app.get("/documents")
    async def list_documents(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # ⬇ ÉTAPE CRUCIALE pour isolation multi-tenant
        set_tenant_context(db, current_user.tenant_id)
        
        # RLS filtre automatiquement par tenant_id
        documents = db.query(Document).all()
        return documents
```
    
     SÉCURITÉ :
    → Même si vous oubliez de filtrer par tenant_id dans Python,
      PostgreSQL le fait automatiquement (RLS policies)
    → Couche de sécurité supplémentaire au niveau DB
    → Defense in depth (défense en profondeur)
    
    Args:
        db: Session SQLAlchemy active
        tenant_id: UUID du tenant actuel (extrait du JWT)
    """
    #  Convertir UUID en string pour PostgreSQL
    # PostgreSQL custom settings acceptent seulement des strings
    
    # 🔧 SET SESSION : Définit une variable PostgreSQL pour la SESSION
    #  SESSION = valide jusqu'à la fin de la session (persiste)
    # Meilleur que SET LOCAL pour une utilisation avec SQLAlchemy
    db.execute(text(f"SET app.current_tenant = '{str(tenant_id)}'"))
    
    #  PostgreSQL peut maintenant utiliser :
    # current_setting('app.current_tenant') dans les RLS policies


# ==============================================================================
# 🏗️ UTILITAIRES DE GESTION DES TABLES
# ==============================================================================

def create_tables() -> None:
    """
    Créer toutes les tables définies dans les modèles
    
     ATTENTION : 
    → En PRODUCTION, utilisez ALEMBIC pour les migrations !
    → Cette fonction est pour DEV/PROTOTYPAGE seulement
    
     Usage (script d'initialisation) :
```python
    from app.database import create_tables
    create_tables()
```
    
    🔍 Actions effectuées :
    → Lit tous les modèles héritant de Base
    → Génère les CREATE TABLE correspondants
    → Exécute les commandes sur PostgreSQL
    
     Crée automatiquement :
    - Tables (users, tenants, documents, etc.)
    - Colonnes avec leurs types
    - Contraintes (NOT NULL, UNIQUE, etc.)
    - Index définis dans les modèles
    
     NE crée PAS :
    - RLS policies (à faire via migration Alembic)
    - Triggers (à définir dans migration)
    - Fonctions PostgreSQL custom
    - Données de test/seed
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès")


def drop_tables() -> None:
    """
    Supprimer TOUTES les tables
 

    
    🎯 Usage (tests) :
```python
    from app.database import drop_tables, create_tables
    
    def reset_database():
        drop_tables()   # Supprime tout
        create_tables() # Recrée proprement
```
    
     Alternative plus sûre :
    → Utilisez Alembic downgrade pour revenir en arrière proprement
    → Alembic garde l'historique des migrations
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️ Tables supprimées")

