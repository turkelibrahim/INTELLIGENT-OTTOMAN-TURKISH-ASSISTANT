import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.models.processing_job import ProcessingJob
from app.services.job_manager import JobManager

@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "job_manager.db"
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

def test_job_idempotency(db_session):
    manager = JobManager(db_session)
    job1 = manager.start_job(document_id=1, user_id=1, job_type="ocr")
    job2 = manager.start_job(document_id=1, user_id=1, job_type="ocr")
    
    assert job1.id == job2.id
    assert job1.status == "QUEUED"

def test_job_lifecycle(db_session):
    manager = JobManager(db_session)
    job = manager.start_job(document_id=2, user_id=1, job_type="ocr")
    assert job.status == "QUEUED"
    
    acquired_job = manager.acquire_job("test_worker")
    assert acquired_job is not None
    assert acquired_job.id == job.id
    assert acquired_job.status == "OCR_RUNNING"
    
    manager.mark_completed(job.id, worker_id="test_worker")
    db_session.refresh(job)
    assert job.status == "COMPLETED"

def test_job_cancellation(db_session):
    manager = JobManager(db_session)
    job = manager.start_job(document_id=3, user_id=1, job_type="ocr")
    manager.cancel_job(job.id)
    db_session.refresh(job)
    assert job.status == "CANCELLED"
