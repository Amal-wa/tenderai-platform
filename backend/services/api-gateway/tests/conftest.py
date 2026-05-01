import pytest
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.auth import get_password_hash
from app.models import User, Tenant, Role, AuthSession, APIKey
from app.database import SessionLocal, Base, engine
from app.security.api_keys import generate_api_key
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        return db
    
    from app.database import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def tenant(db):
    tenant = Tenant(
        id=uuid4(),
        name="Test Organization",
        email="org@example.com",
        subscription_plan="professional",
        is_active=True,
        tenant_metadata={"color": "#D4A84B"}
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def role(db, tenant):
    role = Role(
        id=uuid4(),
        tenant_id=tenant.id,
        name="user",
        description="Regular user",
        permissions={"documents": "read", "profile": "read"},
        is_system=False
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@pytest.fixture
def test_user(db, tenant, role):
    user = User(
        id=uuid4(),
        tenant_id=tenant.id,
        role_id=role.id,
        email="user@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("SecurePassword123"),
        is_active=True,
        is_deleted=False,
        email_verified=True,
        last_login_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(client, test_user):
    from app.security import create_access_token
    from uuid import UUID
    
    token = create_access_token(
        data={"sub": str(test_user.id), "tenant_id": str(test_user.tenant_id)},
        expires_delta=timedelta(hours=1)
    )
    return token


@pytest.fixture
def auth_session(db, test_user):
    session = AuthSession(
        id=uuid4(),
        user_id=test_user.id,
        tenant_id=test_user.tenant_id,
        jti=uuid4(),
        token_type="access",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        ip_address="192.168.1.100",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        revoked_at=None,
        last_used_at=None
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@pytest.fixture
def api_key(db, test_user):
    full_key, prefix, key_hash = generate_api_key()
    
    api_key = APIKey(
        id=uuid4(),
        tenant_id=test_user.tenant_id,
        user_id=test_user.id,
        name="Test API Key",
        key_prefix=prefix,
        key_hash=key_hash,
        permissions=["documents:read"],
        expires_at=None,
        revoked_at=None,
        last_used_at=None
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key
