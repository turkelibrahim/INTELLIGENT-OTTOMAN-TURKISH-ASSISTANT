import asyncio
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.processing_job import ProcessingJob
from worker import process_full_document_analysis_job

async def test_job():
    db = SessionLocal()
    job = db.query(ProcessingJob).order_by(ProcessingJob.id.desc()).first()
    print(f"Testing job {job.id}")
    try:
        await process_full_document_analysis_job(db, job, "manual-test-worker")
        print("Success!")
    except Exception as e:
        print("CRITICAL ERROR IN PIPELINE:")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_job())
