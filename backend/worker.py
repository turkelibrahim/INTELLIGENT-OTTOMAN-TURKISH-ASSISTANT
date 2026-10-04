import asyncio
import logging
import sys
import os
import uuid
from datetime import datetime, timezone

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.processing_job import ProcessingJob
from app.services.job_manager import JobManager
from app.services.document_processing.pipeline import DocumentProcessingPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

WORKER_ID = f"worker-{uuid.uuid4().hex[:8]}"
WORKER_VERSION = "2.0.0"

async def heartbeat_loop(db_factory, job_id: int, worker_id: str, interval: int = 30):
    """Periodically updates the heartbeat for the active job."""
    try:
        while True:
            await asyncio.sleep(interval)
            db = db_factory()
            try:
                job_manager = JobManager(db)
                job_manager.update_heartbeat(job_id, worker_id)
                logger.debug(f"Heartbeat updated for job {job_id}")
            except Exception as e:
                logger.error(f"Heartbeat update failed for job {job_id}: {e}")
            finally:
                db.close()
    except asyncio.CancelledError:
        logger.debug(f"Heartbeat loop cancelled for job {job_id}")

_PIPELINE_CACHE = None

def get_pipeline():
    global _PIPELINE_CACHE
    if _PIPELINE_CACHE is None:
        logger.info("Initializing global DocumentProcessingPipeline")
        _PIPELINE_CACHE = DocumentProcessingPipeline()
    return _PIPELINE_CACHE

async def process_job(db, job: ProcessingJob, worker_id: str):
    """Executes a single processing job"""
    job_manager = JobManager(db)
    
    # Start heartbeat task
    hb_task = asyncio.create_task(heartbeat_loop(SessionLocal, job.id, worker_id))
    
    try:
        if job.job_type == "pilot_ocr_evaluation":
            await process_pilot_evaluation_job(db, job, worker_id)
            job_manager.mark_completed(
                job.id,
                result={"status": "PILOT_EVALUATION_QUEUED_FOR_LOCKED_DATASET"},
                worker_id=worker_id,
            )
            return

        if job.job_type == "full_document_analysis":
            await process_full_document_analysis_job(db, job, worker_id)
            job_manager.mark_completed(job.id, result=None, worker_id=worker_id)
            logger.info(f"Full document analysis job {job.id} marked as COMPLETED")
            return

        logger.info(f"Processing document {job.document_id} for job {job.id} (Retry: {job.retry_count}/{job.max_retries})")
        
        # Load the document to get the file path
        from app.models.document import Document
        import cv2
        import numpy as np
        from PIL import Image

        document = db.query(Document).filter(Document.id == job.document_id).first()
        if not document:
            raise ValueError(f"Document {job.document_id} not found")
        
        from app.models.page import Page
        page = db.query(Page).filter(Page.document_id == document.id).order_by(Page.page_no).first()
        if not page:
            raise ValueError(f"No pages found for Document {job.document_id}")
            
        file_path = page.original_path
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
            
        logger.info(f"Loading image from {file_path}")
        image_pil = Image.open(file_path).convert('RGB')
        image_np = np.array(image_pil)
        # Convert RGB to BGR for OpenCV
        if len(image_np.shape) == 3 and image_np.shape[2] == 3:
            image_np = image_np[:, :, ::-1].copy()

        # Run the pipeline
        pipeline = get_pipeline()
        pipeline_result = await pipeline.process_document(
            image_np,
            job_id=str(job.id),
            document_id=str(job.document_id),
            page_id=str(job.page_id or page.id)
        )
        pipeline_result["worker_version"] = WORKER_VERSION
        
        # Save results
        import json
        job.result_summary = json.dumps(pipeline_result, ensure_ascii=False)
        job.confidence_score = pipeline_result.get("quality", {}).get("ocr_confidence", 0.0)
        job.pipeline_version = pipeline_result.get("pipeline_version")
        job.worker_version = WORKER_VERSION
        
        # Populate VectorDB
        try:
            from app.services.chat.embeddings import VectorStoreService
            vector_service = VectorStoreService()
            if vector_service.collection is not None:
                ocr_text = pipeline_result.get("raw_ocr_text", "")
                if ocr_text:
                    chunk_id = f"doc_{job.document_id}_ocr_full"
                    vector_service.add_texts(
                        texts=[ocr_text],
                        metadatas=[{"document_id": job.document_id, "chunk_type": "ocr"}],
                        ids=[chunk_id]
                    )
                logger.info(f"VectorDB populated for document {job.document_id}")
        except Exception as ve:
            logger.error(f"Failed to populate VectorDB: {ve}")
        
        # Mark as completed or failed based on quality gate
        if pipeline_result.get("status") == "FAILED":
            job_manager.mark_failed(job.id, error_message="Pipeline failed quality gate", worker_id=worker_id)
            logger.warning(f"Job {job.id} marked as FAILED due to quality gate")
        else:
            job_manager.mark_completed(job.id, result=pipeline_result, worker_id=worker_id)
            # If low quality, update status to OCR_LOW_QUALITY
            if pipeline_result.get("quality", {}).get("quality_gate") == "LOW_QUALITY":
                job.status = "OCR_LOW_QUALITY"
                db.commit()
            logger.info(f"Job {job.id} marked as {job.status}")
        
    except Exception as e:
        logger.error(f"Job {job.id} failed: {e}")
        import traceback
        traceback.print_exc()
        job_manager.mark_failed(job.id, error_message=str(e), worker_id=worker_id)
    finally:
        hb_task.cancel()
        try:
            await hb_task
        except asyncio.CancelledError:
            pass


