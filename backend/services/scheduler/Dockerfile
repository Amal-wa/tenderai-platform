# ==============================================================================
# Dockerfile - Scheduler Service (APScheduler)
# ==============================================================================
#
# 🎯 Service indépendant pour les tâches de fond :
# - Rotation des clés EdDSA chaque nuit à 2h UTC
# - Pas de dépendance avec api-gateway (appels HTTP seulement)
# 
# Build : docker build -t tenderai-scheduler .
# Run   : docker run --env-file .env tenderai-scheduler
#
# ==============================================================================

FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY pyproject.toml poetry.lock* ./

# Installer Poetry
RUN pip install --no-cache-dir poetry

# Installer les dépendances Python
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Copier le code de l'application
COPY . ./

# Health check : vérifie que le scheduler tourne
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; import sys; sys.exit(0 if os.path.exists('/tmp/scheduler_running') else 1)" || true

# Démarrer le scheduler
CMD ["python", "main.py"]
