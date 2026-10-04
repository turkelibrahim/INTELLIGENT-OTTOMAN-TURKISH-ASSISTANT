import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.page import Page
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.schemas.document_analysis import FullDocumentAnalysisResponse
from app.services.document_analysis_pipeline import DocumentAnalysisPipeline
from app.services.file_service import file_service
from app.services.job_manager import ACTIVE_JOB_STATUSES, JobManager

router = APIRouter(prefix="/document", tags=["Document Analysis"])


def get_document_analysis_pipeline() -> DocumentAnalysisPipeline:
    return DocumentAnalysisPipeline()


async def _create_uploaded_document(
    *,
    file: UploadFile,
    title: str,
    description: Optional[str],
    current_user: User,
    db: Session,
) -> tuple[Document, list[Page], str]:
    mime_type, ext = file_service.validate_file(file)

    document = Document(
        user_id=current_user.id,
        title=title,
        description=description,
        original_filename=file.filename,
        file_hash="pending",
        file_size=0,
        mime_type=mime_type,
        status="uploaded",
        access_level="private",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        saved_path, file_hash, file_size = await file_service.save_upload(file, document.id)
        document.file_hash = file_hash
        document.file_size = file_size

        pages: list[Page] = []
        if ext == "pdf":
            pages_info = file_service.split_pdf_to_pages(saved_path, document.id)
            if not pages_info:
                raise ValueError("PDF pages could not be rendered for analysis.")
            document.page_count = len(pages_info)
            for page_info in pages_info:
                thumb_path = file_service.create_thumbnail(page_info["image_path"], document.id, page_info["page_no"])
                page = Page(
                    document_id=document.id,
                    page_no=page_info["page_no"],
                    original_path=page_info["image_path"],
                    thumbnail_path=thumb_path,
                    width=page_info["width"],
                    height=page_info["height"],
                    status="pending",
                )
                db.add(page)
                pages.append(page)
        else:
            width, height = file_service.get_image_dimensions(saved_path)
            thumb_path = file_service.create_thumbnail(saved_path, document.id, 1)
            page = Page(
                document_id=document.id,
                page_no=1,
                original_path=saved_path,
                thumbnail_path=thumb_path,
                width=width,
                height=height,
                status="pending",
            )
            db.add(page)
            pages.append(page)
            document.page_count = 1

        db.commit()
        for page in pages:
            db.refresh(page)
        db.refresh(document)
        return document, pages, file_hash
    except Exception:
        db.delete(document)
        db.commit()
        raise


def _authorized_job(job_id: int, current_user: User, db: Session) -> ProcessingJob:
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return job


def _job_payload(job: ProcessingJob) -> dict:
    current_stage = job.status
    return {
        "job_id": job.id,
        "document_id": job.document_id,
        "status": job.status,
        "progress": job.progress,
        "current_stage": current_stage,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.ended_at.isoformat() if job.ended_at else None,
        "error_code": "ANALYSIS_FAILED" if job.status == "FAILED" else None,
        "error_message": job.error_message,
        "result_url": f"/api/v1/document/jobs/{job.id}/result" if job.status == "COMPLETED" else None,
    }


def _find_active_analysis_job(db: Session, *, user_id: int, document_id: Optional[int] = None, file_hash: Optional[str] = None) -> Optional[ProcessingJob]:
    query = db.query(ProcessingJob).filter(
        ProcessingJob.user_id == user_id,
        ProcessingJob.job_type == "full_document_analysis",
        ProcessingJob.status.in_(ACTIVE_JOB_STATUSES),
    )
    if document_id is not None:
        found = query.filter(ProcessingJob.document_id == document_id).first()
        if found:
            return found
    if file_hash:
        found = (
            query.join(Document, ProcessingJob.document_id == Document.id)
            .filter(Document.file_hash == file_hash)
            .first()
        )
        if found:
            return found
    return None


@router.post("/analyze-full", response_model=FullDocumentAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_full_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form("Unknown Ottoman Document"),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    pipeline: DocumentAnalysisPipeline = Depends(get_document_analysis_pipeline),
):
    try:
        document, pages, _ = await _create_uploaded_document(
            file=file,
            title=title,
            description=description,
            current_user=current_user,
            db=db,
        )

        result = await pipeline.analyze_document(
            document=document,
            pages=pages,
            db=db,
            user_id=current_user.id,
        )

        audit = AuditLog(
            actor_id=current_user.id,
            action="document.analyze_full",
            object_type="document",
            object_id=document.id,
            new_value=json.dumps(
                {
                    "filename": file.filename,
                    "pages": document.page_count,
                    "ocr_confidence": result.get("ocr", {}).get("confidence"),
                    "historical_evidence_count": len(
                        result.get("evidence", {}).get("historical_external_evidence", [])
                    ),
                },
                ensure_ascii=False,
            ),
            ip_address=request.client.host if request.client else None,
        )
        db.add(audit)
        db.commit()

        return result

    except HTTPException:
        if "document" in locals():
            db.delete(document)
        db.commit()
        raise
    except Exception as exc:
        if "document" in locals():
            db.delete(document)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Full document analysis failed: {exc}",
        ) from exc


@router.post("/analyze", status_code=status.HTTP_202_ACCEPTED)
async def start_async_document_analysis(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form("Unknown Ottoman Document"),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document: Document | None = None
    try:
        document, pages, file_hash = await _create_uploaded_document(
            file=file,
            title=title,
            description=description,
            current_user=current_user,
            db=db,
        )

        duplicate = _find_active_analysis_job(db, user_id=current_user.id, file_hash=file_hash)
        if duplicate and duplicate.document_id != document.id:
            db.delete(document)
            db.commit()
            return _job_payload(duplicate)

        job = JobManager(db).start_job(
            document_id=document.id,
            user_id=current_user.id,
            job_type="full_document_analysis",
            idempotency_key=f"full-analysis:{current_user.id}:{document.id}",
        )
        job.page_id = pages[0].id if pages else None
        job.parameters = {"title": title, "description": description, "filename": file.filename}
        document.status = "preprocessing"
        audit = AuditLog(
            actor_id=current_user.id,
            action="document.analysis_queued",
            object_type="document",
            object_id=document.id,
            new_value=json.dumps({"job_id": job.id, "filename": file.filename}, ensure_ascii=False),
            ip_address=request.client.host if request.client else None,
        )
        db.add(audit)
        db.commit()
        db.refresh(job)
        payload = _job_payload(job)
        payload["status"] = "QUEUED"
        return payload
    except HTTPException:
        if document is not None:
            db.delete(document)
            db.commit()
        raise
    except Exception as exc:
        if document is not None:
            db.delete(document)
            db.commit()
        raise HTTPException(status_code=500, detail=f"Async document analysis enqueue failed: {exc}") from exc


@router.get("/jobs/{job_id}")
async def get_document_analysis_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _job_payload(_authorized_job(job_id, current_user, db))


@router.get("/jobs/{job_id}/result", response_model=FullDocumentAnalysisResponse)
async def get_document_analysis_job_result(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = _authorized_job(job_id, current_user, db)
    if job.status != "COMPLETED":
        raise HTTPException(status_code=409, detail=f"Analysis job is not completed. Current status: {job.status}")
    if not job.result_summary:
        raise HTTPException(status_code=404, detail="Analysis result is not available")
    try:
        payload = json.loads(job.result_summary)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Stored analysis result is malformed") from exc
    return FullDocumentAnalysisResponse.model_validate(payload)