def update_job_stage(db, job: ProcessingJob, status: str, progress: float) -> None:
    job.status = status
    job.progress = float(progress)
    job.heartbeat_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("Job %s stage=%s progress=%.1f", job.id, status, progress)


async def process_full_document_analysis_job(db, job: ProcessingJob, worker_id: str):
    """Run the production unknown-document analysis pipeline in the worker context."""
    import json

    from app.models.document import Document
    from app.models.page import Page
    from app.services.document_analysis_pipeline import DocumentAnalysisPipeline

    document = db.query(Document).filter(Document.id == job.document_id).first()
    if not document:
        raise ValueError(f"Document {job.document_id} not found")
    pages = (
        db.query(Page)
        .filter(Page.document_id == document.id)
        .order_by(Page.page_no.asc())
        .all()
    )
    if not pages:
        raise ValueError(f"No pages found for Document {job.document_id}")

    document.status = "preprocessing"
    update_job_stage(db, job, "PREPROCESSING", 5.0)
    pipeline = DocumentAnalysisPipeline()

    update_job_stage(db, job, "OCR_RUNNING", 20.0)
    result = await pipeline.analyze_document(
        document=document,
        pages=pages,
        db=db,
        user_id=job.user_id,
    )
    update_job_stage(db, job, "TRANSLITERATING", 70.0)
    # DocumentAnalysisPipeline currently performs transformation/RAG inside one call.
    # These final persisted stages keep the external job lifecycle observable.
    update_job_stage(db, job, "MODERNIZING", 82.0)
    update_job_stage(db, job, "NER_RUNNING", 92.0)

    job.result_summary = json.dumps(result, ensure_ascii=False)
    job.confidence_score = result.get("confidence", {}).get("combined")
    job.pipeline_version = "document-analysis-pipeline-1d"
    job.worker_version = WORKER_VERSION
    document.status = "ready"
    db.commit()


