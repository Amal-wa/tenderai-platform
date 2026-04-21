# ==============================================================================
# ALEMBIC/ENV.PY — Configuration des Migrations de Base de Données
# ==============================================================================


from __future__ import with_statement
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# =============================================================================
# CONFIGURATION DU CHEIN D'IMPORT
# =============================================================================

# S'assurer que le dossier racine du projet est dans le chemin Python
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# =============================================================================
# CONFIGURATION ALEMBIC
# =============================================================================


# Objet de configuration Alembic (lit alembic.ini)
config = context.config

# Configuration du logging Python depuis alembic.ini
#    Affiche les logs pendant l'exécution des migrations
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# =============================================================================
# IMPORT DES MODÈLES SQLALCHEMY
# =============================================================================

try:
    # Importer tous les modèles depuis app.models
    from app.models import Base
    # target_metadata = catalogue des tables pour autogénération
    target_metadata = Base.metadata
except Exception as e:
    print(f"❌ Erreur import modèles : {e}")
    raise  # Re-lancer l'erreur pour voir le vrai problème

# =============================================================================
# CONNEXION À LA BASE DE DONNÉES
# =============================================================================
def get_url():
    """
    Récupère l'URL de la base de données depuis les variables d'environnement.
    
    Priorité :
    1. DATABASE_URL (variable d'environnement) - pour production/Docker
    2. URL par défaut - pour développement local
    
    Returns:
        str: URL de connexion PostgreSQL complète
    """
    return os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg://postgres:admin@localhost:5433/tenderaidb'
    )


# =============================================================================
# MODE OFFLINE - GÉNÉRATION SANS CONNEXION
# =============================================================================

def run_migrations_offline():
    """
    Exécute les migrations en mode 'offline' (sans connexion BD).
    
    Génère uniquement le code SQL sans l'exécuter.
    Utile pour les environnements CI/CD ou quand la BD n'est pas accessible.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # Génère SQL littéral (pas de paramètres)
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# =============================================================================
# MODE ONLINE - CONNEXION ET EXÉCUTION RÉELLE
# =============================================================================


def run_migrations_online():
    """
    Exécute les migrations en mode 'online' (avec connexion BD réelle).
    
    C'est le mode normal qui :
    1. Se connecte à la base de données
    2. Compare les modèles vs la structure actuelle
    3. Exécute les migrations nécessaires
    """
    # Récupérer la configuration depuis alembic.ini et ajouter l'URL
    configuration = config.get_section(config.config_ini_section) or {}
    configuration['sqlalchemy.url'] = get_url()

    # Créer le moteur de connexion à la base de données
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',  # Préfixe des paramètres SQLAlchemy
        poolclass=pool.NullPool,  # Pas de pool pour les migrations
    )

    # Se connecter et exécuter les migrations
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Comparer les types de colonnes
            compare_server_default=True,  # Comparer les valeurs par défaut
        )

        with context.begin_transaction():
            context.run_migrations()


# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================


if context.is_offline_mode():
    # Mode offline : génère le SQL sans l'exécuter
    run_migrations_offline()
else:
    # Mode online : se connecte et exécute les migrations (mode par défaut)
    run_migrations_online()
