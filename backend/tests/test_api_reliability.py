import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import get_current_user
from app.db.database import Base, get_db
from app.main import app
from app.models.document import Document
from app.models.user import User

@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'reliability.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = testing_session()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

from app.core.security import get_password_hash

@pytest.fixture()
def users(db_session):
    pw_hash = get_password_hash("password")
    user_a = User(
        email="user_a@example.com",
        username="user_a",
        full_name="User A",
        password_hash=pw_hash,
        status="active",
    )
    user_b = User(
        email="user_b@example.com",
        username="user_b",
        full_name="User B",
        password_hash=pw_hash,
        status="active",
    )
    db_session.add_all([user_a, user_b])
    db_session.commit()
    db_session.refresh(user_a)
    db_session.refresh(user_b)
    return user_a, user_b

def test_register_login_persistence(client):
    # Register
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test-reliability@example.com",
            "username": "test_reliability",
            "password": "Password123!",
            "full_name": "Test Reliability"
        }
    )
    assert res.status_code == 201
    
    # Login
    res = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test-reliability@example.com",
            "password": "Password123!"
        }
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    
    # Me endpoint
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "test-reliability@example.com"

def test_unauthorized_document_access(client, db_session, users):
    user_a, user_b = users
    
    # Create doc for user A
    doc = Document(
        user_id=user_a.id,
        title="Secret Doc",
        original_filename="secret.pdf",
        file_hash="hash",
        file_size=100,
        mime_type="application/pdf",
        status="uploaded"
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    
    # Login as User B
    res = client.post(
        "/api/v1/auth/login",
        json={
            "email": user_b.email,
            "password": "password"
        }
    )
    assert res.status_code == 200
    token_b = res.json()["access_token"]
    
    # Attempt to access User A's doc
    res = client.get(f"/api/v1/documents/{doc.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 403

def test_api_404_mismatch(client):
    res = client.get("/api/v1/non_existent_endpoint_for_test")
    assert res.status_code == 404
    # The detail should be structured
    assert "detail" in res.json()

def test_request_id_middleware(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert "x-request-id" in res.headers
    assert len(res.headers["x-request-id"]) > 0
