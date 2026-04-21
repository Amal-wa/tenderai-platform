#!/usr/bin/env python3
# ==============================================================================
# GENERATE ED25519 KEYS FOR JWT SIGNING
# ==============================================================================
#
# Unified script for key generation (replaces old generate_ed25519_keys.py,
# test_key_generation.py, generate-keys.sh, and generate-keys.bat).
#
# Usage:
#   python3 scripts/generate_ed25519_keys.py [OPTIONS]
#
# Options:
#   (no args)        Display keys for manual .env entry (default mode)
#   --test           Test key generation and .env writing (isolated test)
#   --write-files    Generate and save keys as PEM files in current directory
#
# Output:
#   - Default:  Keys displayed on console (copy to .env manually)
#   - --test:   Validates that keys can be generated and persist in .env
#   - --write:  Saves ed25519_private.pem and ed25519_public.pem (600/644 perms)
#

import os
import sys
import argparse
import tempfile
import shutil
import stat
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


def generate_keys_pem():
    """
    Generate Ed25519 private and public keys as PEM strings.
    
    Returns:
        tuple: (private_key_pem, public_key_pem) as strings
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    return private_pem, public_pem


def display_keys_for_env():
    """DEFAULT MODE: Display keys for manual copy-paste into .env"""
    print("\n" + "=" * 80)
    print("🔐 GENERATE ED25519 KEY PAIR FOR JWT")
    print("=" * 80)

    private_pem, public_pem = generate_keys_pem()

    print("\n✅ ED25519_PRIVATE_KEY:")
    print("-" * 80)
    print(private_pem.strip())

    print("\n✅ ED25519_PUBLIC_KEY:")
    print("-" * 80)
    print(public_pem.strip())

    print("\n" + "=" * 80)
    print("📝 ADD THESE TO YOUR .env FILE:")
    print("=" * 80)
    print(f'\nED25519_PRIVATE_KEY="{private_pem.strip()}"')
    print(f'ED25519_PUBLIC_KEY="{public_pem.strip()}"')
    print("\n⚠️  Make sure to escape newlines as \\n in your .env if needed")
    print("=" * 80 + "\n")

    return 0


def test_key_generation_and_env_writing():
    """TEST MODE: Isolated test of key generation and .env persistence"""
    print("\n" + "=" * 80)
    print("🧪 TEST ED25519 KEY GENERATION AND .env WRITING")
    print("=" * 80)

    try:
        from dotenv import set_key, load_dotenv
    except ImportError:
        print("❌ Error: python-dotenv not found")
        print("Install with: pip install python-dotenv")
        return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        env_file = tmpdir / ".env"
        
        # Create empty .env
        env_file.write_text("# Test .env file\nDATABASE_URL=test\n")
        print(f"\n📁 Test directory: {tmpdir}")
        print(f"📝 Initial .env:\n{env_file.read_text()}")

        # Generate keys
        print("\n🔄 Generating Ed25519 key pair...")
        private_pem, public_pem = generate_keys_pem()

        # Write to .env using dotenv
        print("💾 Writing keys to .env...")
        set_key(env_file, "ED25519_PRIVATE_KEY", private_pem)
        set_key(env_file, "ED25519_PUBLIC_KEY", public_pem)

        # Load and verify
        load_dotenv(env_file)
        loaded_private = os.getenv("ED25519_PRIVATE_KEY")
        loaded_public = os.getenv("ED25519_PUBLIC_KEY")

        print(f"\n✅ Loaded {len(loaded_private)} bytes of private key")
        print(f"✅ Loaded {len(loaded_public)} bytes of public key")

        # Verify keys match
        if loaded_private == private_pem and loaded_public == public_pem:
            print("\n📝 Updated .env content:")
            print(env_file.read_text())
            print("✅ TEST PASSED: Keys generated, written, and loaded successfully!\n")
            return 0
        else:
            print("\n❌ TEST FAILED: Keys do not match after write/load cycle\n")
            return 1

    return 0


def write_keys_to_files():
    """--write-files MODE: Generate and save PEM files to current directory"""
    print("\n" + "=" * 80)
    print("💾 GENERATE AND SAVE ED25519 KEY FILES")
    print("=" * 80)

    private_pem, public_pem = generate_keys_pem()

    # Determine output directory
    output_dir = Path.cwd()
    private_file = output_dir / "ed25519_private.pem"
    public_file = output_dir / "ed25519_public.pem"

    # Save private key with 600 permissions
    private_file.write_text(private_pem)
    os.chmod(private_file, stat.S_IRUSR | stat.S_IWUSR)  # 600
    print(f"\n✅ Private key saved: {private_file}")
    print(f"   Permissions: 600 (read/write for owner only)")

    # Save public key with 644 permissions
    public_file.write_text(public_pem)
    os.chmod(public_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 644
    print(f"✅ Public key saved:  {public_file}")
    print(f"   Permissions: 644 (read/write for owner, read for others)")

    print(f"\n📝 Keys are ready for use!")
    print("=" * 80 + "\n")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Ed25519 keys for JWT signing in TenderAI"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test mode: generate keys and write to temporary .env"
    )
    parser.add_argument(
        "--write-files",
        action="store_true",
        help="Write keys to PEM files (ed25519_private.pem, ed25519_public.pem)"
    )

    args = parser.parse_args()

    try:
        if args.test:
            sys.exit(test_key_generation_and_env_writing())
        elif args.write_files:
            sys.exit(write_keys_to_files())
        else:
            sys.exit(display_keys_for_env())
    except ModuleNotFoundError as e:
        print(f"❌ Error: Missing module: {e}")
        print("Install with: pip install cryptography python-dotenv")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
