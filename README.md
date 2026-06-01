# TenderAI

> Plateforme B2B SaaS d'analyse intelligente des appels d'offres publics

TenderAI automatise l'analyse de conformité, l'évaluation des risques et la génération de recommandations structurées à partir de documents d'appels d'offres. Conçue pour les équipes qui répondent à des marchés publics, elle réduit le temps d'analyse de plusieurs jours à quelques heures.

---

## Fonctionnalités principales

- **Analyse de conformité** — vérification automatique des exigences administratives et techniques
- **Scoring de risque** — évaluation multicritères des risques contractuels
- **Gestion multi-tenant** — isolation complète des données par organisation via RLS PostgreSQL
- **Journal d'audit immuable** — traçabilité SHA-256 append-only de toutes les actions
- **Authentification renforcée** — JWT EdDSA Ed25519 + TOTP 2FA obligatoire + RBAC 6 rôles

---

## Stack technique

### Frontend
| Technologie | Usage |
|---|---|
| Next.js 14 + TypeScript 5 | App Router, RSC, SSR |
| React 18 | Composants, Context, Hooks |
| Tailwind CSS 3 | Styles |
| Framer Motion | Animations |
| Axios | Client HTTP centralisé (`lib/api.ts`) |
| React Hook Form + Zod | Formulaires et validation |

### Backend
| Technologie | Usage |
|---|---|
| FastAPI 0.115 + Python 3.11 | API REST asynchrone (ASGI) |
| PostgreSQL 15 + pgvector | Stockage relationnel, RLS, recherche vectorielle HNSW 1024-dim |
| Redis 7 | Rate limiting, sessions, cache |
| MinIO (S3-compatible) | Stockage de documents avec isolation par tenant |
| APScheduler 3.10 | Jobs planifiés (rotation clés, cleanup, emails) |
| Alembic 1.12 | Migrations de base de données |

### Sécurité & Auth
| Composant | Implémentation |
|---|---|
| JWT | EdDSA Ed25519 — NSA Suite B |
| Mots de passe | Argon2id (OWASP) |
| 2FA | TOTP RFC 6238 — obligatoire |
| Secrets | HashiCorp Vault 1.20 |
| Cookies | httpOnly + Secure + SameSite=Strict |
| Multi-tenancy | RLS PostgreSQL — isolation kernel-level |

### Observabilité
| Outil | Usage |
|---|---|
| Sentry | Error tracking + performance |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           Next.js 14 (Frontend)             │
│   Axios · httpOnly cookies · Tailwind CSS   │
└──────────────────┬──────────────────────────┘
                   │ HTTPS / REST
┌──────────────────▼──────────────────────────┐
│         FastAPI 0.115 — Port 8000           │
│                                             │
│  Middleware stack (10 couches) :            │
│  RequestId → Logging → JWT → Tenant →       │
│  RLS → RateLimit → Idempotency →            │
│  SSRF → CORS → SecurityHeaders              │
│                                             │
│  47 endpoints · RBAC 6 rôles                │
└────┬──────────┬──────────┬──────────┬───────┘
     │          │          │          │
┌────▼───┐ ┌───▼───┐ ┌────▼───┐ ┌───▼────┐
│  PG 15 │ │Redis 7│ │ MinIO  │ │ Vault  │
│pgvector│ │ Cache │ │  Docs  │ │Secrets │
│  RLS   │ │RL·Sess│ │tenants/│ │EdDSA   │
└────────┘ └───────┘ └────────┘ └────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         APScheduler (service séparé)        │
│  Key rotation · Session cleanup · Emails    │
└─────────────────────────────────────────────┘
```

---

## Middleware stack

Le pipeline de sécurité traite chaque requête HTTP à travers 10 couches dans cet ordre :

| # | Middleware | Rôle |
|---|---|---|
| 1 | `RequestIdMiddleware` | UUID v4 par requête — distributed tracing |
| 2 | `LoggingMiddleware` | Logs JSON structurés — ELK compatible |
| 3 | `JWTAuthMiddleware` | Validation signature EdDSA + révocation JTI |
| 4 | `TenantContextMiddleware` | Extraction tenant depuis JWT |
| 5 | `RLSBindMiddleware` | `SET LOCAL app.current_tenant` — isolation DB |
| 6 | `ErrorHandlerMiddleware` | Normalisation erreurs, masquage stack traces |
| 7 | `RateLimitMiddleware` | Token Bucket via Redis — 100/min auth, 10/min anon |
| 8 | `IdempotencyMiddleware` | Idempotency-Key + cache Redis 24h |
| 9 | `APIKeyMiddleware` | Validation clés API pour intégrations tierces |
| 10 | `SSRFGuardMiddleware` | Blocage RFC 1918/4193/3927 |

---

## Prérequis

- Docker Desktop 4.x+
- Docker Compose v2+
- Node.js 20+ (développement frontend)
- Python 3.11+ (développement backend)

---

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/<org>/tenderai.git
cd tenderai

# Copier les variables d'environnement
cp services/api-gateway/.env.example services/api-gateway/.env

# Éditer les variables obligatoires
# DATABASE_URL, SECRET_ENCRYPTION_KEY, SCHEDULER_SECRET, SMTP_*

# Démarrer tous les services
cd backend/infra
docker compose up -d

# Vérifier que tout est healthy
docker compose ps
```

Les migrations Alembic s'exécutent automatiquement au démarrage du container `api-gateway`.

---

## Variables d'environnement

