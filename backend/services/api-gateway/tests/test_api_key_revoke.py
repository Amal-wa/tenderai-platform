import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.models import APIKey
from app.security.api_keys import generate_api_key


@pytest.mark.asyncio
async def test_revoke_api_key_success(client, test_user, auth_token, api_key):
    """Successfully revoke an API key"""
    response = client.delete(
        f"/api/v1/api-keys/{api_key.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Clé API révoquée avec succès"
    assert data["key_id"] == str(api_key.id)
    assert data["revoked_at"] is not None


@pytest.mark.asyncio
async def test_revoke_api_key_not_found(client, test_user, auth_token):
    """API key not found (404)"""
    response = client.delete(
        f"/api/v1/api-keys/{uuid4()}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_revoke_api_key_already_revoked(client, test_user, auth_token, api_key, db):
    """Try to revoke already-revoked key"""
    api_key.revoked_at = datetime.now(timezone.utc)
    db.commit()
    
    response = client.delete(
        f"/api/v1/api-keys/{api_key.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    assert "déjà révoquée" in response.json()["detail"]


@pytest.mark.asyncio
async def test_revoke_api_key_no_auth(client, api_key):
    """Unauthorized access without token"""
    response = client.delete(
        f"/api/v1/api-keys/{api_key.id}"
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_revoke_api_key_invalid_id_format(client, test_user, auth_token):
    """Invalid UUID format"""
    response = client.delete(
        "/api/v1/api-keys/not-a-uuid",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    assert "Invalid key ID format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_revoke_api_key_audited(client, test_user, auth_token, api_key, db):
    """Key revocation is logged to audit trail"""
    from app.models import AuditLog
    
    response = client.delete(
        f"/api/v1/api-keys/{api_key.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    
    audit_log = db.query(AuditLog).filter(
        AuditLog.action == "api_key.revoked",
        AuditLog.user_id == test_user.id
    ).first()
    
    assert audit_log is not None
    assert audit_log.status == "success"


@pytest.mark.asyncio
async def test_revoke_other_users_api_key(client, test_user, auth_token, db, tenant, role):
    """Cannot revoke another user's API key"""
    from app.models import User
    
    other_user = User(
        id=uuid4(),
        tenant_id=tenant.id,
        role_id=role.id,
        email="other@example.com",
        full_name="Other User",
        hashed_password="hashed_password",
        is_active=True,
        is_deleted=False,
        email_verified=True
    )
    db.add(other_user)
    db.commit()
    
    full_key, prefix, key_hash = generate_api_key()
    other_key = APIKey(
        id=uuid4(),
        tenant_id=tenant.id,
        user_id=other_user.id,
        name="Other User's Key",
        key_prefix=prefix,
        key_hash=key_hash,
        permissions=[]
    )
    db.add(other_key)
    db.commit()
    
    response = client.delete(
        f"/api/v1/api-keys/{other_key.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_revoke_api_key_updates_timestamp(client, test_user, auth_token, api_key, db):
    """revoked_at timestamp is set correctly"""
    before_revoke = datetime.now(timezone.utc)
    
    response = client.delete(
        f"/api/v1/api-keys/{api_key.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    
    db.refresh(api_key)
    assert api_key.revoked_at is not None
    assert before_revoke <= api_key.revoked_at <= datetime.now(timezone.utc)
