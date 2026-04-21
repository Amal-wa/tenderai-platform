#!/bin/bash
# ==============================================================================
# PRE-GENERATE ED25519 KEYS FOR DOCKER COMPOSE
# ==============================================================================
#
# This is OPTIONAL — keys will be auto-generated on first run anyway.
#
# This script generates Ed25519 keys and saves them as PEM files in a
# Docker volume for persistent, secure key storage (alternative to .env).
#
# Usage:
#   bash generate-keys.sh
#
# What happens:
#   1. Creates Docker volume 'api_keys' (if not exists)
#   2. Runs generate_ed25519_keys.py with --write-files in Docker
#   3. Saves keys as PEM files with proper permissions
#   4. Next: Start Docker Compose normally
#

set -e

echo "🔑 Generating EdDSA keys for api_keys Docker volume..."
echo ""

# Step 1: Create Docker volume
echo "Step 1: Creating Docker volume 'api_keys'..."
docker volume create api_keys 2>/dev/null || echo "  (volume already exists)"

# Step 2: Copy script to temporary location and run in Docker
echo "Step 2: Generating EdDSA key pair in Docker..."
docker run --rm \
  -v api_keys:/app/keys \
  -w /app \
  python:3.11-slim \
  python << 'ENDSCRIPT'
"""
Run from within Docker container:
Generate Ed25519 keys and save as PEM files.
(Extracted from scripts/generate_ed25519_keys.py)
"""

import os
import stat
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Create directory
os.makedirs('/app/keys', exist_ok=True)

# Generate keys
print("  Generating Ed25519 private key...")
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Serialize to PEM
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode()

public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()

# Save to disk with proper permissions
print("  Saving private key...")
private_file = Path('/app/keys/ed25519_private.pem')
private_file.write_text(private_pem)
os.chmod(private_file, stat.S_IRUSR | stat.S_IWUSR)  # 600

print("  Saving public key...")
public_file = Path('/app/keys/ed25519_public.pem')
public_file.write_text(public_pem)
os.chmod(public_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 644

print("\n✅ Keys generated successfully!")
print("   Private key: /app/keys/ed25519_private.pem (mode 600)")
print("   Public key:  /app/keys/ed25519_public.pem (mode 644)")
ENDSCRIPT

echo ""
echo "✅ Done! Keys are ready in the 'api_keys' Docker volume"
echo ""
echo "📌 Next step: Start Docker Compose"
echo "   cd backend/infra && docker-compose up -d"
echo ""
echo "💡 To verify keys were created:"
echo "   docker run --rm -v api_keys:/data alpine ls -la /data/"
echo ""
public_key = private_key.public_key()

# Serialize to PEM
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Save to disk
print("  Saving private key...")
with open('/app/keys/ed25519_private.pem', 'wb') as f:
    f.write(private_pem)
os.chmod('/app/keys/ed25519_private.pem', 0o600)

print("  Saving public key...")
with open('/app/keys/ed25519_public.pem', 'wb') as f:
    f.write(public_pem)
os.chmod('/app/keys/ed25519_public.pem', 0o644)

print("\n✅ Keys generated successfully!")
print("   Private key: /app/keys/ed25519_private.pem (mode 600)")
print("   Public key:  /app/keys/ed25519_public.pem (mode 644)")
EOF

echo ""
echo "✅ Done! Keys are ready in the 'api_keys' volume"
echo ""
echo "Next step: Start Docker Compose"
echo "  cd backend/infra && docker-compose up -d"
