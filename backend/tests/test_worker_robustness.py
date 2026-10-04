import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
import app.models  # noqa: F401
from app.models.processing_job import ProcessingJob
from app.services.job_manager import JobManager


@pytest.fixture
def db_session(tmp_path):
    db_path = tmp_path / "worker_robustness.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_atomic_lease(db_session):
    jm = JobManager(db_session)
    job = jm.start_job(document_id=1, user_id=1)
    assert job.status == "QUEUED"

    acquired_1 = jm.acquire_job("worker_1")
    assert acquired_1 is not None
    assert acquired_1.id == job.id
    assert acquired_1.status == "OCR_RUNNING"
    assert acquired_1.locked_by == "worker_1"

    acquired_2 = jm.acquire_job("worker_2")
    assert acquired_2 is None


def test_stale_lease_recovery(db_session):
    jm = JobManager(db_session)
    job = jm.start_job(document_id=2, user_id=1)

    job.status = "OCR_RUNNING"
    job.locked_by = "dead_worker"
    job.heartbeat_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.commit()

    acquired = jm.acquire_job("new_worker")
    assert acquired is not None
    assert acquired.id == job.id
    assert acquired.locked_by == "new_worker"
    assert acquired.status == "OCR_RUNNING"


def test_retry_backoff(db_session):
    jm = JobManager(db_session)
    job = jm.start_job(document_id=3, user_id=1)

    jm.mark_failed(job.id, error_message="Mock error", worker_id="worker_x")
    db_session.refresh(job)

    assert job.status == "retrying"
    assert job.retry_count == 1
    assert job.next_retry_at is not None

    jm.mark_failed(job.id, error_message="Mock error 2", worker_id="worker_x")
    db_session.refresh(job)
    assert job.retry_count == 2

    jm.mark_failed(job.id, error_message="Fatal error", worker_id="worker_x")
    db_session.refresh(job)
    assert job.status == "FAILED"


def test_idempotency(db_session):
    jm = JobManager(db_session)
    job1 = jm.start_job(document_id=4, user_id=1, idempotency_key="unique_key_123")
    job2 = jm.start_job(document_id=4, user_id=1, idempotency_key="unique_key_123")

    assert job1.id == job2.id


def test_pilot_evaluation_uses_job_result_path_source_contract():
    worker_source = open("worker.py", "r", encoding="utf-8").read()

    assert "if job.result_path:" in worker_source
    assert "result_path = Path(job.result_path)" in worker_source
    assert "pilot_metrics.json\"" not in worker_source
    assert "pilot_metrics_job_" in worker_source
    assert "pilot_page_metrics_job_" in worker_source
    assert "pilot_error_analysis_job_" in worker_source
