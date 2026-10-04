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
from app.models.processing_outputs import Entity, TextVersion
from app.models.user import User
from app.services.document_processing.ner_extractor import NERExtractor


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "analysis.db"
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


def _text_version(db_session, owner, text):
    document = Document(
        user_id=owner.id,
        title="Analysis Doc",
        original_filename="analysis.png",
        file_hash="hash-analysis",
        file_size=12,
        mime_type="image/png",
        page_count=1,
        status="analysis",
        access_level="private",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    version = TextVersion(
        document_id=document.id,
        user_id=owner.id,
        version_type="modernization_faithful",
        text=text,
        confidence_score=0.8,
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    return document, version


def test_ner_extracts_entities_dates_glossary_and_metrics():
    extractor = NERExtractor()
    text = "Ahmed Pasa Istanbul Hicri 1327 tarihinde mektub dahi yazdi."
    result = extractor.extract(text, source_line_no=4)

    types = {entity["entity_type"] for entity in result["entities"]}
    date_entity = next(entity for entity in result["entities"] if entity["entity_type"] == "DATE")
    glossary = {entry["word"] for entry in result["glossary"]}
    metrics = extractor.evaluate_predictions(["Ahmed Pasa", "Istanbul"], ["Ahmed Pasa", "Istanbul", "1327"])

    assert {"PER", "LOC", "DATE", "GLOSSARY"}.issubset(types)
    assert date_entity["metadata"]["date"]["raw_value"] == "Hicri 1327"
    assert date_entity["metadata"]["date"]["calendar"] == "hijri"
    assert date_entity["metadata"]["date"]["method"] == "approx_hijri_year_plus_622"
    assert {"mektub", "dahi"}.issubset(glossary)
    assert metrics == {"precision": 1.0, "recall": 0.6667, "f1": 0.8}
    assert result["ocr_impact"]["impact_level"] == "low"


def test_ocr_impact_report_flags_uncertain_tokens():
    report = NERExtractor().ocr_impact_report("Ali Pasa [okunamadi] ???")

    assert report["suspicious_token_count"] == 2
    assert report["impact_level"] == "high"
    assert "not a correctness guarantee" in report["note"]


def test_analysis_api_stores_entities_user_correction_and_audit(client, db_session):
    owner = _user(db_session, "analysis-owner@example.com", "analysisowner")
    _, version = _text_version(
        db_session,
        owner,
        "Ahmed Pasa Istanbul Rumi 1330 tarihinde mektub yazdi.",
    )

    response = client.post(
        f"/api/v1/analysis/text-versions/{version.id}/entities",
        headers=_headers(owner),
        json={
            "user_entities": [
                {
                    "entity_type": "ORG",
                    "value": "Meclis-i Mebusan",
                    "normalized_value": "Meclis-i Mebusan",
                    "start_offset": 0,
                    "end_offset": 16,
                }
            ]
        },
    )

    assert response.status_code == 201
    body = response.json()
    entities = db_session.query(Entity).filter(Entity.text_version_id == version.id).all()
    actions = {audit.action for audit in db_session.query(AuditLog).all()}

    assert body["evaluation"] == {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    assert any(entity.entity_type == "DATE" and entity.metadata_json["date"]["raw_value"] == "Rumi 1330" for entity in entities)
    assert any(entity.entity_type == "ORG" and entity.metadata_json["source"] == "user_correction" for entity in entities)
    assert {"entity.extraction.create", "entity.user_correction.create"}.issubset(actions)


def test_analysis_api_enforces_ownership(client, db_session):
    owner = _user(db_session, "analysis-scope@example.com", "analysisscope")
    other = _user(db_session, "analysis-other@example.com", "analysisother")
    _, version = _text_version(db_session, owner, "Ahmed Pasa Istanbul 1327")

    response = client.post(
        f"/api/v1/analysis/text-versions/{version.id}/entities",
        headers=_headers(other),
        json={},
    )

    assert response.status_code == 403
