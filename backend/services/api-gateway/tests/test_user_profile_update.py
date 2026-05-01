import pytest
from uuid import uuid4
from datetime import datetime, timezone
from app.models import User


@pytest.mark.asyncio
async def test_update_user_profile_success(client, test_user, auth_token):
    """Successful profile update (full_name)"""
    response = client.patch(
        "/api/v1/auth/me",
        json={"full_name": "Updated Name"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == test_user.email
    assert data["id"] == str(test_user.id)


@pytest.mark.asyncio
async def test_update_user_profile_partial(client, test_user, auth_token):
    """Update profile with only some fields"""
    response = client.patch(
        "/api/v1/auth/me",
        json={"full_name": "New Name"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "New Name"
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_update_user_profile_no_auth(client):
    """Unauthorized access without token"""
    response = client.patch(
        "/api/v1/auth/me",
        json={"full_name": "New Name"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_profile_invalid_token(client):
    """Invalid token format"""
    response = client.patch(
        "/api/v1/auth/me",
        json={"full_name": "New Name"},
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_user_profile_empty_update(client, test_user, auth_token):
    """Empty update request"""
    response = client.patch(
        "/api/v1/auth/me",
        json={},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == test_user.full_name


@pytest.mark.asyncio
async def test_update_user_profile_too_short_name(client, test_user, auth_token):
    """Name too short (less than 2 characters)"""
    response = client.patch(
        "/api/v1/auth/me",
        json={"full_name": "A"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_profile_too_long_name(client, test_user, auth_token):
    """Name too long (more than 255 characters)"""
    long_name = "A" * 256
    response = client.patch(
        "/api/v1/auth/me",
        json={"full_name": long_name},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_profile_includes_tenant(client, test_user, auth_token, tenant):
    """Response includes tenant information"""
    response = client.patch(
        "/api/v1/auth/me",
        json={"full_name": "New Name"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == str(tenant.id)
    assert data["tenant_name"] == tenant.name
    assert data["subscription_plan"] == tenant.subscription_plan
