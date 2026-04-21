"""
Centralized cookie security configuration for FastAPI.

Ensures all auth cookies (access_token, refresh_token) are set with consistent
security flags: httponly=True, secure=IS_PRODUCTION, samesite="strict", path="/"
"""
import os
from fastapi.responses import JSONResponse

# Read environment once at module load (not per-request for performance)
IS_PRODUCTION = os.getenv("APP_ENV") == "production"


def _set_cookie(
    response: JSONResponse,
    key: str,
    value: str,
    max_age: int,
) -> None:
    """
    Private helper to set a single auth cookie with standardized security flags.
    
    Args:
        response: FastAPI JSONResponse object
        key: Cookie name ("access_token" or "refresh_token")
        value: Cookie value (JWT token or empty string for deletion)
        max_age: Cookie lifetime in seconds (0 for deletion, 900 for access, 604800 for refresh)
    """
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="strict",
        max_age=max_age,
        path="/"
    )


def set_auth_cookies(
    response: JSONResponse,
    access_token: str,
    refresh_token: str,
) -> None:
    """
    Set both access_token and refresh_token cookies with standardized security flags.
    
    **Security Flags**:
    - httponly=True: Prevents JavaScript access (blocks XSS token theft)
    - secure={IS_PRODUCTION}: Sent only over HTTPS in production
    - samesite="strict": Prevents cross-site request forgery (CSRF)
    - path="/": Available to all application paths
    
    **Token Lifetimes**:
    - access_token: 900 seconds (15 minutes) — short-lived for security
    - refresh_token: 604800 seconds (7 days) — long-lived for user convenience
    
    Args:
        response: FastAPI JSONResponse object
        access_token: Signed JWT access token
        refresh_token: Signed JWT refresh token
    """
    _set_cookie(response, "access_token", access_token, max_age=900)
    _set_cookie(response, "refresh_token", refresh_token, max_age=604800)


def delete_auth_cookies(response: JSONResponse) -> None:
    """
    Delete both access_token and refresh_token cookies by setting them to empty
    values with max_age=0.
    
    **Why not use FastAPI's delete_cookie()?**
    FastAPI's delete_cookie() does not support the `secure` parameter, which means
    the deletion instruction could be sent over HTTP if secure was conditional.
    By using set_cookie with empty value and max_age=0, we ensure the deletion
    instruction respects the same security flags as the original cookies.
    
    Args:
        response: FastAPI JSONResponse object
    """
    _set_cookie(response, "access_token", "", max_age=0)
    _set_cookie(response, "refresh_token", "", max_age=0)
