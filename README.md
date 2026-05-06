<div align="center">

<img src="https://img.shields.io/badge/TenderAI-Platform-6366f1?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyTDIgN2wxMCA1IDEwLTV6TTIgMTdsOSA1IDktNXYtNmwtOS01LTkgNXoiLz48L3N2Zz4=" alt="TenderAI Platform" />

# TenderAI Platform

**Plateforme intelligente de gestion et d'analyse des appels d'offres**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

[Fonctionnalités](#-fonctionnalités) · [Architecture](#-architecture) · [Démarrage rapide](#-démarrage-rapide) · [Sécurité](#-sécurité) · [Documentation API](#-documentation-api)

</div>

---

## 🎯 Aperçu

**TenderAI Platform** est une solution complète de gestion des appels d'offres, enrichie par l'intelligence artificielle. Elle permet aux équipes de centraliser, analyser et suivre leurs dossiers d'appels d'offres grâce à une interface moderne et intuitive, une API robuste et des mécanismes de sécurité enterprise-grade.

### ✨ Pourquoi TenderAI ?

| Traditionnel | Avec TenderAI |
|---|---|
| Analyse manuelle fastidieuse | Analyse IA automatisée en quelques secondes |
| Fichiers éparpillés | Stockage centralisé & sécurisé |
| Aucune traçabilité | Audit log complet de chaque action |
| Sécurité minimale | Authentification 2FA + EdDSA + chiffrement bout-en-bout |
| Travail en silo | Gestion d'équipes et rôles granulaires |

---

## 🚀 Fonctionnalités

### 📄 Gestion des appels d'offres
- Upload et stockage sécurisé de documents (PDF, DOCX, etc.) via MinIO (S3-compatible)
- Recherche sémantique vectorielle grâce à **pgvector** + embeddings IA
- Tableau de bord de suivi avec pagination et filtres avancés

### 🤖 Analyse IA
- Génération automatique de **rapports de conformité**
- Analyse contextuelle des documents avec recherche par similarité vectorielle
- Historique complet des analyses par utilisateur

### 👥 Gestion des équipes
- Multi-tenant : isolation complète des données par organisation
- Invitations par email avec lien sécurisé
- Rôles et permissions granulaires

### 🔑 API Keys
- Génération et révocation de clés API personnelles
- Scopes configurables pour intégrations tierces

### 📬 Notifications email
- File d'attente SMTP asynchrone avec retry automatique (backoff exponentiel)
- Templates HTML : bienvenue, invitation, vérification, réinitialisation de mot de passe

### 📊 Administration
- Dashboard admin avec vue globale
- Logs d'audit complets (qui a fait quoi, quand, depuis quelle IP)
- Surveillance des tentatives de connexion

---

## 🏗 Architecture

```
tenderai-platform/
├── frontend/               # Interface Next.js 14 (TypeScript + Tailwind)
│   ├── app/
│   │   ├── (auth)/         # Login, Register, 2FA, Reset password
│   │   └── dashboard/      # Tenders, Analyse, Team, Settings, Admin
│   ├── components/         # Composants réutilisables
│   ├── hooks/              # Hooks React custom
│   └── lib/                # Clients API, utilitaires
│
└── backend/
    ├── infra/
    │   └── docker-compose.yml   # Orchestration complète
    └── services/
        ├── api-gateway/    # API FastAPI (Python 3.11)
        │   ├── app/
        │   │   ├── routers/     # Endpoints REST (auth, analyse, tenders…)
        │   │   ├── models/      # Modèles SQLAlchemy
        │   │   ├── schemas/     # Schémas Pydantic v2
        │   │   ├── services/    # Logique métier & email
        │   │   └── security/    # JWT EdDSA, 2FA TOTP, audit
        │   └── alembic/    # Migrations de base de données
        └── scheduler/      # APScheduler (Python)
            ├── jobs.py     # Key rotation, session cleanup, email processing
            └── scheduler.py
```

### Stack technologique

| Couche | Technologie |
|--------|-------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Framer Motion |
| **Backend** | FastAPI, Python 3.11, SQLAlchemy 2.0, Pydantic v2 |
| **Base de données** | PostgreSQL 15 + pgvector (recherche vectorielle) |
| **Cache** | Redis 7 |
| **Stockage fichiers** | MinIO (S3-compatible) |
| **Secrets** | HashiCorp Vault |
| **Monitoring** | Sentry |
| **Scheduler** | APScheduler |
| **Conteneurisation** | Docker + Docker Compose |

---

## ⚡ Démarrage rapide

### Prérequis

- [Docker](https://docs.docker.com/get-docker/) ≥ 24
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2.20
- [Node.js](https://nodejs.org/) ≥ 20 (pour le développement frontend)
- [Python](https://python.org/) ≥ 3.11 (pour le développement backend)

### 1. Cloner le dépôt

```bash
git clone https://github.com/Amal-wa/tenderai-platform.git
cd tenderai-platform
```

### 2. Configurer les variables d'environnement

```bash
cp backend/services/api-gateway/.env.example backend/services/api-gateway/.env
```

Éditez `.env` avec vos paramètres :

```dotenv
# Base de données
DATABASE_URL=postgresql+psycopg://postgres:admin@tenderai-postgres:5432/tenderaidb

# Sécurité
SECRET_ENCRYPTION_KEY=your-secret-key-here
SCHEDULER_SECRET=your-scheduler-secret

# Vault (optionnel)
VAULT_TOKEN=dev-root-token

# SMTP (notifications email)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=no-reply@tenderai.com
```

### 3. Lancer l'infrastructure

```bash
cd backend/infra
docker compose up -d
```

Cela démarre automatiquement :
- 🐘 PostgreSQL + pgvector sur le port `5433`
- 🔴 Redis sur le port `6379`
- 📦 MinIO sur les ports `9000` / `9001`
- 🔐 HashiCorp Vault sur le port `8200`
- 🚀 API Gateway sur le port `8000`
- ⏰ Scheduler en arrière-plan

### 4. Lancer le frontend

```bash
cd frontend
npm install
npm run dev
```

L'application est accessible sur [http://localhost:3000](http://localhost:3000) 🎉

---

## 🔐 Sécurité

TenderAI intègre des mécanismes de sécurité enterprise dès sa conception :

### Authentification & autorisation
- **JWT EdDSA (Ed25519)** — algorithme de signature asymétrique moderne, résistant aux attaques par force brute
- **Access Token** (15 min) + **Refresh Token** (7 jours) avec rotation automatique
- **2FA TOTP** — compatible Google Authenticator, Authy et toute application TOTP standard
- **Rate Limiting** — protection contre les attaques par déni de service (via SlowAPI)

### Gestion des secrets
- **HashiCorp Vault** — stockage sécurisé des clés cryptographiques
- **Rotation automatique des clés EdDSA** — planifiée par le scheduler interne
- **Chiffrement des données sensibles** au repos

### Isolation & traçabilité
- **Multi-tenant** — isolation stricte des données par organisation (row-level security)
- **Audit Log complet** — chaque action est enregistrée avec utilisateur, timestamp et IP
- **Suivi des tentatives de connexion** — détection des comportements suspects

### Sessions
- **Nettoyage automatique** — purge des sessions expirées toutes les heures
- **Invalidation immédiate** possible (logout, révocation de tokens)

---

## 📡 Documentation API

Une fois l'API Gateway démarrée, la documentation interactive est disponible :

| Interface | URL |
|-----------|-----|
| **Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| **OpenAPI JSON** | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) |

### Endpoints principaux

| Groupe | Endpoint | Description |
|--------|----------|-------------|
| **Auth** | `POST /api/v1/auth/register` | Créer un compte |
| **Auth** | `POST /api/v1/auth/login` | Connexion |
| **Auth** | `POST /api/v1/auth/2fa/setup` | Activer le 2FA |
| **Tenders** | `GET /api/v1/tenders` | Lister les appels d'offres |
| **Tenders** | `POST /api/v1/tenders` | Uploader un document |
| **Analyse** | `POST /api/v1/analyse` | Lancer une analyse IA |
| **Analyse** | `GET /api/v1/analyse/history` | Historique des analyses |
| **API Keys** | `POST /api/v1/api-keys` | Créer une clé API |

---

## 🛠 Développement

### Lancer les tests

```bash
# Backend
cd backend/services/api-gateway
poetry run pytest

# Frontend
cd frontend
npm run type-check
npm run lint
```

### Migrations de base de données

```bash
cd backend/services/api-gateway

# Créer une nouvelle migration
poetry run alembic revision --autogenerate -m "description"

# Appliquer les migrations
poetry run alembic upgrade head

# Revenir en arrière
poetry run alembic downgrade -1
```

### Services disponibles

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | — |
| **API Gateway** | http://localhost:8000 | — |
| **MinIO Console** | http://localhost:9001 | `minio` / `minio123` |
| **Vault UI** | http://localhost:8200 | Token: `dev-root-token` |
| **PostgreSQL** | localhost:5433 | `postgres` / `admin` |

---

## 📁 Structure des modèles de données

```
Tenant (organisation)
├── Users (membres avec rôles)
├── Documents (appels d'offres uploadés)
│   └── Chunks (fragments vectorisés pour la recherche IA)
├── ComplianceReports (rapports d'analyse générés)
├── Proposals (propositions liées aux tenders)
├── CompanyAssets (ressources de l'organisation)
├── ApiKeys (clés d'accès programmatique)
├── AuditLogs (traçabilité complète)
└── EmailJobs (file d'envoi asynchrone)
```

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! Pour contribuer :

1. **Forkez** le dépôt
2. Créez votre branche (`git checkout -b feature/ma-fonctionnalite`)
3. Commitez vos changements (`git commit -m 'feat: ajouter ma fonctionnalité'`)
4. Pushez la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvrez une **Pull Request**

### Convention de commits

Ce projet suit [Conventional Commits](https://www.conventionalcommits.org/) :

| Préfixe | Usage |
|---------|-------|
| `feat:` | Nouvelle fonctionnalité |
| `fix:` | Correction de bug |
| `docs:` | Documentation |
| `refactor:` | Refactoring sans changement fonctionnel |
| `test:` | Ajout ou modification de tests |
| `chore:` | Maintenance, dépendances |

---

## 📜 Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

<div align="center">

Fait avec ❤️ par l'équipe **TenderAI**

</div>
