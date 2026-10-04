from io import BytesIO

import app.models  # noqa: F401
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.database import Base, get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.image_variant import ImageVariant
from app.models.page import Page
from app.models.user import User
from app.services.file_service import file_service


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "document_upload.db"
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
def client(db_session, tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_dir))
    file_service.upload_dir = upload_dir

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


def _png_bytes(color=(255, 255, 255)):
    image = Image.new("RGB", (48, 48), color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _pdf_bytes():
    first = Image.new("RGB", (64, 64), (255, 255, 255))
    second = Image.new("RGB", (64, 64), (230, 230, 230))
    buffer = BytesIO()
    first.save(buffer, format="PDF", save_all=True, append_images=[second])
    return buffer.getvalue()


def _create_user(db_session, email="uploader@example.com", username="uploader"):
    user = User(
        email=email,
        username=username,
        password_hash=get_password_hash("StrongPass123"),
        role="user",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _headers(user):
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user.id)})}"}


def _upload_png(client, user, filename="scan.png"):
    return client.post(
        "/api/v1/documents",
        headers=_headers(user),
        data={"title": "Scan", "description": "fixture"},
        files={"file": (filename, _png_bytes(), "image/png")},
    )


def test_upload_requires_authentication(client):
    response = client.post(
        "/api/v1/documents",
        data={"title": "No auth"},
        files={"file": ("scan.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 401


def test_png_upload_creates_document_page_thumbnail_hash_and_audit(client, db_session):
    user = _create_user(db_session)

    response = _upload_png(client, user)

    assert response.status_code == 201
    document_id = response.json()["id"]

    document = db_session.get(Document, document_id)
    page = db_session.query(Page).filter(Page.document_id == document_id).one()
    actions = {row.action for row in db_session.query(AuditLog).all()}

    assert document.user_id == user.id
    assert document.file_hash != "pending"
    assert document.file_size > 0
    assert document.page_count == 1
    assert page.page_no == 1
    assert page.original_path
    assert page.thumbnail_path
    assert "document.create" in actions


def test_upload_rejects_magic_byte_spoof_and_removes_pending_record(client, db_session):
    user = _create_user(db_session)

    response = client.post(
        "/api/v1/documents",
        headers=_headers(user),
        data={"title": "Spoof"},
        files={"file": ("scan.png", b"not-a-real-png", "image/png")},
    )

    assert response.status_code == 400
    assert db_session.query(Document).count() == 0
    assert db_session.query(Page).count() == 0


def test_page_image_thumbnail_and_delete_cleanup_are_authorized(client, db_session):
    user = _create_user(db_session)
    upload_response = _upload_png(client, user)
    document_id = upload_response.json()["id"]

    pages_response = client.get(f"/api/v1/documents/{document_id}/pages", headers=_headers(user))
    image_response = client.get(f"/api/v1/documents/{document_id}/pages/1/image", headers=_headers(user))
    thumb_response = client.get(f"/api/v1/documents/{document_id}/pages/1/thumbnail", headers=_headers(user))

    assert pages_response.status_code == 200
    assert pages_response.json()["total"] == 1
    assert image_response.status_code == 200
    assert thumb_response.status_code == 200

    delete_response = client.delete(f"/api/v1/documents/{document_id}", headers=_headers(user))

    assert delete_response.status_code == 204
    assert db_session.get(Document, document_id) is None
    assert "document.delete" in {row.action for row in db_session.query(AuditLog).all()}


def test_preprocessing_variant_creates_file_db_record_and_audit(client, db_session):
    user = _create_user(db_session)
    upload_response = _upload_png(client, user)
    document_id = upload_response.json()["id"]
    page = db_session.query(Page).filter(Page.document_id == document_id).one()

    response = client.post(
        f"/api/v1/pages/{page.id}/preprocessing",
        headers=_headers(user),
        json={"profile": "temiz_baski"},
    )

    assert response.status_code == 200
    assert response.json()["parameters"]["threshold_method"] == "otsu"
    variant = db_session.get(ImageVariant, response.json()["id"])
    document = db_session.get(Document, document_id)
    actions = {row.action for row in db_session.query(AuditLog).all()}

    assert variant.page_id == page.id
    assert variant.profile == "temiz_baski"
    assert variant.parameters["threshold_method"] == "otsu"
    assert document.status == "preprocessing"
    assert "page.preprocess" in actions


def test_pdf_upload_splits_pages_in_order_and_creates_thumbnails(client, db_session):
    user = _create_user(db_session)

    response = client.post(
        "/api/v1/documents",
        headers=_headers(user),
        data={"title": "PDF Scan"},
        files={"file": ("scan.pdf", _pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 201
    document_id = response.json()["id"]
    pages = (
        db_session.query(Page)
        .filter(Page.document_id == document_id)
        .order_by(Page.page_no)
        .all()
    )

    assert response.json()["page_count"] == 2
    assert [page.page_no for page in pages] == [1, 2]
    assert all(page.original_path.endswith(f"page_{page.page_no}.png") for page in pages)
    assert all(page.thumbnail_path for page in pages)