| Variable | Description | Obligatoire |
|---|---|---|
| `DATABASE_URL` | URL PostgreSQL | Oui |
| `REDIS_URL` | URL Redis | Oui |
| `SECRET_ENCRYPTION_KEY` | Clé Fernet pour chiffrement TOTP | Oui |
| `SCHEDULER_SECRET` | Secret pour les endpoints internes du scheduler | Oui |
| `FRONTEND_URL` | URL du frontend (défaut: `http://localhost:3000`) | Non |
| `SMTP_HOST` | Serveur SMTP pour les emails | Oui |
| `SMTP_USER` | Utilisateur SMTP | Oui |
| `SMTP_PASSWORD` | Mot de passe SMTP | Oui |
| `SENTRY_DSN` | DSN Sentry (optionnel en dev) | Non |
| `USE_VAULT` | Activer HashiCorp Vault (`true`/`false`) | Non |
| `VAULT_ADDR` | URL du serveur Vault | Si USE_VAULT=true |
| `VAULT_TOKEN` | Token Vault | Si USE_VAULT=true |

---

## Structure du projet

```
tenderai/
├── frontend/                    # Next.js 14 App Router
│   ├── app/                     # Pages et layouts
│   │   ├── dashboard/           # Admin, user, analyse, audit
│   │   └── (auth)/              # Login, register, 2FA, invite
│   ├── components/              # Composants réutilisables
│   ├── hooks/                   # Custom hooks (useAuth, useAudit...)
│   ├── lib/
│   │   ├── api.ts               # Instance Axios centralisée + intercepteurs
│   │   └── validators/          # Schémas Zod partagés
│   ├── contexts/                # AuthContext
│   └── types/                   # Types TypeScript
│
├── backend/
│   ├── infra/
│   │   └── docker-compose.yml   # Orchestration dev
│   └── services/
│       ├── api-gateway/         # FastAPI — service principal
│       │   ├── app/
│       │   │   ├── main.py      # 47 endpoints
│       │   │   ├── core/
│       │   │   │   ├── middleware.py    # 10 couches middleware
│       │   │   │   ├── dependencies.py # Dépendances FastAPI
│       │   │   │   └── permissions.py  # RBAC 6 rôles / 14 permissions
│       │   │   ├── routers/     # api_keys, totp, analyse, auth_jwks
│       │   │   ├── models/      # SQLAlchemy — 13 migrations
│       │   │   ├── security/    # JWT, Argon2id, Vault
│       │   │   ├── services/    # Email, invitation, password reset
│       │   │   └── audit_service.py  # Hash chain SHA-256
│       │   └── alembic/versions/     # 13 migrations
│       └── scheduler/           # APScheduler — service séparé
│           ├── main.py
│           └── jobs.py          # Rotation clés, cleanup, emails
```

---

## Sécurité

TenderAI a été conçu avec une approche Zero-Trust et répond aux exigences suivantes :

- **OWASP Top 10 2021** — A01 à A08 couverts
- **RGPD Art. 30** — Audit logs immuables avec rétention configurable
- **RGPD Art. 32** — Chiffrement au repos et en transit
- **ISO 27001:2022** — A.8.2 RBAC + MFA, A.8.3 RLS, A.8.24 EdDSA
- **Multi-tenancy** — 7 couches d'isolation (DB kernel, application, API, cache, storage, queue, audit)

### Flux d'authentification

```
Login → JWT EdDSA (15min) + Refresh (30j) → 2FA TOTP obligatoire
     → httpOnly cookies → RLS automatique sur toutes les requêtes DB
```

---

## RBAC — Rôles et permissions

| Rôle | Description |
|---|---|
| `superadmin` | Accès total, propriétaire de l'organisation |
| `admin` | Administration complète |
| `manager` | Gestion documents, utilisateurs, propositions |
| `analyst` | Lecture, analyse, génération de rapports |
| `contributor` | Création et modification de documents |
| `viewer` | Lecture seule |

---

## Jobs planifiés

| Job | Fréquence | Description |
|---|---|---|
| Rotation clés EdDSA | Quotidien 2h UTC | Renouvellement via Vault |
| Cleanup sessions | Toutes les heures | Suppression sessions expirées |
| Traitement emails | Toutes les 30s | Batch SMTP avec retry exponentiel |

---

## Développement

```bash
# Frontend
cd frontend
npm install
npm run dev          # http://localhost:3000

# Backend (sans Docker)
cd services/api-gateway
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --port 8000

# Scheduler
cd services/scheduler
poetry run python main.py
```

### Conventions

- **Branching** : `main → dev → feature/*` avec PR obligatoire
- **Commits** : `type(scope): description` — pas d'emoji
- **Python** : type hints complets, ruff, pas de `type: ignore` sans justification
- **TypeScript** : pas de `any`, pas de `@ts-ignore`, types dans `types/`
- **HTTP** : toujours `lib/api.ts` — jamais d'import axios direct
- **Erreurs** : toujours `extractErrorMessage()` — jamais `error.message` brut

---

## Statut du projet

| Composant | Statut |
|---|---|
| Auth & JWT | Production-ready |
| Middleware stack (10 couches) | Implémenté |
| Multi-tenancy & RLS | Stable |
| Journal d'audit | Opérationnel |
| Analyse IA (RAG) | Planifié |
| OCR multilingue | Planifié |
| Prometheus + Grafana | Planifié |
| Kubernetes | Planifié |

---

## Licence

Propriétaire — usage interne uniquement.  
© 2026 TenderAI — Tous droits réservés.
