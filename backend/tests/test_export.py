import json
import csv
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, get_password_hash
from app.db.database import Base, get_db
from app.main import app
from app.models.document import Document
from app.models.user import User
from app.models.page import Page
from app.models.processing_outputs import OCRResult, TextVersion, Entity, Citation, ExportRecord

@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "export.db"
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

@pytest.fixture()
def test_user(db_session):
    return _create_user(db_session, "export1@example.com", "export1")

@pytest.fixture()
def test_user2(db_session):
    return _create_user(db_session, "export2@example.com", "export2")

@pytest.fixture()
def test_document(db_session, test_user):
    doc = Document(
        user_id=test_user.id,
        title="Export Doc",
        original_filename="doc.pdf",
        file_hash="hash",
        file_size=10,
        mime_type="application/pdf",
        page_count=1,
        status="ready",
        access_level="private",
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc

def test_export_txt_raw_ocr(client, db_session, test_user, test_document):
    page = Page(document_id=test_document.id, page_no=1, original_path="dummy.png")
    db_session.add(page)
    db_session.commit()
    
    ocr1 = OCRResult(page_id=page.id, raw_text="Line 1", line_no=1, confidence_score=0.9)
    ocr2 = OCRResult(page_id=page.id, raw_text="Line 2", line_no=2, confidence_score=0.8)
    db_session.add_all([ocr1, ocr2])
    db_session.commit()
    
    headers = _auth_header(test_user)
    resp = client.get(f"/api/v1/export/txt/{test_document.id}?version_type=raw_ocr", headers=headers)
    assert resp.status_code == 200
    assert "Line 1" in resp.json()["content"]
    assert "Line 2" in resp.json()["content"]
    
    records = db_session.query(ExportRecord).all()
    assert len(records) == 1
    assert records[0].export_type == "txt_raw_ocr"

def test_export_txt_latin(client, db_session, test_user, test_document):
    tv = TextVersion(document_id=test_document.id, version_type="latin", text="Transliterated line")
    db_session.add(tv)
    db_session.commit()
    
    headers = _auth_header(test_user)
    resp = client.get(f"/api/v1/export/txt/{test_document.id}?version_type=latin", headers=headers)
    assert resp.status_code == 200
    assert "Transliterated line" in resp.json()["content"]

def test_export_json_full(client, db_session, test_user, test_document):
    page = Page(document_id=test_document.id, page_no=1, original_path="dummy.png")
    db_session.add(page)
    db_session.commit()
    
    ocr = OCRResult(page_id=page.id, raw_text="JSON test line", line_no=1, confidence_score=0.9, bbox=[0,0,10,10])
    ent = Entity(document_id=test_document.id, entity_type="PERSON", value="Osman", confidence_score=0.8)
    from app.models.processing_outputs import ChatSession, ChatMessage
    session = ChatSession(document_id=test_document.id, user_id=test_user.id, title="test")
    db_session.add(session)
    db_session.commit()
    msg = ChatMessage(session_id=session.id, role="assistant", content="test")
    db_session.add(msg)
    db_session.commit()
    cit = Citation(message_id=msg.id, document_id=test_document.id, quote="Osman text", locator="Page 1")
    db_session.add_all([ocr, ent, cit])
    db_session.commit()
    
    headers = _auth_header(test_user)
    resp = client.get(f"/api/v1/export/json/{test_document.id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["document_id"] == test_document.id
    assert data["title"] == "Export Doc"
    assert data["pages"][0]["lines"][0]["text"] == "JSON test line"
    assert data["entities"][0]["value"] == "Osman"
    assert data["citations"][0]["locator"] == "Page 1"
    
    records = db_session.query(ExportRecord).filter(ExportRecord.export_type == "json_full").all()
    assert len(records) == 1

def test_export_csv_entities(client, db_session, test_user, test_document):
    ent1 = Entity(document_id=test_document.id, entity_type="LOCATION", value="Istanbul", confidence_score=0.9)
    ent2 = Entity(document_id=test_document.id, entity_type="DATE", value="1453", confidence_score=0.95)
    db_session.add_all([ent1, ent2])
    db_session.commit()
    
    headers = _auth_header(test_user)
    resp = client.get(f"/api/v1/export/csv/entities/{test_document.id}", headers=headers)
    assert resp.status_code == 200
    
    content = resp.json()["content"]
    assert "LOCATION,Istanbul" in content
    assert "DATE,1453" in content

def test_export_unauthorized_access(client, db_session, test_user2, test_document):
    headers = _auth_header(test_user2)
    resp = client.get(f"/api/v1/export/json/{test_document.id}", headers=headers)
    assert resp.status_code == 403
