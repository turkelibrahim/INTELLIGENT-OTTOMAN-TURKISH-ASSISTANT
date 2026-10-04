from datetime import timedelta

import app.models  # noqa: F401
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, get_password_hash
from app.db.database import Base, get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.user import User


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "auth_security.db"
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = testing_session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _create_user(db_session, email, username, password="StrongPass123", role="user", status="active"):
    user = User(
        email=email,
        username=username,
        password_hash=get_password_hash(password),
        role=role,
        status=status,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_header(user):
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _create_document(db_session, owner, title="Doc"):
    document = Document(
        user_id=owner.id,
        title=title,
        original_filename=f"{title}.png",
        file_hash=f"hash-{owner.id}-{title}",
        file_size=10,
        mime_type="image/png",
        page_count=1,
        status="uploaded",
        access_level="private",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


def test_register_login_me_logout_and_audit_flow(client, db_session):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "username": "alice",
            "password": "StrongPass123",
            "full_name": "Alice Example",
        },
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    assert token
    assert register_response.json()["user"]["role"] == "user"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123"},
    )
    assert login_response.status_code == 200

    headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "alice@example.com"

    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 200

    actions = {row.action for row in db_session.query(AuditLog).all()}
    assert {"user.register", "user.login", "user.logout"}.issubset(actions)


def test_invalid_login_uses_generic_error(client, db_session):
    _create_user(db_session, "bob@example.com", "bob")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "WrongPass123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "E-posta veya parola hatalı"
    assert "password_hash" not in response.text


def test_expired_or_missing_token_is_rejected(client, db_session):
    user = _create_user(db_session, "carol@example.com", "carol")
    expired_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=-1),
    )

    no_token_response = client.get("/api/v1/auth/me")
    expired_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert no_token_response.status_code == 401
    assert expired_response.status_code == 401
    assert "password_hash" not in expired_response.text


def test_document_idor_blocks_other_user_and_allows_admin(client, db_session):
    owner = _create_user(db_session, "owner@example.com", "owner")
    other = _create_user(db_session, "other@example.com", "other")
    admin = _create_user(db_session, "admin@example.com", "admin", role="admin")
    document = _create_document(db_session, owner, title="owned")

    other_response = client.get(
        f"/api/v1/documents/{document.id}",
        headers=_auth_header(other),
    )
    owner_response = client.get(
        f"/api/v1/documents/{document.id}",
        headers=_auth_header(owner),
    )
    admin_response = client.get(
        f"/api/v1/documents/{document.id}",
        headers=_auth_header(admin),
    )

    assert other_response.status_code == 403
    assert owner_response.status_code == 200
    assert admin_response.status_code == 200


def test_document_list_is_scoped_to_current_user(client, db_session):
    owner = _create_user(db_session, "dana@example.com", "dana")
    other = _create_user(db_session, "erin@example.com", "erin")
    own_doc = _create_document(db_session, owner, title="own")
    _create_document(db_session, other, title="other")

    response = client.get("/api/v1/documents", headers=_auth_header(owner))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [doc["id"] for doc in body["documents"]] == [own_doc.id]
