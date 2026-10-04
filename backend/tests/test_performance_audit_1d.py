import asyncio
import json
from types import SimpleNamespace

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes.document_analysis import _find_active_analysis_job
from app.db.database import Base
from app.models.document import Document
from app.models.page import Page
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.services.document_processing.kraken_service_client import PersistentKrakenServiceClient
from app.services.job_manager import JobManager
from worker import process_job


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'perf_1d.db'}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _user(db):
    user = User(email="perf1d@example.com", username="perf1d", password_hash="x", status="active")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _document(db, user, file_hash="hash-1"):
    document = Document(
        user_id=user.id,
        title="Perf 1D",
        original_filename="doc.png",
        file_hash=file_hash,
        file_size=128,
        mime_type="image/png",
        status="uploaded",
        access_level="private",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    page = Page(
        document_id=document.id,
        page_no=1,
        original_path="doc.png",
        width=100,
        height=50,
        status="pending",
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return document, page


def test_persistent_kraken_client_uses_service_schema_and_clamps_network_ms(monkeypatch):
    calls = {"ready": 0, "ocr": 0}

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_get(url, timeout):
        calls["ready"] += 1
        return Response({"model_loaded": True, "model_load_count": 1})

    def fake_post(url, files, data, timeout):
        calls["ocr"] += 1
        assert url.endswith("/ocr")
        assert files["image"][2] == "image/png"
        assert json.loads(data["boxes"]) == {"7": [1, 2, 4, 6]}
        return Response(
            {
                "status": "success",
                "lines": [{"id": "7", "text": "متن", "confidence": 0.9}],
                "timings": {"total_ms": 999999.0},
                "service_state": {"model_load_count": 1, "request_count": 1},
            }
        )

    monkeypatch.setattr("app.services.document_processing.kraken_service_client.requests.get", fake_get)
    monkeypatch.setattr("app.services.document_processing.kraken_service_client.requests.post", fake_post)

    box = SimpleNamespace(line_index=7, bbox=(1, 2, 3, 4))
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    lines, payload = PersistentKrakenServiceClient(base_url="http://local").extract_batch(image, [box])

    assert calls == {"ready": 1, "ocr": 1}
    assert lines[0]["text"] == "متن"
    assert payload["timings"]["network_ms"] == 0.0
    assert payload["service_state"]["model_load_count"] == 1


def test_active_full_analysis_duplicate_is_reused_but_completed_job_is_not(db_session):
    user = _user(db_session)
    document, _page = _document(db_session, user, file_hash="same-hash")
    active = JobManager(db_session).start_job(document.id, user.id, "full_document_analysis")

    found = _find_active_analysis_job(db_session, user_id=user.id, file_hash="same-hash")
    assert found.id == active.id

    active.status = "COMPLETED"
    active.progress = 100.0
    db_session.commit()

    assert _find_active_analysis_job(db_session, user_id=user.id, file_hash="same-hash") is None
    new_job = JobManager(db_session).start_job(document.id, user.id, "full_document_analysis")
    assert new_job.id != active.id
    assert new_job.status == "QUEUED"


def test_worker_full_document_analysis_persists_result_and_completion(db_session, monkeypatch):
    user = _user(db_session)
    document, page = _document(db_session, user)
    job = JobManager(db_session).start_job(document.id, user.id, "full_document_analysis")
    job.page_id = page.id
    db_session.commit()

    class FakePipeline:
        async def analyze_document(self, document, pages, db, user_id):
            assert document.id == job.document_id
            assert [page.id for page in pages] == [job.page_id]
            assert user_id == user.id
            return {
                "document": {"id": document.id, "title": document.title},
                "ocr": {"text": "متن", "confidence": 0.91, "lines": []},
                "transliteration": {"text": "metn", "lines": []},
                "modern_turkish": {"text": "metin", "lines": []},
                "entities": [],
                "metadata": {},
                "confidence": {"combined": 0.88},
            }

    monkeypatch.setattr("app.services.document_analysis_pipeline.DocumentAnalysisPipeline", FakePipeline)

    asyncio.run(process_job(db_session, job, "worker-test"))
    db_session.refresh(job)
    db_session.refresh(document)

    assert job.status == "COMPLETED"
    assert job.progress == 100.0
    assert job.confidence_score == 0.88
    assert job.pipeline_version == "document-analysis-pipeline-1d"
    assert document.status == "ready"
    assert json.loads(job.result_summary)["ocr"]["text"] == "متن"
