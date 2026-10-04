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
from app.services.document_processing.translator import Translator


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "transliteration.db"
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


def _ocr_line(db_session, owner):
    document = Document(
        user_id=owner.id,
        title="Transliteration Doc",
        original_filename="translit.png",
        file_hash="hash-translit",
        file_size=12,
        mime_type="image/png",
        page_count=1,
        status="ocr_review",
        access_level="private",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    page = Page(document_id=document.id, page_no=1, original_path="translit.png", status="ocr_review")
    db_session.add(page)
    db_session.commit()
    db_session.refresh(page)

    ocr = OCRResult(
        page_id=page.id,
        line_no=7,
        bbox={"x": 10, "y": 10, "w": 80, "h": 12},
        raw_text="كتاب ١٢",
        confidence_score=0.74,
    )
    db_session.add(ocr)
    db_session.commit()
    db_session.refresh(ocr)
    return document, page, ocr


def test_transliterator_reports_source_mapping_and_ambiguity():
    result = Translator().transliterate_line("كتاب ١٢", source_ocr_result_id=42, line_no=3)

    assert result.source_ocr_result_id == 42
    assert result.line_no == 3
    assert result.transliterated_text == "kitab 12"
    assert result.ambiguity_level == "medium"
    assert any(candidate.ambiguity_level == "medium" for candidate in result.candidates)


def test_transliteration_fixture_metrics_report():
    report = Translator().evaluate_fixture(
        [
            {"source": "كتاب", "expected": "kitab"},
            {"source": "بسم الله الرحمن الرحيم", "expected": "bism allah er-rahman er-rahim"},
        ]
    )

    assert report == {"cer": 0.0, "wer": 0.0, "chrf": 1.0, "sample_count": 2}


def test_transliteration_api_stores_latin_text_separately_and_preserves_ocr(client, db_session):
    owner = _user(db_session, "translit-owner@example.com", "translitowner")
    _, _, ocr = _ocr_line(db_session, owner)

    response = client.post(f"/api/v1/transliteration/ocr-results/{ocr.id}", headers=_headers(owner), json={})

    assert response.status_code == 201
    body = response.json()
    db_session.refresh(ocr)
    version = db_session.get(TextVersion, body["text_version_id"])
    audit = db_session.query(AuditLog).filter(AuditLog.action == "transliteration.create").one()

    assert ocr.raw_text == "كتاب ١٢"
    assert version.version_type == "transliteration"
    assert version.ocr_result_id == ocr.id
    assert version.text == "kitab 12"
    assert body["source_text"] == "كتاب ١٢"
    assert body["ocr_result_id"] == ocr.id
    assert "rule-based-ottoman-latin-v2" in audit.new_value


def test_transliteration_uses_latest_ocr_correction_and_keeps_history(client, db_session):
    owner = _user(db_session, "translit-history@example.com", "translithistory")
    _, _, ocr = _ocr_line(db_session, owner)
    correction = TextVersion(
        document_id=ocr.page.document_id,
        page_id=ocr.page_id,
        ocr_result_id=ocr.id,
        user_id=owner.id,
        version_type="ocr_correction",
        text="كتب",
        previous_text=ocr.raw_text,
    )
    db_session.add(correction)
    db_session.commit()

    first = client.post(f"/api/v1/transliteration/ocr-results/{ocr.id}", headers=_headers(owner), json={})
    second = client.post(
        f"/api/v1/transliteration/ocr-results/{ocr.id}",
        headers=_headers(owner),
        json={"text": "كتاب"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    versions = (
        db_session.query(TextVersion)
        .filter(TextVersion.ocr_result_id == ocr.id, TextVersion.version_type == "transliteration")
        .order_by(TextVersion.id)
        .all()
    )
    assert [version.text for version in versions] == ["kitab", "kitab"]
    assert versions[1].previous_text == "kitab"
    assert versions[1].source_version_id == versions[0].id


def test_transliteration_api_enforces_document_ownership(client, db_session):
    owner = _user(db_session, "translit-scope@example.com", "translitscope")
    other = _user(db_session, "translit-other@example.com", "translitother")
    _, _, ocr = _ocr_line(db_session, owner)

    response = client.post(f"/api/v1/transliteration/ocr-results/{ocr.id}", headers=_headers(other), json={})

    assert response.status_code == 403
