FROM python:3.11-slim

# Dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installer Poetry (version moderne)
RUN pip install --no-cache-dir "poetry>=1.8"

# Dossier de travail
WORKDIR /app

# Configurer Poetry pour installer dans l’environnement système
RUN poetry config virtualenvs.create false

# Copier uniquement les fichiers de dépendances
COPY pyproject.toml ./
COPY poetry.lock* ./

# Installer les dépendances + le projet
RUN poetry install --no-interaction --no-ansi --no-root --only main

# Copier le reste du code applicatif
COPY . .

EXPOSE 8000
