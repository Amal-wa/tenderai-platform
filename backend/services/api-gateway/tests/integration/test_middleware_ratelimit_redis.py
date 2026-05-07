import pytest
import json
import base64
import redis
import time
from uuid import uuid4

from fastapi import FastAPI
from starlette.testclient import TestClient


def redis_available() -> bool:
    """Check if Redis is available on localhost:6379."""
    try:
        client = redis.from_url("redis://localhost:6379/1", decode_responses=True)
        client.ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not redis_available(),
    reason="Redis not reachable on localhost:6379/1",
)
pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def flush_redis_db():
    """Flush Redis db=1 before each test."""
    if redis_available():
        client = redis.from_url("redis://localhost:6379/1", decode_responses=True)
        client.flushdb()
        yield
        client.flushdb()
    else:
        yield


@pytest.mark.integration
class TestRateLimitMiddlewareIntegration:
    """
    Integration tests for RateLimitMiddleware with real Redis.
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

        from app.core.middleware import RateLimitMiddleware
        app.add_middleware(RateLimitMiddleware)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def _create_jwt_token(self, user_id: str) -> str:
        """Create a minimal JWT token for testing."""
        header = base64.urlsafe_b64encode(json.dumps({"alg": "EdDSA"}).encode()).decode().rstrip("=")
        payload = base64.urlsafe_b64encode(
            json.dumps({"sub": user_id, "tenant_id": str(uuid4())}).encode()
        ).decode().rstrip("=")
        signature = base64.urlsafe_b64encode(b"fake_signature").decode().rstrip("=")
        return f"{header}.{payload}.{signature}"

    def test_anonymous_rate_limit_10_per_60s(self, client):
        """
        Anonymous requests should be limited to 10 per 60 seconds.
        Uses real Redis db=1.
        """
        for i in range(10):
            response = client.get("/api/v1/protected")
            assert response.status_code == 200, f"Request {i+1} failed"

        response = client.get("/api/v1/protected")
        assert response.status_code == 429
        data = response.json()
        assert data["detail"] == "Rate limit exceeded"
        assert data["code"] == "RATE_LIMIT_EXCEEDED"

    def test_authenticated_rate_limit_100_per_60s(self, client):
        """
        Authenticated requests (JWT) should be limited to 100 per 60 seconds.
        Uses real Redis db=1.
        """
        user_id = str(uuid4())
        token = self._create_jwt_token(user_id)

        for i in range(100):
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200, f"Request {i+1} failed"

        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 429

    def test_different_users_separate_buckets(self, client):
        """
        Different users should have separate rate limit buckets.
        """
        user1_id = str(uuid4())
        user2_id = str(uuid4())
        token1 = self._create_jwt_token(user1_id)
        token2 = self._create_jwt_token(user2_id)

        for i in range(50):
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": f"Bearer {token1}"},
            )
            assert response.status_code == 200

        for i in range(50):
            response = client.get(
                "/api/v1/protected",
                headers={"Authorization": f"Bearer {token2}"},
            )
            assert response.status_code == 200

        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert response.status_code == 200

        response = client.get(
            "/api/v1/protected",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 200

    def test_rate_limit_reset_after_window(self, client):
        """
        Rate limit bucket should reset after 60 seconds.
        """
        for i in range(10):
            response = client.get("/api/v1/protected")
            assert response.status_code == 200

        response = client.get("/api/v1/protected")
        assert response.status_code == 429

        redis_db = redis.from_url("redis://localhost:6379/1", decode_responses=True)
        redis_db.flushdb()

        response = client.get("/api/v1/protected")
        assert response.status_code == 200

    def test_x_ratelimit_headers_present(self, client):
        """
        Rate limit headers should be present on responses.
        """
        response = client.get("/api/v1/protected")
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers
        remaining = int(response.headers["X-RateLimit-Remaining"])
        assert remaining >= 0
        assert remaining < 10

    def test_429_response_has_retry_after(self, client):
        """
        429 response should include Retry-After header.
        """
        for i in range(10):
            client.get("/api/v1/protected")

        response = client.get("/api/v1/protected")
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "60"

    def test_multiple_ips_separate_limits(self, client):
        """
        Different IP addresses should have separate rate limit buckets.
        """
        for i in range(10):
            response = client.get(
                "/api/v1/protected",
                headers={"X-Forwarded-For": "203.0.113.1"},
            )
            assert response.status_code == 200

        response = client.get(
            "/api/v1/protected",
            headers={"X-Forwarded-For": "203.0.113.1"},
        )
        assert response.status_code == 429

        response = client.get(
            "/api/v1/protected",
            headers={"X-Forwarded-For": "203.0.113.2"},
        )
        assert response.status_code == 200

    def test_token_refill_behavior(self, client):
        """
        Tokens should refill based on elapsed time in the window.
        """
        redis_db = redis.from_url("redis://localhost:6379/1", decode_responses=True)

        for i in range(5):
            response = client.get("/api/v1/protected")
            assert response.status_code == 200

        redis_db.flushdb()

        response = client.get("/api/v1/protected")
        assert response.status_code == 200
        assert int(response.headers["X-RateLimit-Remaining"]) == 9
