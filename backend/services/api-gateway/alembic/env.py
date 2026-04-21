# ==============================================================================
# ALEMBIC/ENV.PY — Configuration des Migrations de Base de Données
# ==============================================================================
#
# 🎯 RÔLE DE CE FICHIER :
#    C'est le "cerveau" d'Alembic (outil de gestion des migrations BD).
#    Il configure comment Alembic se connecte à la base de données et
#    comment il génère automatiquement les migrations.
#
# 📖 QU'EST-CE QU'ALEMBIC ?
#    Alembic = Git pour les bases de données. Versionne la structure
#    de vos tables (création, modification, suppression) de manière
#    réversible et traçable.
#
# 🔧 FONCTIONNEMENT :
#    1. Compare les modèles SQLAlchemy (code Python) vs structure BD réelle
#    2. Génère automatiquement le SQL nécessaire pour synchroniser
#    3. Exécute les migrations dans l'ordre (avec rollback possible)
#
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
#
# Pourquoi ce code est nécessaire ?
#    Alembic doit importer vos modèles Python (User, Document, etc.)
#    pour connaître la structure actuelle de vos tables.
#    Mais Alembic s'exécute depuis alembic/ et ne trouve pas le dossier app/.
#
# Solution : Ajouter le dossier parent au chemin Python
#    alembic/env.py → ../ (services/api-gateway/) → app/
#
# 📁 Structure des dossiers :
# services/api-gateway/
# ├── alembic/
# │   ├── env.py          ← Nous sommes ici
# │   ├── versions/       ← Contient les fichiers de migration
# │   └── alembic.ini     ← Configuration Alembic
# └── app/
#     ├── models/         ← Vos modèles SQLAlchemy
#     └── database.py     ← Configuration BD
# =============================================================================

# S'assurer que le dossier racine du projet est dans le chemin Python
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# =============================================================================
# CONFIGURATION ALEMBIC
# =============================================================================
#
# config = objet Alembic qui lit le fichier alembic.ini
#    - Contient les paramètres de connexion BD
#    - Contient la configuration des logs
#    - Contient les paramètres de génération de migrations
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
#
# 🎯 POURQUOI CET IMPORT EST CRUCIAL ?
#    Alembic a besoin de connaître la structure de VOS tables pour :
#    1. Détecter les changements (nouvelle table, nouvelle colonne...)
#    2. Générer automatiquement le SQL correspondant
#    3. Comparer code Python vs base de données réelle
#
# 🔧 COMMENT ÇA MARCHE ?
#    Base.metadata = catalogue complet de toutes vos tables
#    Chaque modèle hérite de Base → automatiquement référencé ici
#
# 📋 Exemples de modèles que Alembic va trouver :
#    - class User(Base) → Table users
#    - class Document(Base) → Table documents  
#    - class Tenant(Base) → Table tenants
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
#
# 🔧 POURQUOI UTILISER get_url() au lieu de coder en dur ?
#    1. Flexibilité : Différentes env (dev/test/prod) = différentes URLs
#    2. Sécurité : Ne pas exposer les credentials dans le code
#    3. Docker : Variables d'environnement facilement configurables
#
# 🏗️ FORMAT DE L'URL :
#    postgresql+psycopg://user:password@host:port/database
#    - postgresql+psycopg : driver PostgreSQL pour Python
#    - app_role : utilisateur de l'application (pas postgres !)
#    - app_secure_pwd_2026 : mot de passe sécurisé
#    - localhost:5432 : serveur PostgreSQL
#    - tenderai_db : nom de la base de données
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
#
# 🎯 QUAND UTILISER LE MODE OFFLINE ?
#    Quand vous voulez générer une migration SANS vous connecter à la BD.
#    Utile pour :
#    - Environnements de développement sans BD locale
#    - CI/CD où la BD n'est pas accessible
#    - Révision de migrations avant déploiement
#
# 🔧 COMMENT ÇA MARCHE ?
#    - literal_binds=True : Génère le SQL littéral (pas de paramètres ?)
#    - Pas de connexion réelle → juste génération de code SQL
#
# 💡 EXEMPLE D'UTILISATION :
#    alembic revision --autogenerate -m "offline_mode" --sql
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
#
# 🎯 MODE PAR DÉFAUT ET LE PLUS UTILISÉ
#    Se connecte réellement à la base de données et exécute les migrations.
#
# 🔧 ÉTAPES DU PROCESSUS :
#    1. Créer le moteur SQLAlchemy (connexion à la BD)
#    2. Se connecter à la base de données
#    3. Configurer Alembic avec la connexion active
#    4. Exécuter les migrations dans une transaction
#
# 🛡️ SÉCURITÉ :
#    - context.begin_transaction() : Tout ou rien
#    - Si une migration échoue → rollback automatique
#    - compare_type=True : Détecte les changements de type de colonnes
#    - compare_server_default=True : Détecte les changements de valeurs par défaut
#
# 💡 POOLCLASS=NullPool :
#    Pas de pool de connexions pour les migrations
#    (on ouvre, on exécute, on ferme immédiatement)
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
#
# 🎯 DÉCISION AUTOMATIQUE DU MODE
#    Alembic vérifie s'il doit s'exécuter en mode offline ou online :
#
#    - Mode offline : --sql dans la commande
#      alembic revision --autogenerate -m "migration" --sql
#
#    - Mode online : normal (par défaut)
#      alembic upgrade head
#      alembic revision --autogenerate -m "migration"
#
# 💡 99% du temps : vous utiliserez run_migrations_online()
# =============================================================================

if context.is_offline_mode():
    # Mode offline : génère le SQL sans l'exécuter
    run_migrations_offline()
else:
    # Mode online : se connecte et exécute les migrations (mode par défaut)
    run_migrations_online()
