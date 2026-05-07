import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Depends
from starlette.testclient import TestClient
from fastapi.exceptions import HTTPException

from app.core.dependencies import require_permission, get_current_auth


@pytest.mark.asyncio
class TestRequirePermission:
    """
    Unit tests for require_permission() factory dependency.
    """

    @pytest.fixture
    def app(self):
        """Create FastAPI app with a test endpoint."""
        app = FastAPI()

        @app.get("/documents")
        async def list_documents(
            auth: dict = Depends(require_permission("documents:read")),
        ):
            return {"documents": [], "user_id": auth.get("user_id")}

        @app.get("/create")
        async def create_document(
            auth: dict = Depends(require_permission("documents:write")),
        ):
            return {"created": True}

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_api_key_with_required_permission_allowed(self, client):
        """
        API key with required permission should be allowed.
        """
        auth_dict = {
            "type": "api_key",
            "api_key_id": "key_123",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
            "permissions": ["documents:read", "documents:write"],
        }

        with patch(
            "app.core.dependencies.get_current_auth",
            return_value=auth_dict,
        ):
            with patch("app.core.dependencies.Depends", side_effect=lambda x: x):
                response = client.get("/documents")
                assert response.status_code == 200

    def test_jwt_auth_forbidden(self, client):
        """
        JWT-only authentication should be forbidden (API key required).
        """
        auth_dict = {
            "type": "jwt",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
        }

        with patch(
            "app.core.dependencies.get_current_auth",
            return_value=auth_dict,
        ):
            response = client.get("/documents")
            assert response.status_code == 403

    def test_api_key_missing_permission_forbidden(self, client):
        """
        API key without required permission should be forbidden.
        """
        auth_dict = {
            "type": "api_key",
            "api_key_id": "key_123",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
            "permissions": ["documents:read"],
        }

        with patch(
            "app.core.dependencies.get_current_auth",
            return_value=auth_dict,
        ):
            response = client.get("/create")
            assert response.status_code == 403

    def test_api_key_no_permissions_forbidden(self, client):
        """
        API key with empty permissions should be forbidden.
        """
        auth_dict = {
            "type": "api_key",
            "api_key_id": "key_123",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
            "permissions": [],
        }

        with patch(
            "app.core.dependencies.get_current_auth",
            return_value=auth_dict,
        ):
            response = client.get("/documents")
            assert response.status_code == 403

    def test_api_key_detail_messages(self, client):
        """
        Error responses should have correct detail messages.
        """
        jwt_auth = {
            "type": "jwt",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
        }

        with patch(
            "app.core.dependencies.get_current_auth",
            return_value=jwt_auth,
        ):
            response = client.get("/documents")
            assert response.status_code == 403
            data = response.json()
            assert "detail" in data

    @pytest.mark.asyncio
    async def test_require_permission_factory_returns_callable(self):
        """
        require_permission() should return a callable dependency function.
        """
        dependency_func = require_permission("documents:read")
        assert callable(dependency_func)

    @pytest.mark.asyncio
    async def test_require_permission_multiple_permissions(self):
        """
        API key with multiple permissions should work for any of them.
        """
        auth_dict = {
            "type": "api_key",
            "api_key_id": "key_123",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
            "permissions": [
                "documents:read",
                "documents:write",
                "proposals:read",
            ],
        }

        dep_func = require_permission("documents:read")
        result = await dep_func(auth_dict)
        assert result == auth_dict

        dep_func = require_permission("documents:write")
        result = await dep_func(auth_dict)
        assert result == auth_dict

        dep_func = await require_permission("proposals:read").__call__(auth_dict)

    @pytest.mark.asyncio
    async def test_require_permission_exact_match(self):
        """
        Permission check should be exact match, not substring.
        """
        auth_dict = {
            "type": "api_key",
            "api_key_id": "key_123",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
            "permissions": ["documents:read"],
        }

        dep_func = require_permission("documents:read:admin")
        with pytest.raises(HTTPException) as exc:
            await dep_func(auth_dict)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_api_key_required_403_error(self):
        """
        Non-API-key auth should raise 403 with correct status.
        """
        auth_dict = {
            "type": "jwt",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
        }

        dep_func = require_permission("documents:read")
        with pytest.raises(HTTPException) as exc:
            await dep_func(auth_dict)

        assert exc.value.status_code == 403
        assert "API key required" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_insufficient_permissions_403_error(self):
        """
        Missing permission should raise 403 with correct status.
        """
        auth_dict = {
            "type": "api_key",
            "api_key_id": "key_123",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
            "permissions": ["documents:read"],
        }

        dep_func = require_permission("documents:delete")
        with pytest.raises(HTTPException) as exc:
            await dep_func(auth_dict)

        assert exc.value.status_code == 403
        assert "Insufficient permissions" in str(exc.value.detail)

    @pytest.mark.asyncio
    async def test_require_permission_returns_auth_dict(self):
        """
        Successful permission check should return the auth dict.
        """
        auth_dict = {
            "type": "api_key",
            "api_key_id": "key_123",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
            "permissions": ["documents:read"],
        }

        dep_func = require_permission("documents:read")
        result = await dep_func(auth_dict)
        assert result == auth_dict
        assert result["type"] == "api_key"
        assert result["user_id"] == "user_456"

    @pytest.mark.asyncio
    async def test_missing_permissions_field_in_auth(self):
        """
        If permissions field is missing, should treat as empty list.
        """
        auth_dict = {
            "type": "api_key",
            "api_key_id": "key_123",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
        }

        dep_func = require_permission("documents:read")
        with pytest.raises(HTTPException) as exc:
            await dep_func(auth_dict)

        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_case_sensitive_permission_check(self):
        """
        Permission check should be case-sensitive.
        """
        auth_dict = {
            "type": "api_key",
            "api_key_id": "key_123",
            "user_id": "user_456",
            "tenant_id": "tenant_789",
            "permissions": ["Documents:Read"],
        }

        dep_func = require_permission("documents:read")
        with pytest.raises(HTTPException) as exc:
            await dep_func(auth_dict)

        assert exc.value.status_code == 403
