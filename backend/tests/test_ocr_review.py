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
from app.models.page import Page
from app.models.processing_outputs import OCRResult, TextVersion
from app.models.user import User


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "ocr_review.db"
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


def _user(db_session, email, username, role="user"):
    user = User(
        email=email,
        username=username,
        password_hash=get_password_hash("StrongPass123"),
        role=role,
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _headers(user):
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user.id)})}"}


def _document_page_and_ocr(db_session, owner):
    document = Document(
        user_id=owner.id,
        title="Review Doc",
        original_filename="review.png",
        file_hash="hash-review",
        file_size=12,
        mime_type="image/png",
        page_count=1,
        status="ocr_review",
        access_level="private",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    page = Page(document_id=document.id, page_no=1, original_path="review.png", status="ocr_review")
    db_session.add(page)
    db_session.commit()
    db_session.refresh(page)

    high = OCRResult(
        page_id=page.id,
        line_no=1,
        bbox={"x": 10, "y": 10, "w": 80, "h": 12},
        raw_text="خام متن",
        confidence_score=0.92,
    )
    low = OCRResult(
        page_id=page.id,
        line_no=2,
        bbox={"x": 12, "y": 30, "w": 82, "h": 12},
        raw_text="کم اعتماد",
        confidence_score=0.42,
    )
    db_session.add_all([high, low])
    db_session.commit()
    db_session.refresh(high)
    db_session.refresh(low)
    return document, page, high, low


def test_review_lines_are_scoped_and_low_confidence_filter_works(client, db_session):
    owner = _user(db_session, "owner-review@example.com", "ownerreview")
    other = _user(db_session, "other-review@example.com", "otherreview")
    _, page, high, low = _document_page_and_ocr(db_session, owner)

    denied = client.get(f"/api/v1/ocr-review/pages/{page.id}/lines", headers=_headers(other))
    all_lines = client.get(f"/api/v1/ocr-review/pages/{page.id}/lines", headers=_headers(owner))
    low_lines = client.get(
        f"/api/v1/ocr-review/pages/{page.id}/lines?low_confidence_only=true&threshold=0.75",
        headers=_headers(owner),
    )

    assert denied.status_code == 403
    assert all_lines.status_code == 200
    assert [line["id"] for line in all_lines.json()] == [high.id, low.id]
    assert low_lines.status_code == 200
    assert [line["id"] for line in low_lines.json()] == [low.id]


def test_correction_preserves_raw_ocr_and_creates_text_version_and_audit(client, db_session):
    owner = _user(db_session, "corrector@example.com", "corrector")
    _, _, raw_ocr, _ = _document_page_and_ocr(db_session, owner)

    response = client.post(
        f"/api/v1/ocr-review/ocr-results/{raw_ocr.id}/corrections",
        headers=_headers(owner),
        json={"text": "صحیح متن"},
    )

    assert response.status_code == 201
    body = response.json()
    db_session.refresh(raw_ocr)
    version = db_session.get(TextVersion, body["id"])
    audit = db_session.query(AuditLog).filter(AuditLog.action == "ocr.correction.create").one()

    assert raw_ocr.raw_text == "خام متن"
    assert version.version_type == "ocr_correction"
    assert version.text == "صحیح متن"
    assert version.previous_text == "خام متن"
    assert audit.object_type == "text_version"
    assert "صحیح متن" in audit.new_value


def test_second_correction_keeps_correction_history(client, db_session):
    owner = _user(db_session, "history@example.com", "history")
    _, _, raw_ocr, _ = _document_page_and_ocr(db_session, owner)

    first = client.post(
        f"/api/v1/ocr-review/ocr-results/{raw_ocr.id}/corrections",
        headers=_headers(owner),
        json={"text": "first correction"},
    )
    second = client.post(
        f"/api/v1/ocr-review/ocr-results/{raw_ocr.id}/corrections",
        headers=_headers(owner),
        json={"text": "second correction"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    versions = (
        db_session.query(TextVersion)
        .filter(TextVersion.ocr_result_id == raw_ocr.id)
        .order_by(TextVersion.id)
        .all()
    )
    assert [version.text for version in versions] == ["first correction", "second correction"]
    assert versions[1].previous_text == "first correction"
