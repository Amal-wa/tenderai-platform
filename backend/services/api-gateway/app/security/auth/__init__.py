# ==============================================================================
# app/security/auth/__init__.py
# ==============================================================================


from .jwt_handler import (
    JWTAlgorithm,
    JWTHandler,
    get_jwt_handler,
    reset_jwt_handler,      
    create_access_token,
    create_refresh_token,
    create_partial_token,
    verify_jwt_token,
)

from .key_manager import (
    get_key_manager,
    reset_key_manager,
    check_and_rotate_keys,
)

# Wrapper functions for backward compatibility
def should_rotate_keys():
    """Wrapper pour vérifier si une rotation est nécessaire."""
    manager = get_key_manager()
    return manager.should_rotate_keys()

def rotate_eddsa_keys():
    """Wrapper pour effectuer la rotation des clés EdDSA."""
    manager = get_key_manager()
    return manager.rotate_keys()

def check_and_rotate_keys_on_startup():
    """Wrapper pour vérifier et effectuer une rotation au démarrage."""
    check_and_rotate_keys()

# Vault manager compatibility (delegated to key_manager)
class VaultKeyManager:
    """Compatibility wrapper — functionality moved to KeyManager."""
    pass

def get_vault_manager():
    """Compatibility wrapper — returns unified key manager."""
    return get_key_manager()

def load_keys_from_vault():
    """Compatibility wrapper."""
    manager = get_key_manager()
    return manager.get_current_keys()

def check_and_rotate_keys_on_startup_vault():
    """Compatibility wrapper."""
    check_and_rotate_keys()

__all__ = [
    # JWT Handler
    "JWTAlgorithm",
    "JWTHandler",
    "get_jwt_handler",
    "reset_jwt_handler",
    # API publique
    "create_access_token",
    "create_refresh_token",
    "create_partial_token",
    "verify_jwt_token",
    # Key Manager
    "get_key_manager",
    "reset_key_manager",
    "check_and_rotate_keys",
    # Rotation des clés (fichier)
    "should_rotate_keys",
    "rotate_eddsa_keys",
    "check_and_rotate_keys_on_startup",
    # Rotation des clés (Vault)
    "VaultKeyManager",
    "get_vault_manager",
    "load_keys_from_vault",
    "check_and_rotate_keys_on_startup_vault",
]

