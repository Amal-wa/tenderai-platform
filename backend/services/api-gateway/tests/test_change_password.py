import pytest
from app.auth import verify_password


@pytest.mark.asyncio
async def test_change_password_success(client, test_user, auth_token, db):
    """Successful password change"""
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "SecurePassword123",
            "new_password": "NewPassword456",
            "confirm_password": "NewPassword456"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Mot de passe modifié avec succès"
    
    db.refresh(test_user)
    assert verify_password("NewPassword456", test_user.hashed_password)


@pytest.mark.asyncio
async def test_change_password_incorrect_current(client, test_user, auth_token):
    """Current password incorrect"""
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "WrongPassword",
            "new_password": "NewPassword456",
            "confirm_password": "NewPassword456"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    assert "Mot de passe actuel incorrect" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_mismatch(client, test_user, auth_token):
    """New passwords don't match"""
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "SecurePassword123",
            "new_password": "NewPassword456",
            "confirm_password": "DifferentPassword"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    assert "ne correspondent pas" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_same_as_current(client, test_user, auth_token):
    """New password same as current"""
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "SecurePassword123",
            "new_password": "SecurePassword123",
            "confirm_password": "SecurePassword123"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    assert "doit être différent" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_no_auth(client):
    """Unauthorized access without token"""
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "SecurePassword123",
            "new_password": "NewPassword456",
            "confirm_password": "NewPassword456"
        }
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_too_short(client, test_user, auth_token):
    """New password too short"""
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "SecurePassword123",
            "new_password": "Short1",
            "confirm_password": "Short1"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_change_password_revokes_other_sessions(client, test_user, auth_token, db, auth_session):
    """Other sessions are revoked after password change"""
    from app.models import AuthSession
    
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "SecurePassword123",
            "new_password": "NewPassword456",
            "confirm_password": "NewPassword456"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    
    db.refresh(auth_session)
    assert auth_session.revoked_at is not None


@pytest.mark.asyncio
async def test_change_password_audited(client, test_user, auth_token, db):
    """Password change is logged to audit trail"""
    from app.models import AuditLog
    
    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "SecurePassword123",
            "new_password": "NewPassword456",
            "confirm_password": "NewPassword456"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    
    audit_log = db.query(AuditLog).filter(
        AuditLog.action == "auth.password_changed",
        AuditLog.user_id == test_user.id
    ).first()
    
    assert audit_log is not None
    assert audit_log.status == "success"
