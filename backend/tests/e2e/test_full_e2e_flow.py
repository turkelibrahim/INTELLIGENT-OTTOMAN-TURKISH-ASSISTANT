import time
import pytest
import app.models  # noqa: F401
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from io import BytesIO
from PIL import Image
from app.core.config import settings

@pytest.fixture(scope="module")
def engine():
    engine = create_engine(
        "sqlite:///:memory:", 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def db_session(engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture(scope="module")
def client(db_session, tmp_path_factory):
    # Override db
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    
    # Use temporary upload dir
    upload_dir = tmp_path_factory.mktemp("uploads")
    settings.UPLOAD_DIR = str(upload_dir)
    from app.services.file_service import file_service
    file_service.upload_dir = upload_dir

    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def _png_bytes():
    image = Image.new("RGB", (100, 100), (255, 255, 255))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()

def test_full_e2e_flow(client, db_session):
    # 1. Register & Login
    res = client.post("/api/v1/auth/register", json={
        "email": "e2e@example.com",
        "username": "e2e_user",
        "password": "Password123!",
        "full_name": "E2E Tester"
    })
    assert res.status_code in (201, 409)
    
    res = client.post("/api/v1/auth/login", json={
        "email": "e2e@example.com",
        "password": "Password123!"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Upload Document
    res = client.post(
        "/api/v1/documents",
        headers=headers,
        data={"title": "E2E Scan", "description": "e2e test doc"},
        files={"file": ("scan.png", _png_bytes(), "image/png")},
    )
    assert res.status_code == 201
    doc_id = res.json()["id"]
    
    # 3. Get Pages
    res = client.get(f"/api/v1/documents/{doc_id}/pages", headers=headers)
    assert res.status_code == 200
    pages = res.json()["pages"]
    assert len(pages) == 1
    page_id = pages[0]["id"]
    
    # 4. Trigger Preprocessing
    res = client.post(
        f"/api/v1/pages/{page_id}/preprocessing",
        headers=headers,
        json={"profile": "temiz_baski"}
    )
    assert res.status_code == 200
    
    # 5. Trigger OCR (Full Pipeline)
    res = client.post(
        f"/api/v1/documents/{doc_id}/ocr",
        headers=headers,
    )
    assert res.status_code == 202
    job_id = res.json()["job_id"]
    
    # 6. Wait for OCR to complete (Polling)
    # Since worker runs separately, we simulate worker here
    import asyncio
    from worker import process_job
    from app.models.processing_job import ProcessingJob
    
    # Needs a separate session or same session? Let's use a new one to be safe, but db_session is fine.
    # The job should be pending
    job = db_session.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    assert job is not None
    assert job.status == "QUEUED"
    
    # Process it synchronously via asyncio run, using the real pipeline to prevent false pass
    asyncio.run(process_job(db_session, job, "test_worker_e2e"))
    
    res = client.get(
        f"/api/v1/documents/{doc_id}/ocr/status",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"
    
    # 7. Start Chat Session
    res = client.post(
        "/api/v1/chat/sessions",
        headers=headers,
        json={"document_id": doc_id, "title": "E2E Chat"}
    )
    assert res.status_code == 200
    session_id = res.json()["id"]
    
    # 8. Send Chat Message
    res = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        headers=headers,
        json={"content": "Bu belgede neler yazıyor?"}
    )
    assert res.status_code == 200
    chat_response = res.json()
    assert chat_response["role"] == "assistant"
    assert "citations" in chat_response
    
    # 9. Export
    res = client.get(
        f"/api/v1/export/txt/{doc_id}?version_type=raw_ocr",
        headers=headers,
    )
    assert res.status_code == 200
    
    print("E2E Test completed successfully.")
