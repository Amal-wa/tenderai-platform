# ==============================================================================
# app/security/__init__.py
# ==============================================================================

from .auth import (
    JWTAlgorithm,
    JWTHandler,
    get_jwt_handler,
    create_access_token,
    create_refresh_token,
    create_partial_token,
    verify_jwt_token,
)

# New unified key manager (replaces vault_manager.py + key_rotation.py)
from .auth.key_manager import (
    KeyAlgorithm,
    KeyBackend,
    EnvBackend,
    VaultBackend,
    KeyManager,
    get_key_manager,
    reset_key_manager,
    check_and_rotate_keys,
)

__all__ = [
    # JWT utilities
    "JWTAlgorithm",
    "JWTHandler",
    "get_jwt_handler",
    "create_access_token",
    "create_refresh_token",
    "create_partial_token",
    "verify_jwt_token",
    # New unified key manager
    "KeyAlgorithm",
    "KeyBackend",
    "EnvBackend",
    "VaultBackend",
    "KeyManager",
    "get_key_manager",
    "reset_key_manager",
    "check_and_rotate_keys",
]

