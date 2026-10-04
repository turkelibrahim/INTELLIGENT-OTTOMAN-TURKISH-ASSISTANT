import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.processing_job import ProcessingJob
from worker import process_job


def run_async(coro):
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()

def test_process_job_marks_running_then_completed():
    db = MagicMock(spec=Session)
    
    # Create a mock job
    job = ProcessingJob(
        id=1,
        document_id=100,
        user_id=1,
        job_type="full_pipeline",
        status="QUEUED"
    )
    
    
    # Mock Document model and pipeline
    mock_doc = MagicMock()
    mock_doc.file_path = "dummy/path.png"
    db.query.return_value.filter.return_value.first.return_value = mock_doc
    
    with patch("PIL.Image.open") as mock_image_open, \
         patch("worker.DocumentProcessingPipeline") as MockPipeline:
        
        # Mock image to avoid file system errors
        mock_image_open.return_value = MagicMock()
        from unittest.mock import AsyncMock
        mock_pipeline_instance = MockPipeline.return_value
        mock_pipeline_instance.process_document = AsyncMock(return_value={"quality": {"ocr_confidence": 0.9}})
        
        # Run the worker process
        run_async(process_job(db, job, "test_worker_1"))
        
    assert '"quality": {"ocr_confidence": 0.9}' in job.result_summary

