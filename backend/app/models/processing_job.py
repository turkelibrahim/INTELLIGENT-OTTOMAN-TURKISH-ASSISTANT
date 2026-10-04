"""
Persistent processing job model.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)

from app.db.database import Base


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    page_id = Column(
        Integer,
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    job_type = Column(String(50), nullable=False, index=True)
    status = Column(
        SAEnum(
            "QUEUED",
            "PREPROCESSING",
            "LAYOUT_ANALYSIS",
            "OCR_RUNNING",
            "OCR_LOW_QUALITY",
            "TRANSLITERATING",
            "MODERNIZING",
            "NER_RUNNING",
            "PARTIAL",
            "COMPLETED",
            "FAILED",
            "CANCELLED",
            "pending",
            "running",
            "retrying",
            "timed_out",
            name="job_status",
        ),
        default="QUEUED",
        nullable=False,
        index=True,
    )

    pipeline_version = Column(String(50), nullable=True)
    worker_version = Column(String(50), nullable=True)

    model_name = Column(String(200), nullable=True)
    model_version = Column(String(100), nullable=True)
    parameters = Column(JSON, nullable=True)
    progress = Column(Float, default=0.0, nullable=False)
    result_path = Column(String(1000), nullable=True)

    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)

    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    heartbeat_at = Column(DateTime, nullable=True)
    locked_by = Column(String(100), nullable=True, index=True)
    lock_expires_at = Column(DateTime, nullable=True, index=True)
    next_retry_at = Column(DateTime, nullable=True)
    idempotency_key = Column(String(200), nullable=True, unique=True, index=True)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return (
            f"<ProcessingJob(id={self.id}, type='{self.job_type}', "
            f"status='{self.status}')>"
        )