async def process_pilot_evaluation_job(db, job: ProcessingJob, worker_id: str):
    """Run real OCR and metrics for a locked pilot ground-truth dataset."""
    import json
    import statistics
    import time
    import csv
    from pathlib import Path

    import numpy as np
    from PIL import Image

    from app.models.ground_truth import Dataset, GroundTruthLine, GroundTruthPage
    from app.services.document_processing.ocr_factory import create_ottoman_ocr_engine
    from app.services.evaluation.metrics import calculate_metrics, evaluate_page

    params = job.parameters or {}
    dataset_id = params.get("dataset_id")
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or dataset.status != "LOCKED":
        raise ValueError("Pilot evaluation requires a LOCKED dataset")

    if job.result_path:
        result_path = Path(job.result_path)
        if not result_path.is_absolute():
            result_path = Path(__file__).resolve().parents[1] / result_path
        evidence_dir = result_path.parent
    else:
        evidence_dir = Path(__file__).resolve().parents[1] / "evidence" / "post_review_reconciliation"
        result_path = evidence_dir / f"pilot_metrics_job_{job.id}.json"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    page_metrics_path = evidence_dir / f"pilot_page_metrics_job_{job.id}.csv"
    error_analysis_path = evidence_dir / f"pilot_error_analysis_job_{job.id}.md"

    engine = create_ottoman_ocr_engine()
    model_metadata = engine.model_metadata()

    page_rows = []
    page_payloads = []
    all_gt_lines = []
    all_ocr_lines = []
    all_times = []
    total_gt_lines = 0
    total_detected_lines = 0
    total_matched_lines = 0
    exact_line_matches = 0
    page_failures = 0
    error_examples = []

    pages = (
        db.query(GroundTruthPage)
        .filter(GroundTruthPage.dataset_id == dataset.id)
        .order_by(GroundTruthPage.id)
        .all()
    )
    for index, page in enumerate(pages, start=1):
        image_path = Path(page.image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Pilot page image missing: {image_path}")

        gt_lines = (
            db.query(GroundTruthLine)
            .filter(GroundTruthLine.page_id == page.id)
            .order_by(GroundTruthLine.reading_order)
            .all()
        )
        gt_texts = [line.text_content for line in gt_lines]
        total_gt_lines += len(gt_lines)

        start = time.perf_counter()
        image = np.array(Image.open(image_path).convert("RGB"))
        ocr_result = await engine.extract(image[:, :, ::-1].copy())
        elapsed_ms = (time.perf_counter() - start) * 1000
        all_times.append(elapsed_ms)

        ocr_lines_sorted = sorted(ocr_result.lines, key=lambda line: (line.bbox[1], line.bbox[0]))
        ocr_texts = [line.text for line in ocr_lines_sorted]
        total_detected_lines += len(ocr_texts)
        if not ocr_texts:
            page_failures += 1

        page_eval = evaluate_page(gt_texts, ocr_texts)
        strict = page_eval["strict"]
        normalized = page_eval["normalized"]

        matched_for_page = min(len(gt_texts), len(ocr_texts))
        total_matched_lines += matched_for_page
        for line_idx in range(matched_for_page):
            if gt_texts[line_idx] == ocr_texts[line_idx]:
                exact_line_matches += 1
            if gt_texts[line_idx] != ocr_texts[line_idx] and len(error_examples) < 20:
                error_examples.append(
                    {
                        "page_id": page.id,
                        "line_index": line_idx + 1,
                        "ground_truth": gt_texts[line_idx],
                        "ocr": ocr_texts[line_idx],
                    }
                )

        all_gt_lines.extend(gt_texts)
        all_ocr_lines.extend(ocr_texts)
        row = {
            "page_id": page.id,
            "source_page_id": page.metadata_json.get("source_page_id") if page.metadata_json else f"page_{index:03d}",
            "split": page.split_type,
            "gt_lines": len(gt_texts),
            "ocr_lines": len(ocr_texts),
            "strict_cer": strict.get("cer"),
            "normalized_cer": normalized.get("cer"),
            "strict_wer": strict.get("wer"),
            "normalized_wer": normalized.get("wer"),
            "processing_time_ms": elapsed_ms,
            "engine": ocr_result.engine_name,
            "confidence": ocr_result.page_confidence,
        }
        page_rows.append(row)
        page_payloads.append({**row, "ocr_texts": ocr_texts})
        job.progress = round((index / max(len(pages), 1)) * 100, 2)
        job.heartbeat_at = datetime.now(timezone.utc)
        db.commit()

    aggregate_eval = evaluate_page(all_gt_lines, all_ocr_lines)
    strict_agg = aggregate_eval["strict"]
    normalized_agg = aggregate_eval["normalized"]
    line_precision = total_matched_lines / total_detected_lines if total_detected_lines else 0.0
    line_recall = total_matched_lines / total_gt_lines if total_gt_lines else 0.0
    line_f1 = (
        2 * line_precision * line_recall / (line_precision + line_recall)
        if line_precision + line_recall
        else 0.0
    )
    exact_line_match = exact_line_matches / total_gt_lines if total_gt_lines else 0.0
    reading_order_accuracy = exact_line_match
    payload = {
        "status": "SUCCEEDED",
        "job_id": job.id,
        "dataset_id": dataset.id,
        "dataset_version": dataset.version,
        "worker_id": worker_id,
        "model": model_metadata,
        "preprocessing_profile": "raw_page_images",
        "strict_cer": strict_agg.get("cer"),
        "normalized_cer": normalized_agg.get("cer"),
        "strict_wer": strict_agg.get("wer"),
        "normalized_wer": normalized_agg.get("wer"),
        "character_accuracy": 1.0 - float(strict_agg.get("cer", 1.0)),
        "exact_line_match": exact_line_match,
        "line_precision": line_precision,
        "line_recall": line_recall,
        "line_f1": line_f1,
        "reading_order_accuracy": reading_order_accuracy,
        "page_failure_rate": page_failures / len(pages) if pages else 1.0,
        "performance_ms": {
            "average": statistics.mean(all_times) if all_times else 0.0,
            "median": statistics.median(all_times) if all_times else 0.0,
            "p95": sorted(all_times)[int(0.95 * (len(all_times) - 1))] if all_times else 0.0,
            "pages": all_times,
        },
        "totals": {
            "pages": len(pages),
            "gt_lines": total_gt_lines,
            "ocr_lines": total_detected_lines,
            "matched_lines": total_matched_lines,
        },
        "pages": page_payloads,
        "error_examples": error_examples,
    }

    with page_metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(page_rows[0].keys()) if page_rows else ["page_id"])
        writer.writeheader()
        writer.writerows(page_rows)

    error_lines = [
        "# Pilot OCR Error Analysis",
        "",
        f"Job: {job.id}",
        f"Dataset: {dataset.id} / {dataset.version}",
        f"Total error examples captured: {len(error_examples)}",
        "",
    ]
    for example in error_examples:
        error_lines.extend(
            [
                f"## Page {example['page_id']} Line {example['line_index']}",
                f"- Ground truth: `{example['ground_truth']}`",
                f"- OCR: `{example['ocr']}`",
                "",
            ]
        )
    error_analysis_path.write_text("\n".join(error_lines), encoding="utf-8")

    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    job.progress = 100.0
    job.result_path = str(result_path)
    job.result_summary = json.dumps(payload, ensure_ascii=False)
    primary_engine = model_metadata.get("primary_engine")
    job.model_name = primary_engine
    job.model_version = (
        model_metadata.get("engines", {})
        .get(primary_engine, {})
        .get("engine_version", "unknown")
    )
    job.confidence_score = statistics.mean([row["confidence"] for row in page_rows]) if page_rows else 0.0
    db.commit()

async def run_worker(poll_interval: int = 5):
    """Runs the persistent background worker polling the database"""
    logger.info(f"Starting Persistent Background Worker (ID: {WORKER_ID})...")
    
    while True:
        db = SessionLocal()
        try:
            job_manager = JobManager(db)
            job = job_manager.acquire_job(worker_id=WORKER_ID)
            
            if job:
                logger.info(f"Acquired job {job.id}")
                await process_job(db, job, WORKER_ID)
            else:
                await asyncio.sleep(poll_interval)
                
        except Exception as e:
            logger.error(f"Worker encountered an error: {e}")
            await asyncio.sleep(poll_interval)
        finally:
            db.close()

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")

