import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.processing_job import ProcessingJob


ACTIVE_JOB_STATUSES = [
    "QUEUED",
    "PREPROCESSING",
    "LAYOUT_ANALYSIS",
    "OCR_RUNNING",
    "TRANSLITERATING",
    "MODERNIZING",
    "NER_RUNNING",
    "pending",
    "running",
    "retrying",
]

class JobManager:
    def __init__(self, db: Session):
        self.db = db

    def start_job(self, document_id: int, user_id: int, job_type: str = "full_pipeline", idempotency_key: str = None) -> ProcessingJob:
        if idempotency_key:
            existing_job = self.db.query(ProcessingJob).filter(
                ProcessingJob.idempotency_key == idempotency_key
            ).first()
            if existing_job:
                return existing_job
                
        # Existing check by document/user/type
        existing_job = self.db.query(ProcessingJob).filter(
            ProcessingJob.document_id == document_id,
            ProcessingJob.user_id == user_id,
            ProcessingJob.job_type == job_type,
            ProcessingJob.status.in_(ACTIVE_JOB_STATUSES)
        ).first()
        
        if existing_job:
            return existing_job
            
        new_job = ProcessingJob(
            document_id=document_id,
            user_id=user_id,
            job_type=job_type,
            status="QUEUED",
            idempotency_key=idempotency_key,
            max_retries=3,
            retry_count=0
        )
        self.db.add(new_job)
        self.db.commit()
        self.db.refresh(new_job)
        return new_job
        
    def acquire_job(self, worker_id: str, lock_duration_sec: int = 300) -> ProcessingJob:
        """Atomically leases a pending or retrying job for this worker."""
        # Clean up stale locks first
        stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
        stale_jobs = self.db.query(ProcessingJob).filter(
            ProcessingJob.status == "OCR_RUNNING",
            or_(
                ProcessingJob.heartbeat_at < stale_threshold,
                ProcessingJob.heartbeat_at.is_(None)
            )
        ).all()
        for sj in stale_jobs:
            sj.status = "QUEUED"
            sj.locked_by = None
            sj.lock_expires_at = None
        if stale_jobs:
            self.db.commit()

        # Try to acquire a job
        job = self.db.query(ProcessingJob).filter(
            ProcessingJob.status.in_(["QUEUED", "retrying"])
        ).order_by(
            ProcessingJob.created_at.asc()
        ).with_for_update(skip_locked=True).first()
        
        if job:
            job.status = "OCR_RUNNING"
            job.locked_by = worker_id
            job.started_at = job.started_at or datetime.now(timezone.utc)
            job.lock_expires_at = datetime.now(timezone.utc) + timedelta(seconds=lock_duration_sec)
            job.heartbeat_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(job)
            return job
        return None

    def update_heartbeat(self, job_id: int, worker_id: str):
        job = self.db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id,
            ProcessingJob.locked_by == worker_id
        ).first()
        if job:
            job.heartbeat_at = datetime.now(timezone.utc)
            self.db.commit()
            
    def mark_completed(self, job_id: int, result: dict = None, worker_id: str = None):
        job = self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = "COMPLETED"
            job.progress = 100.0
            job.ended_at = datetime.now(timezone.utc)
            if job.started_at:
                job.duration_seconds = (job.ended_at - job.started_at.replace(tzinfo=timezone.utc)).total_seconds()
            job.error_message = None
            job.locked_by = None
            job.lock_expires_at = None
            self.db.commit()
            
    def mark_failed(self, job_id: int, error_message: str, worker_id: str = None):
        job = self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.retry_count += 1
            if job.retry_count >= job.max_retries:
                job.status = "FAILED"
            else:
                job.status = "retrying"
                job.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=2 ** job.retry_count * 10)
                
            job.error_message = error_message
            job.ended_at = datetime.now(timezone.utc)
            job.locked_by = None
            job.lock_expires_at = None
            self.db.commit()

    def cancel_job(self, job_id: int):
        job = self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job and job.status in ["QUEUED", "OCR_RUNNING", "retrying"]:
            job.status = "CANCELLED"
            job.ended_at = datetime.now(timezone.utc)
            job.locked_by = None
            job.lock_expires_at = None
            self.db.commit()
