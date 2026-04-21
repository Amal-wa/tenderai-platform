# ==============================================================================
# tests/security/test_jwt_handler.py — JWT Handler Tests
# ==============================================================================
#
# Comprehensive test suite for multi-algorithm JWT handler and key rotation.
#
# Run with: pytest tests/security/test_jwt_handler.py -v
#
# ==============================================================================

import os
import pytest
from datetime import datetime, timedelta, timezone
from jwt.exceptions import InvalidTokenError as JWTError
from pathlib import Path
import tempfile
import shutil

# Import from the JWT handler
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.security.auth.jwt_handler import (
    JWTAlgorithm,
    JWTHandler,
    create_access_token,
    create_refresh_token,
    verify_jwt_token,
)
from app.security.auth.key_manager import (
    get_key_manager,
    reset_key_manager,
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def temp_env_dir():
    """Create a temporary directory with a test .env file."""
    temp_dir = tempfile.mkdtemp()
    env_file = Path(temp_dir) / ".env"
    env_file.touch()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def original_env():
    """Save original environment variables."""
    original = {
        "JWT_ALGORITHM": os.environ.get("JWT_ALGORITHM"),
        "ED25519_PRIVATE_KEY": os.environ.get("ED25519_PRIVATE_KEY"),
        "ED25519_PUBLIC_KEY": os.environ.get("ED25519_PUBLIC_KEY"),
        "RSA_PRIVATE_KEY": os.environ.get("RSA_PRIVATE_KEY"),
        "RSA_PUBLIC_KEY": os.environ.get("RSA_PUBLIC_KEY"),
        "JWT_SECRET_KEY": os.environ.get("JWT_SECRET_KEY"),
    }
    yield
    # Restore
    for key, value in original.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


# ==============================================================================
# TEST ALGORITHM ENUM
# ==============================================================================

def test_algorithm_enum():
    """Test that JWTAlgorithm enum contains supported values."""
    assert JWTAlgorithm.EdDSA.value == "EdDSA"
    assert JWTAlgorithm.RS256.value == "RS256"
    assert JWTAlgorithm.HS256.value == "HS256"


# ==============================================================================
# TEST EDDSA ALGORITHM
# ==============================================================================

def test_eddsa_token_creation(original_env):
    """Test creating a token with EdDSA algorithm."""
    os.environ["JWT_ALGORITHM"] = "EdDSA"
    
    # Clear cached handler
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler = JWTHandler()
    token = handler.create_token(
        data={"sub": "user-123", "tenant_id": "tenant-456"},
        token_type="access"
    )
    
    assert token is not None
    assert isinstance(token, str)
    assert token.count(".") == 2  # JWT format: header.payload.signature


def test_eddsa_token_verification(original_env):
    """Test verifying an EdDSA token."""
    os.environ["JWT_ALGORITHM"] = "EdDSA"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler = JWTHandler()
    data = {"sub": "user-123", "tenant_id": "tenant-456"}
    token = handler.create_token(data, token_type="access")
    
    payload = handler.verify_token(token)
    
    assert payload["sub"] == "user-123"
    assert payload["tenant_id"] == "tenant-456"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "jti" in payload


def test_eddsa_token_expiration(original_env):
    """Test that an expired EdDSA token is rejected."""
    os.environ["JWT_ALGORITHM"] = "EdDSA"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler = JWTHandler()
    
    # Create token with negative expiration (already expired)
    token = handler.create_token(
        data={"sub": "user-123"},
        expires_delta=timedelta(seconds=-10),
        token_type="access"
    )
    
    with pytest.raises(JWTError):
        handler.verify_token(token)


# ==============================================================================
# TEST RS256 ALGORITHM
# ==============================================================================

def test_rs256_token_creation(original_env):
    """Test creating a token with RS256 algorithm."""
    os.environ["JWT_ALGORITHM"] = "RS256"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler = JWTHandler()
    token = handler.create_token(
        data={"sub": "user-123", "tenant_id": "tenant-456"},
        token_type="access"
    )
    
    assert token is not None
    assert isinstance(token, str)
    assert token.count(".") == 2


def test_rs256_token_verification(original_env):
    """Test verifying an RS256 token."""
    os.environ["JWT_ALGORITHM"] = "RS256"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler = JWTHandler()
    data = {"sub": "user-789", "tenant_id": "tenant-012"}
    token = handler.create_token(data, token_type="refresh")
    
    payload = handler.verify_token(token)
    
    assert payload["sub"] == "user-789"
    assert payload["tenant_id"] == "tenant-012"
    assert payload["type"] == "refresh"


# ==============================================================================
# TEST HS256 ALGORITHM
# ==============================================================================

def test_hs256_token_creation(original_env):
    """Test creating a token with HS256 algorithm."""
    os.environ["JWT_ALGORITHM"] = "HS256"
    os.environ["JWT_SECRET_KEY"] = "this-is-a-very-long-secret-key-with-at-least-32-characters-xyz"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler = JWTHandler()
    token = handler.create_token(
        data={"sub": "user-456", "tenant_id": "tenant-789"},
        token_type="access"
    )
    
    assert token is not None
    assert isinstance(token, str)
    assert token.count(".") == 2


def test_hs256_token_verification(original_env):
    """Test verifying an HS256 token."""
    os.environ["JWT_ALGORITHM"] = "HS256"
    os.environ["JWT_SECRET_KEY"] = "this-is-a-very-long-secret-key-with-at-least-32-characters-xyz"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler = JWTHandler()
    data = {"sub": "user-456", "tenant_id": "tenant-789"}
    token = handler.create_token(data, token_type="refresh")
    
    payload = handler.verify_token(token)
    
    assert payload["sub"] == "user-456"
    assert payload["tenant_id"] == "tenant-789"
    assert payload["type"] == "refresh"


# ==============================================================================
# TEST TOKEN TAMPERING DETECTION
# ==============================================================================

def test_tampered_token_rejected(original_env):
    """Test that a tampered token is rejected."""
    os.environ["JWT_ALGORITHM"] = "EdDSA"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler = JWTHandler()
    token = handler.create_token({"sub": "user-123"}, token_type="access")
    
    # Tamper with the token (flip a bit in the signature)
    parts = token.split(".")
    tampered_sig = "x" + parts[2][1:]  # Change first character of signature
    tampered_token = ".".join([parts[0], parts[1], tampered_sig])
    
    with pytest.raises(JWTError):
        handler.verify_token(tampered_token)


def test_wrong_algorithm_rejected(original_env):
    """Test that tokens signed with one algorithm can't verify with another."""
    os.environ["JWT_ALGORITHM"] = "EdDSA"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler_eddsa = JWTHandler()
    token = handler_eddsa.create_token({"sub": "user-123"}, token_type="access")
    
    # Switch to RS256 and try to verify EdDSA token
    os.environ["JWT_ALGORITHM"] = "RS256"
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler_rsa = JWTHandler()
    
    # Verification should fail because algorithms don't match
    with pytest.raises(JWTError):
        handler_rsa.verify_token(token)


# ==============================================================================
# TEST BACKWARD COMPATIBILITY FUNCTIONS
# ==============================================================================

def test_create_access_token_backward_compat(original_env):
    """Test backward-compatible create_access_token() function."""
    os.environ["JWT_ALGORITHM"] = "EdDSA"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    token = create_access_token({"sub": "user-123"})
    
    assert token is not None
    assert isinstance(token, str)
    
    payload = verify_jwt_token(token)
    assert payload["type"] == "access"


def test_create_refresh_token_backward_compat(original_env):
    """Test backward-compatible create_refresh_token() function."""
    os.environ["JWT_ALGORITHM"] = "EdDSA"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    token = create_refresh_token({"sub": "user-123"})
    
    assert token is not None
    assert isinstance(token, str)
    
    payload = verify_jwt_token(token)
    assert payload["type"] == "refresh"


# ==============================================================================
# TEST KEY ROTATION
# ==============================================================================

def test_key_manager_initialization():
    """Test that key_manager initializes correctly."""
    os.environ["USE_VAULT"] = "false"
    reset_key_manager()
    
    manager = get_key_manager()
    assert manager is not None
    
    keys = manager.get_current_keys()
    assert keys is not None
    assert "private_key" in keys or "public_key" in keys


def test_should_rotate_keys_no_last_rotation(original_env):
    """Test that rotation is due when no rotation date is set."""
    os.environ.pop("KEY_ROTATION_LAST_ROTATED", None)
    os.environ["VAULT_KEY_ROTATION_INTERVAL_DAYS"] = "30"
    os.environ["USE_VAULT"] = "false"
    reset_key_manager()
    
    # First call should indicate rotation is due
    manager = get_key_manager()
    result = manager.should_rotate_keys()
    assert result is True


def test_should_rotate_keys_fresh():
    """Test that rotation is not due for fresh keys."""
    # Set last rotation to today
    today = datetime.now(timezone.utc).date().isoformat()
    os.environ["KEY_ROTATION_LAST_ROTATED"] = today
    os.environ["VAULT_KEY_ROTATION_INTERVAL_DAYS"] = "30"
    os.environ["USE_VAULT"] = "false"
    reset_key_manager()
    
    manager = get_key_manager()
    result = manager.should_rotate_keys()
    assert result is False


def test_should_rotate_keys_overdue():
    """Test that rotation is due when interval has passed."""
    # Set last rotation to 40 days ago
    last_rotation = (datetime.now(timezone.utc) - timedelta(days=40)).date().isoformat()
    os.environ["KEY_ROTATION_LAST_ROTATED"] = last_rotation
    os.environ["VAULT_KEY_ROTATION_INTERVAL_DAYS"] = "30"
    os.environ["USE_VAULT"] = "false"
    reset_key_manager()
    
    manager = get_key_manager()
    result = manager.should_rotate_keys()
    assert result is True


def test_rotation_fallback_to_previous_key(original_env):
    """Test that after rotation, old tokens verify with previous key."""
    os.environ["JWT_ALGORITHM"] = "EdDSA"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    # Create token with original key
    handler_original = JWTHandler()
    token = handler_original.create_token({"sub": "user-123"}, token_type="access")
    
    # Verify with original key works
    payload = handler_original.verify_token(token)
    assert payload["sub"] == "user-123"
    
    # Simulate rotation: backup current key as previous, and create new key
    current_public = os.environ.get("ED25519_PUBLIC_KEY")
    os.environ["ED25519_PUBLIC_KEY_PREVIOUS"] = current_public
    
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    new_public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    new_private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    
    os.environ["ED25519_PRIVATE_KEY"] = new_private_pem
    os.environ["ED25519_PUBLIC_KEY"] = new_public_pem
    
    # Reload handler with new keys
    app.security.auth.jwt_handler._jwt_handler = None
    handler_rotated = JWTHandler()
    
    # Old token should still verify via fallback to previous key
    payload = handler_rotated.verify_token(token)
    assert payload["sub"] == "user-123"


# ==============================================================================
# TEST CUSTOM EXPIRY
# ==============================================================================

def test_custom_expiry_access_token(original_env):
    """Test token creation with custom expiration."""
    os.environ["JWT_ALGORITHM"] = "EdDSA"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler = JWTHandler()
    custom_delta = timedelta(hours=2)
    token = handler.create_token(
        data={"sub": "user-123"},
        expires_delta=custom_delta,
        token_type="access"
    )
    
    payload = handler.verify_token(token)
    
    # Check expiration is approximately 2 hours in the future
    now = datetime.now(timezone.utc)
    exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    delta = exp_time - now
    
    # Allow 5 second tolerance
    assert timedelta(hours=2) - timedelta(seconds=5) < delta < timedelta(hours=2) + timedelta(seconds=5)


# ==============================================================================
# TEST TOKEN CLAIMS
# ==============================================================================

def test_token_has_required_claims(original_env):
    """Test that tokens contain all required claims."""
    os.environ["JWT_ALGORITHM"] = "EdDSA"
    
    import app.security.auth.jwt_handler
    app.security.auth.jwt_handler._jwt_handler = None
    
    handler = JWTHandler()
    token = handler.create_token(
        data={"sub": "user-123", "tenant_id": "tenant-456"},
        token_type="access"
    )
    
    payload = handler.verify_token(token)
    
    # Required claims
    assert "sub" in payload
    assert "tenant_id" in payload
    assert "exp" in payload
    assert "iat" in payload
    assert "jti" in payload
    assert "type" in payload
    
    # JTI should be unique
    token2 = handler.create_token(
        data={"sub": "user-123", "tenant_id": "tenant-456"},
        token_type="access"
    )
    payload2 = handler.verify_token(token2)
    assert payload["jti"] != payload2["jti"]
