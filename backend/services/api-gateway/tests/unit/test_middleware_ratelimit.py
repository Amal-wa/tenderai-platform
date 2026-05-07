import pytest
import json
import base64
from time import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import FastAPI
from starlette.testclient import TestClient
from starlette.responses import JSONResponse

from app.core.middleware import RateLimitMiddleware, JWT_PUBLIC_PATHS


@pytest.mark.asyncio
class TestRateLimitMiddleware:
    """
    Unit tests for RateLimitMiddleware with mocked Redis.
    """

    @pytest.fixture
    def app(self):
        """Create a minimal FastAPI app for testing."""
        app = FastAPI()

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        @app.get("/api/v1/protected")
        async def protected():
            return {"message": "success"}

        app.add_middleware(RateLimitMiddleware)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def _create_jwt_token(self, user_id: str) -> str:
        """
        Create a minimal JWT token for testing.
        Format: header.payload.signature (no signature verification needed)
        """
        header = base64.urlsafe_b64encode(json.dumps({"alg": "EdDSA"}).encode()).decode().rstrip("=")
        payload = base64.urlsafe_b64encode(
            json.dumps({"sub": user_id, "tenant_id": str(uuid4())}).encode()
        ).decode().rstrip("=")
        signature = base64.urlsafe_b64encode(b"fake_signature").decode().rstrip("=")
        return f"{header}.{payload}.{signature}"

    @patch("app.core.middleware._get_redis_client")
    def test_exempt_path_health_no_redis_call(self, mock_get_redis, client):
        """Exempt paths should never call Redis."""
        mock_get_redis.return_value = MagicMock()

        response = client.get("/health")

        assert response.status_code == 200
        mock_get_redis.assert_not_called()

    @patch("app.core.middleware._get_redis_client")
    def test_anonymous_limit_10_requests(self, mock_get_redis, client):
        """
        Anonymous (IP-based) rate limit: 429 after 10 requests.
        """
        mock_redis = MagicMock()

        def lua_script_side_effect(script, num_keys, *args):
            limit = args[2]
            refill_rate = args[3]
            now = args[4]

            key_tokens = f"{args[0]}:tokens"
            key_last = f"{args[1]}:last"

            current_tokens = float(mock_redis.get(key_tokens) or limit)
            last_refill = float(mock_redis.get(key_last) or now)

            elapsed = now - last_refill
            refill_amount = (elapsed / refill_rate) * limit
            current_tokens = min(limit, current_tokens + refill_amount)
            last_refill = now

            if current_tokens >= 1:
                current_tokens -= 1
                mock_redis.set(key_tokens, str(current_tokens))
                mock_redis.set(key_last, str(last_refill))
                return [1, current_tokens]
            else:
                mock_redis.set(key_tokens, str(current_tokens))
                mock_redis.set(key_last, str(last_refill))
                return [0, 0]

        mock_redis.eval = lua_script_side_effect
        mock_get_redis.return_value = mock_redis

        for i in range(10):
            response = client.get("/api/v1/protected")
            assert response.status_code == 200
            assert "X-RateLimit-Remaining" in response.headers

        response = client.get("/api/v1/protected")
        assert response.status_code == 429
        assert response.json() == {
            "detail": "Rate limit exceeded",
            "code": "RATE_LIMIT_EXCEEDED",
        }
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert "X-RateLimit-Reset" in response.headers
        assert "Retry-After" in response.headers

    @patch("app.core.middleware._get_redis_client")
    def test_authenticated_limit_100_requests(self, mock_get_redis, client):
        """
        Authenticated (user_id-based) rate limit: 429 after 100 requests.
        """
        mock_redis = MagicMock()
        user_id = str(uuid4())
        token = self._create_jwt_token(user_id)

        def lua_script_side_effect(script, num_keys, *args):
            limit = args[2]
            refill_rate = args[3]
            now = args[4]

            key_tokens = f"{args[0]}:tokens"
            key_last = f"{args[1]}:last"

            current_tokens = float(mock_redis.get(key_tokens) or limit)
            last_refill = float(mock_redis.get(key_last) or now)

            elapsed = now - last_refill
            refill_amount = (elapsed / refill_rate) * limit
            current_tokens = min(limit, current_tokens + refill_amount)
            last_refill = now

            if current_tokens >= 1:
                current_tokens -= 1
                mock_redis.set(key_tokens, str(current_tokens))
                mock_redis.set(key_last, str(last_refill))
                return [1, current_tokens]
            else:
                mock_redis.set(key_tokens, str(current_tokens))
                mock_redis.set(key_last, str(last_refill))
                return [0, 0]

        mock_redis.eval = lua_script_side_effect
        mock_get_redis.return_value = mock_redis

        for i in range(100):
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200

        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 429
        assert response.json()["code"] == "RATE_LIMIT_EXCEEDED"

    @patch("app.core.middleware._get_redis_client")
    def test_rate_limit_429_response_body(self, mock_get_redis, client):
        """
        429 response body should have correct structure with code field.
        """
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [0, 0]
        mock_get_redis.return_value = mock_redis

        response = client.get("/api/v1/protected")

        assert response.status_code == 429
        data = response.json()
        assert data["detail"] == "Rate limit exceeded"
        assert data["code"] == "RATE_LIMIT_EXCEEDED"

    @patch("app.core.middleware._get_redis_client")
    def test_allowed_response_has_ratelimit_remaining_header(self, mock_get_redis, client):
        """
        Allowed responses should include X-RateLimit-Remaining header.
        """
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [1, 95]
        mock_get_redis.return_value = mock_redis

        response = client.get("/api/v1/protected")

        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers
        assert int(response.headers["X-RateLimit-Remaining"]) >= 0
        assert response.headers["X-RateLimit-Remaining"] == "95"

    @patch("app.core.middleware._get_redis_client")
    def test_redis_failure_fails_open(self, mock_get_redis, client):
        """
        Redis connection failure should pass request through (fail-open).
        """
        mock_get_redis.side_effect = Exception("Redis connection error")

        response = client.get("/api/v1/protected")

        assert response.status_code == 200

    @patch("app.core.middleware._get_redis_client")
    def test_redis_none_fails_open(self, mock_get_redis, client):
        """
        If _get_redis_client returns None, middleware should pass through.
        """
        mock_get_redis.return_value = None

        response = client.get("/api/v1/protected")

        assert response.status_code == 200

    @patch("app.core.middleware._get_redis_client")
    def test_lua_script_failure_fails_open(self, mock_get_redis, client):
        """
        Redis Lua script failure should pass request through.
        """
        mock_redis = MagicMock()
        mock_redis.eval.side_effect = Exception("Lua script error")
        mock_get_redis.return_value = mock_redis

        response = client.get("/api/v1/protected")

        assert response.status_code == 200

    @patch("app.core.middleware._get_redis_client")
    def test_x_forwarded_for_header_used_for_ip(self, mock_get_redis, client):
        """
        X-Forwarded-For header should be used to extract client IP.
        """
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [1, 9]
        mock_get_redis.return_value = mock_redis

        response = client.get(
            "/api/v1/protected",
            headers={"X-Forwarded-For": "203.0.113.1, 198.51.100.2"},
        )

        assert response.status_code == 200
        called_with = mock_redis.eval.call_args[0]
        assert "ip:203.0.113.1" in called_with[2]

    @patch("app.core.middleware._get_redis_client")
    def test_rate_limit_headers_on_429(self, mock_get_redis, client):
        """
        429 response should have X-RateLimit-Reset, X-RateLimit-Remaining,
        and Retry-After headers.
        """
        mock_redis = MagicMock()
        mock_redis.eval.return_value = [0, 0]
        mock_get_redis.return_value = mock_redis

        response = client.get("/api/v1/protected")

        assert response.status_code == 429
        assert "X-RateLimit-Reset" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "Retry-After" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.headers["Retry-After"] == "60"

        reset_time = int(response.headers["X-RateLimit-Reset"])
        assert reset_time > int(time())

    @patch("app.core.middleware._get_redis_client")
    def test_multiple_requests_same_user_consume_tokens(self, mock_get_redis, client):
        """
        Multiple requests from same user should consume tokens properly.
        """
        mock_redis = MagicMock()
        user_id = str(uuid4())
        token = self._create_jwt_token(user_id)

        token_state = {"tokens": 100}

        def lua_script_side_effect(script, num_keys, *args):
            if token_state["tokens"] >= 1:
                token_state["tokens"] -= 1
                return [1, token_state["tokens"]]
            return [0, 0]

        mock_redis.eval = lua_script_side_effect
        mock_get_redis.return_value = mock_redis

        for i in range(5):
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            remaining = int(response.headers["X-RateLimit-Remaining"])
            assert remaining == 100 - (i + 1)

    @patch("app.core.middleware._get_redis_client")
    def test_malformed_jwt_falls_back_to_ip_limit(self, mock_get_redis, client):
        """
        Malformed JWT should be ignored, fall back to IP-based limit (10 tokens).
        """
        mock_redis = MagicMock()

        def lua_script_side_effect(script, num_keys, *args):
            limit = args[2]
            assert limit == 10, "Malformed JWT should use anonymous limit"
            return [1, limit - 1]

        mock_redis.eval = lua_script_side_effect
        mock_get_redis.return_value = mock_redis

        malformed_token = "invalid.token"
        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {malformed_token}"},
        )

        assert response.status_code == 200

    @patch("app.core.middleware._get_redis_client")
    def test_empty_bearer_header_uses_ip_limit(self, mock_get_redis, client):
        """
        Empty Authorization header should use IP-based limit.
        """
        mock_redis = MagicMock()

        def lua_script_side_effect(script, num_keys, *args):
            limit = args[2]
            assert limit == 10, "Empty bearer should use anonymous limit"
            return [1, limit - 1]

        mock_redis.eval = lua_script_side_effect
        mock_get_redis.return_value = mock_redis

        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": "Bearer "},
        )

        assert response.status_code == 200

    @patch("app.core.middleware._get_redis_client")
    def test_jwt_public_paths_exempt(self, mock_get_redis, client):
        """
        Routes in JWT_PUBLIC_PATHS should be exempt from rate limiting.
        """
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        for path in JWT_PUBLIC_PATHS:
            if path == "/health":
                response = client.get(path)
                assert response.status_code == 200
                mock_get_redis.assert_not_called()
