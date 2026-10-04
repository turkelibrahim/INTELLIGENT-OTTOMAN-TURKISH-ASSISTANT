import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import get_current_user
from app.db.database import Base, get_db
from app.main import app
from app.models.ground_truth import GroundTruthLine, GroundTruthReviewAudit
from app.models.processing_job import ProcessingJob
from app.models.user import User
from worker import process_job


def run_async(coro):
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'human_review.db').as_posix()}",
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
def users(db_session):
    user_a = User(
        email="reviewer-a@example.com",
        username="reviewer_a",
        full_name="Reviewer A",
        password_hash="pw",
        status="active",
    )
    user_b = User(
        email="reviewer-b@example.com",
        username="reviewer_b",
        full_name="Reviewer B",
        password_hash="pw",
        status="active",
    )
    db_session.add_all([user_a, user_b])
    db_session.commit()
    db_session.refresh(user_a)
    db_session.refresh(user_b)
    return user_a, user_b


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def set_user(user):
    app.dependency_overrides[get_current_user] = lambda: user


def import_pilot(client, user):
    set_user(user)
    response = client.post("/api/v1/ground-truth/pilot-draft/import")
    assert response.status_code == 200
    return response.json()


def test_pilot_import_is_idempotent_and_preserves_integrity(client, db_session, users):
    user_a, _ = users

    first = import_pilot(client, user_a)
    second = import_pilot(client, user_a)

    assert first["created"] is True
    assert second["created"] is False
    progress = second["progress"]
    assert progress["total_lines"] == 73
    assert progress["text_reviewed"] == 0
    assert [page["total"] for page in progress["pages"]] == [23, 25, 25]

    pages = client.get(f"/api/v1/ground-truth/datasets/{first['dataset']['id']}/pages").json()
    assert [page["split_type"] for page in pages] == ["dev", "test", "test"]
    assert pages[0]["original_image_hash"] == "a4143718838f5f02dd52dcebdc656e3c39a66bdb5cba488e22ea018c0ee35f9d"
    assert db_session.query(GroundTruthLine).count() == 73


def test_review_auth_audit_lock_and_auto_job(client, db_session, users):
    user_a, user_b = users
    imported = import_pilot(client, user_a)
    dataset_id = imported["dataset"]["id"]
    pages = client.get(f"/api/v1/ground-truth/datasets/{dataset_id}/pages").json()
    first_page_id = pages[0]["id"]
    lines = client.get(f"/api/v1/ground-truth/pages/{first_page_id}/lines").json()

    set_user(user_b)
    assert client.get(f"/api/v1/ground-truth/pages/{first_page_id}/lines").status_code == 403

    set_user(user_a)
    spoof = client.patch(
        f"/api/v1/ground-truth/lines/{lines[0]['id']}/review",
        json={
            "text_content": lines[0]["text_content"],
            "bounding_box": lines[0]["bounding_box"],
            "text_reviewed": True,
            "bbox_reviewed": True,
            "reviewer_display_name": "Fake Reviewer",
        },
    )
    assert spoof.status_code == 400

    denied = client.post(
        f"/api/v1/ground-truth/datasets/{dataset_id}/ready-to-lock",
        json={"rights_confirmed": True},
    )
    assert denied.status_code == 400

    for page in pages:
        for line in client.get(f"/api/v1/ground-truth/pages/{page['id']}/lines").json():
            response = client.patch(
                f"/api/v1/ground-truth/lines/{line['id']}/review",
                json={
                    "text_content": line["text_content"],
                    "bounding_box": line["bounding_box"],
                    "text_reviewed": True,
                    "bbox_reviewed": True,
                },
            )
            assert response.status_code == 200

    progress = client.get(f"/api/v1/ground-truth/datasets/{dataset_id}/progress").json()
    assert progress["text_reviewed"] == 73
    assert progress["bbox_reviewed"] == 73
    assert progress["pending"] == 0

    ready = client.post(
        f"/api/v1/ground-truth/datasets/{dataset_id}/ready-to-lock",
        json={"rights_confirmed": True},
    )
    assert ready.status_code == 200

    locked = client.post(f"/api/v1/ground-truth/datasets/{dataset_id}/lock")
    assert locked.status_code == 200
    job_id = locked.json()["job_id"]
    duplicate = client.post(f"/api/v1/ground-truth/datasets/{dataset_id}/lock")
    assert duplicate.json()["job_id"] == job_id

    assert db_session.query(GroundTruthReviewAudit).count() == 73
    assert {audit.reviewer_id for audit in db_session.query(GroundTruthReviewAudit).all()} == {user_a.id}

    line_after_lock = db_session.query(GroundTruthLine).first()
    immutable = client.patch(
        f"/api/v1/ground-truth/lines/{line_after_lock.id}/review",
        json={
            "text_content": line_after_lock.text_content,
            "bounding_box": line_after_lock.bounding_box,
            "text_reviewed": True,
            "bbox_reviewed": True,
        },
    )
    assert immutable.status_code == 400

    job = db_session.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    assert job.job_type == "pilot_ocr_evaluation"
    from unittest.mock import patch, AsyncMock

    class DummyOCRResult:
        def __init__(self):
            self.engine_name = "test_engine"
            self.confidence = 0.9
            self.page_confidence = 0.9
            self.lines = []

    with patch("app.services.document_processing.ocr_factory.create_ottoman_ocr_engine") as mock_engine_factory:
        mock_engine = mock_engine_factory.return_value
        mock_engine.extract = AsyncMock(return_value=DummyOCRResult())
        mock_engine.model_metadata.return_value = {"model": "test"}
        run_async(process_job(db_session, job, "review-test-worker"))
    db_session.refresh(job)
    assert job.status == "COMPLETED"
    assert job.progress == 100.0
