from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.processing_job import ProcessingJob

router = APIRouter(prefix="/documents/{document_id}/ocr", tags=["OCR"])

def _get_authorized_document(document_id: int, current_user: User, db: Session) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Belge bulunamadı")
    if document.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Erişim engellendi")
    return document

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def trigger_ocr(
    document_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """OCR işlemini asenkron başlatır."""
    document = _get_authorized_document(document_id, current_user, db)
    
    # Mevcut devam eden job var mı kontrol et
    existing_job = db.query(ProcessingJob).filter(
        ProcessingJob.document_id == document.id,
        ProcessingJob.status.in_([
            "QUEUED", "PREPROCESSING", "LAYOUT_ANALYSIS", 
            "OCR_RUNNING", "TRANSLITERATING", "MODERNIZING", 
            "NER_RUNNING", "pending", "running"
        ])
    ).first()
    
    if existing_job:
        return {"job_id": existing_job.id, "status": existing_job.status}
        
    job = ProcessingJob(
        document_id=document.id,
        user_id=current_user.id,
        job_type="full_pipeline",
        status="QUEUED",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return {"job_id": job.id, "status": "QUEUED"}

@router.get("/status")
async def get_ocr_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """OCR iş durumunu döner."""
    document = _get_authorized_document(document_id, current_user, db)
    
    # En son job'ı bul
    job = db.query(ProcessingJob).filter(
        ProcessingJob.document_id == document.id
    ).order_by(ProcessingJob.created_at.desc()).first()
    
    if not job:
        return {"status": "none"}
        
    # Eğer tamamlanmışsa veritabanından sonucu al
    result = {}
    completed_statuses = ["COMPLETED", "OCR_LOW_QUALITY", "PARTIAL", "completed"]
    if job.status in completed_statuses:
        import json
        try:
            result = json.loads(job.result_summary) if job.result_summary else {}
        except json.JSONDecodeError:
            result = {}
            
    # For frontend compatibility, map backend statuses to frontend expected payload if needed
    if result and "pipeline_results" not in result:
        # Wrap the new schema in the old schema format for frontend compatibility during migration
        result = {
            "status": "success",
            "pipeline_results": {
                "original_ocr_text": result.get("raw_ocr_text", ""),
                "transliterated_text": result.get("transliterated_text", ""),
                "modernized_text": result.get("modernized_text", ""),
                "summary_text": result.get("summary_text", ""),
                "ner_results": result.get("entities", []),
                "lines": result.get("lines", []),
                "image_width": 0, # Could extract if needed
                "image_height": 0,
                "transformation_quality": result.get("transformation_quality", {})
            },
            "confidence_scores": {
                "preprocessing": result.get("quality", {}).get("input_quality", 0.0),
                "ocr": result.get("quality", {}).get("ocr_confidence", 0.0),
                "translation": 0.0,
                "ner": 0.0,
                "overall": result.get("quality", {}).get("ocr_confidence", 0.0)
            },
            "warnings": result.get("warnings", [])
        }
        
    return {
        "job_id": job.id,
        "status": job.status,
        "result": result if job.status in completed_statuses else None,
        "error": job.error_message
    }
