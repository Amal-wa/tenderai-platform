"""
TOTP (Time-based One-Time Password) handler for 2FA.
Implements RFC 6238 using pyotp library.
"""

import pyotp
import qrcode
from io import BytesIO
import base64
import secrets
import hashlib
from typing import Tuple, List
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash


# ============================================================================
# Backup Code Hasher — Argon2id for security against brute-force attacks
# ============================================================================

_backup_code_hasher = PasswordHasher(
    time_cost=1,
    memory_cost=32768,
    parallelism=1,
    hash_len=32,
    salt_len=16
)


def _is_argon2_hash(hash_str: str) -> bool:
    """Check if hash string is Argon2id format (vs legacy SHA-256)."""
    return hash_str.startswith("$argon2")


def generate_totp_secret() -> str:
    """
    Generate a random base32 TOTP secret.
    
    Returns:
        str: Base32-encoded secret for TOTP generation
    """
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str, issuer: str = "TenderAI") -> str:
    """
    Generate otpauth:// URI for QR code.
    
    Args:
        secret: Base32-encoded TOTP secret
        email: User's email address
        issuer: Issuer name (appears in authenticator app)
        
    Returns:
        str: otpauth:// URI
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def generate_qr_code(uri: str) -> str:
    """
    Generate QR code from otpauth URI.
    
    Args:
        uri: otpauth:// URI
        
    Returns:
        str: Base64-encoded PNG image as data URI
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    img_b64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{img_b64}"


def verify_totp_code(secret: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify a 6-digit TOTP code.
    
    Args:
        secret: Base32-encoded TOTP secret
        code: 6-digit code to verify
        valid_window: Allow ±N time windows (30s each)
        
    Returns:
        bool: True if code is valid
    """
    try:
        totp = pyotp.TOTP(secret)
        # valid_window allows for clock drift
        return totp.verify(code, valid_window=valid_window)
    except Exception:
        return False


def generate_backup_codes(count: int = 10) -> List[str]:
    """
    Generate backup codes for account recovery.
    
    Args:
        count: Number of codes to generate (default 8)
        
    Returns:
        list[str]: List of backup codes in format "XXXX-XXXX"
    """
    codes = []
    for _ in range(count):
        code_part1 = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(4))
        code_part2 = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(4))
        codes.append(f"{code_part1}-{code_part2}")
    return codes


def hash_backup_code(code: str) -> str:
    """
    Hash a backup code using Argon2id (secure against brute-force attacks).
    
    MIGRATION NOTE:
    From v2.0+, all NEW backup codes use Argon2id.
    Existing SHA-256 codes (v1.x) remain valid via dual-format verification in verify_backup_code().
    Legacy codes will be automatically upgraded to Argon2id when user regenerates.
    
    Hash Format:
    - Argon2id: $argon2id$v=19$m=32768,t=1,p=1$<salt>$<hash>
    - Complexity: O(n) time, O(32MB) memory per verification → brute-force resistant
    
    Args:
        code: Backup code in format "XXXX-XXXX" (9 characters)
        
    Returns:
        str: Argon2id hash string starting with "$argon2id$"
    """
    return _backup_code_hasher.hash(code)


def verify_backup_code(code: str, hashed_codes: List[str]) -> Tuple[bool, List[str]]:
    """
    Verify a backup code against stored hashes and remove it from the list if valid.
    
    MIGRATION HANDLING (Backward Compatibility v1.x → v2.0+):
    This function handles TWO hash formats transparently:
    
    1. ARGON2ID (v2.0+):
       - Format: $argon2id$v=19$m=32768,t=1,p=1$<salt>$<hash>
       - Detection: hash.startswith("$argon2id$")
       - Verification: Use _backup_code_hasher.verify()
       - Security: O(32MB memory) per check → brute-force resistant
    
    2. SHA-256 (v1.x, legacy):
       - Format: 64-character hexadecimal string
       - Detection: Does not start with "$argon2id$"
       - Verification: Direct hex comparison
       - Security: Legacy, no salt or cost factor (vulnerable to precomputed tables)
       - Note: These codes remain functional until user regenerates backup codes
    
    Matching Logic:
    - For each stored hash, determine format and verify accordingly
    - On successful match, remove hash from list and return remaining codes
    - All subsequent logins will gradually upgrade legacy codes to Argon2id
      (user regenerates codes → new codes use Argon2id automatically)
    
    Args:
        code: Backup code to verify (format "XXXX-XXXX")
        hashed_codes: List of stored hashes (mixed v1.x SHA-256 and v2.0+ Argon2id)
        
    Returns:
        tuple[bool, list[str]]: (is_valid, remaining_codes_after_removal)
        - is_valid: True if code matched any stored hash
        - remaining_codes: List of hashes with matched code removed (or original if no match)
    """
    for stored_hash in hashed_codes:
        matched = False
        
        if _is_argon2_hash(stored_hash):
            # NEW FORMAT: Argon2id (v2.0+)
            try:
                _backup_code_hasher.verify(stored_hash, code)
                matched = True
            except (VerifyMismatchError, InvalidHash):
                matched = False
        else:
            # LEGACY FORMAT: SHA-256 (v1.x)
            legacy_hash = hashlib.sha256(code.encode()).hexdigest()
            matched = (legacy_hash == stored_hash)
        
        if matched:
            remaining = [h for h in hashed_codes if h != stored_hash]
            return True, remaining
    
    return False, hashed_codes
