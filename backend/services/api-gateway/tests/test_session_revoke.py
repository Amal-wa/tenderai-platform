import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.models import AuthSession


@pytest.mark.asyncio
async def test_revoke_session_success(client, test_user, auth_token, auth_session, db):
    """Successfully revoke a session"""
    other_session = AuthSession(
        id=uuid4(),
        user_id=test_user.id,
        tenant_id=test_user.tenant_id,
        jti=uuid4(),
        token_type="access",
        user_agent="Safari/537.36",
        ip_address="10.0.0.1",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=None,
        last_used_at=None
    )
    db.add(other_session)
    db.commit()
    db.refresh(other_session)
    
    response = client.delete(
        f"/api/v1/auth/sessions/{other_session.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Session révoquée avec succès"
    assert data["session_id"] == str(other_session.id)
    assert data["revoked_at"] is not None
    
    db.refresh(other_session)
    assert other_session.revoked_at is not None


@pytest.mark.asyncio
async def test_revoke_session_not_found(client, test_user, auth_token):
    """Session not found (404)"""
    response = client.delete(
        f"/api/v1/auth/sessions/{uuid4()}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404
    assert "non trouvée" in response.json()["detail"]


@pytest.mark.asyncio
async def test_revoke_current_session(client, test_user, auth_token, auth_session):
    """Cannot revoke the current session"""
    response = client.delete(
        f"/api/v1/auth/sessions/{auth_session.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    assert "logout" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_revoke_session_already_revoked(client, test_user, auth_token, db):
    """Try to revoke already-revoked session"""
    revoked_session = AuthSession(
        id=uuid4(),
        user_id=test_user.id,
        tenant_id=test_user.tenant_id,
        jti=uuid4(),
        token_type="access",
        user_agent="Chrome/120",
        ip_address="192.168.1.50",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=datetime.now(timezone.utc),
        last_used_at=None
    )
    db.add(revoked_session)
    db.commit()
    db.refresh(revoked_session)
    
    response = client.delete(
        f"/api/v1/auth/sessions/{revoked_session.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    assert "déjà révoquée" in response.json()["detail"]


@pytest.mark.asyncio
async def test_revoke_session_no_auth(client, auth_session):
    """Unauthorized access without token"""
    response = client.delete(
        f"/api/v1/auth/sessions/{auth_session.id}"
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_revoke_other_users_session(client, test_user, auth_token, db, tenant, role):
    """Cannot revoke another user's session"""
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
    
    other_session = AuthSession(
        id=uuid4(),
        user_id=other_user.id,
        tenant_id=tenant.id,
        jti=uuid4(),
        token_type="access",
        user_agent="Firefox/121",
        ip_address="203.0.113.42",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=None,
        last_used_at=None
    )
    db.add(other_session)
    db.commit()
    
    response = client.delete(
        f"/api/v1/auth/sessions/{other_session.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_revoke_session_audited(client, test_user, auth_token, auth_session, db):
    """Session revocation is logged to audit trail"""
    from app.models import AuditLog
    
    other_session = AuthSession(
        id=uuid4(),
        user_id=test_user.id,
        tenant_id=test_user.tenant_id,
        jti=uuid4(),
        token_type="access",
        user_agent="Safari/537.36",
        ip_address="10.0.0.1",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=None,
        last_used_at=None
    )
    db.add(other_session)
    db.commit()
    db.refresh(other_session)
    
    response = client.delete(
        f"/api/v1/auth/sessions/{other_session.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    
    audit_log = db.query(AuditLog).filter(
        AuditLog.action == "session.revoked",
        AuditLog.user_id == test_user.id
    ).first()
    
    assert audit_log is not None
    assert audit_log.status == "success"


@pytest.mark.asyncio
async def test_revoke_session_updates_timestamp(client, test_user, auth_token, db):
    """revoked_at timestamp is set correctly"""
    other_session = AuthSession(
        id=uuid4(),
        user_id=test_user.id,
        tenant_id=test_user.tenant_id,
        jti=uuid4(),
        token_type="access",
        user_agent="Safari/537.36",
        ip_address="10.0.0.1",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=None,
        last_used_at=None
    )
    db.add(other_session)
    db.commit()
    db.refresh(other_session)
    
    before_revoke = datetime.now(timezone.utc)
    
    response = client.delete(
        f"/api/v1/auth/sessions/{other_session.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    
    db.refresh(other_session)
    assert other_session.revoked_at is not None
    assert before_revoke <= other_session.revoked_at <= datetime.now(timezone.utc)
