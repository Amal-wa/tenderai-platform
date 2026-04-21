#!/usr/bin/env sh
# ==============================================================================
# scripts/init_vault.sh — Initialisation Vault OSS pour TenderAI
# ==============================================================================
# À exécuter UNE SEULE FOIS après le premier démarrage de Vault.
# Requiert : VAULT_ADDR et VAULT_TOKEN (root token) dans l'environnement.
#
# Usage :
#   docker exec -it <vault_container> sh /scripts/init_vault.sh
#   # ou en local :
#   VAULT_ADDR=http://localhost:8200 VAULT_TOKEN=dev-root-token sh scripts/init_vault.sh
# ==============================================================================

set -e

export VAULT_ADDR="${VAULT_ADDR:-http://tenderai-vault:8200}"
export VAULT_TOKEN="${VAULT_TOKEN:-dev-root-token}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " TenderAI — Vault init | addr=$VAULT_ADDR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─────────────────────────────────────────────────
# ÉTAPE 1 — Activer KV v2 (idempotent)
# ─────────────────────────────────────────────────
echo "\n[1/5] Vérification secrets engine KV v2..."

if vault secrets list | grep -q "^secret/"; then
    echo "  ✅ secret/ déjà monté — skip"
else
    vault secrets enable -version=2 -path=secret kv
    echo "  ✅ secret/ KV v2 activé"
fi

# ─────────────────────────────────────────────────
# ÉTAPE 2 — Activer AppRole auth (idempotent)
# ─────────────────────────────────────────────────
echo "\n[2/5] Vérification AppRole auth..."

if vault auth list | grep -q "^approle/"; then
    echo "  ✅ approle/ déjà activé — skip"
else
    vault auth enable approle
    echo "  ✅ approle/ activé"
fi

# ─────────────────────────────────────────────────
# ÉTAPE 3 — Policy restrictive TenderAI
# ─────────────────────────────────────────────────
echo "\n[3/5] Création policy tenderai-policy..."

vault policy write tenderai-policy - <<'EOF'
# TenderAI — accès restreint aux clés JWT et secrets d'application

# Lire et écrire les clés JWT
path "secret/data/tenderai/jwt-keys/*" {
  capabilities = ["create", "read", "update"]
}

# Lire les secrets du scheduler
path "secret/data/tenderai/scheduler" {
  capabilities = ["read"]
}

# Lire la configuration d'application
path "secret/data/tenderai/app-secrets" {
  capabilities = ["read"]
}

# Lister les métadonnées (nécessaire pour KV v2)
path "secret/metadata/tenderai/jwt-keys/*" {
  capabilities = ["read", "list"]
}

path "secret/metadata/tenderai/scheduler" {
  capabilities = ["read"]
}

path "secret/metadata/tenderai/app-secrets" {
  capabilities = ["read"]
}

# Interdit explicitement : tout le reste
EOF

echo "  ✅ Policy tenderai-policy créée"

# ─────────────────────────────────────────────────
# ÉTAPE 4 — Rôle AppRole + récupération credentials
# ─────────────────────────────────────────────────
echo "\n[4/5] Création rôle AppRole tenderai-role..."

vault write auth/approle/role/tenderai-role \
    token_policies="tenderai-policy" \
    token_ttl=1h \
    token_max_ttl=4h \
    secret_id_ttl=0   # 0 = pas d'expiration du secret_id

echo "  ✅ Rôle tenderai-role créé"

# Récupérer et afficher les credentials
ROLE_ID=$(vault read -field=role_id auth/approle/role/tenderai-role/role-id)
SECRET_ID=$(vault write -f -field=secret_id auth/approle/role/tenderai-role/secret-id)

# ─────────────────────────────────────────────────
# ÉTAPE 5 — Générer et stocker SCHEDULER_SECRET
# ─────────────────────────────────────────────────
echo "\n[5/5] Génération du secret scheduler..."

# Vérifier si le secret existe déjà
existing_secret=$(vault kv get -field=scheduler_secret secret/tenderai/scheduler 2>/dev/null || echo "")

if [ -n "$existing_secret" ]; then
    echo "  ✅ SCHEDULER_SECRET existe déjà dans Vault — skip"
    SCHEDULER_SECRET="$existing_secret"
else
    # Générer un nouveau secret sécurisé (32 bytes = 256 bits)
    SCHEDULER_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Stocker dans Vault
    vault kv put secret/tenderai/scheduler \
        scheduler_secret="$SCHEDULER_SECRET" \
        created_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    
    echo "  ✅ SCHEDULER_SECRET généré et stocké dans Vault"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✅ Vault initialisé — Credentials AppRole TenderAI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo " Ajouter dans .env (production uniquement) :"
echo ""
echo "   VAULT_ROLE_ID=$ROLE_ID"
echo "   VAULT_SECRET_ID=$SECRET_ID"
echo "   USE_VAULT=true"
echo ""
echo " ⚠️  Ne jamais commiter ces valeurs dans git."
echo "     Stocker dans Kubernetes Secrets ou CI/CD secrets."
echo ""
echo " SCHEDULER_SECRET stocké dans Vault :"
echo "   secret/tenderai/scheduler → scheduler_secret"
echo ""
echo "   L'application chargera automatiquement cette valeur"
echo "   depuis Vault au démarrage si USE_VAULT=true."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"