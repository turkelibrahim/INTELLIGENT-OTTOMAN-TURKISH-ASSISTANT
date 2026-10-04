from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.annotation import (
    AnnotationDatasetCreate, AnnotationDatasetUpdate, AnnotationDatasetResponse, AnnotationDatasetProgressResponse,
    AnnotationDocumentCreate, AnnotationDocumentResponse,
    AnnotationPageCreate, AnnotationPageResponse,
    AnnotationRegionCreate, AnnotationRegionUpdate, AnnotationRegionResponse,
    AnnotationLineCreate, AnnotationLineUpdate, AnnotationLineResponse,
    NeedsCorrectionRequest, HumanVerificationRequest, SecondReviewRequest, DatasetLockRequest,
    AnnotationAuditEventResponse
)
from app.services.annotation_service import AnnotationService
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

def get_service(db: Session = Depends(get_db)):
    # AnnotationService expects a raw sqlite3.Connection
    raw_conn = db.connection().connection.dbapi_connection
    return AnnotationService(raw_conn)

# DATASETS
@router.post("/datasets", response_model=AnnotationDatasetResponse)
def create_dataset(req: AnnotationDatasetCreate, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.create_dataset(req, str(current_user.id))

@router.get("/datasets", response_model=List[AnnotationDatasetResponse])
def list_datasets(service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.list_datasets()

@router.get("/datasets/{dataset_id}", response_model=AnnotationDatasetResponse)
def get_dataset(dataset_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.get_dataset(dataset_id)

@router.patch("/datasets/{dataset_id}", response_model=AnnotationDatasetResponse)
def update_dataset(dataset_id: int, req: AnnotationDatasetUpdate, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.update_dataset(dataset_id, req, str(current_user.id))

@router.get("/datasets/{dataset_id}/progress", response_model=AnnotationDatasetProgressResponse)
def get_dataset_progress(dataset_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.get_dataset_progress(dataset_id)

@router.post("/datasets/{dataset_id}/lock")
def lock_dataset(dataset_id: int, req: DatasetLockRequest, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    service.lock_dataset(dataset_id, str(current_user.id))
    return {"message": "Dataset locked"}

@router.get("/datasets/{dataset_id}/audit", response_model=List[AnnotationAuditEventResponse])
def get_dataset_audit(dataset_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.get_dataset_audit(dataset_id)

# DOCUMENTS
@router.post("/datasets/{dataset_id}/documents", response_model=AnnotationDocumentResponse)
def create_document(dataset_id: int, req: AnnotationDocumentCreate, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.create_document(dataset_id, req, str(current_user.id))

@router.get("/datasets/{dataset_id}/documents", response_model=List[AnnotationDocumentResponse])
def list_documents(dataset_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.list_documents(dataset_id)

@router.get("/documents/{document_id}", response_model=AnnotationDocumentResponse)
def get_document(document_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.get_document(document_id)

# PAGES
@router.post("/documents/{document_id}/pages", response_model=AnnotationPageResponse)
def create_page(document_id: int, req: AnnotationPageCreate, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.create_page(document_id, req, str(current_user.id))

@router.get("/documents/{document_id}/pages", response_model=List[AnnotationPageResponse])
def list_pages(document_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.list_pages(document_id)

@router.get("/pages/{page_id}", response_model=AnnotationPageResponse)
def get_page(page_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.get_page(page_id)

# REGIONS
@router.post("/pages/{page_id}/regions", response_model=AnnotationRegionResponse)
def create_region(page_id: int, req: AnnotationRegionCreate, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.create_region(page_id, req, str(current_user.id))

@router.get("/pages/{page_id}/regions", response_model=List[AnnotationRegionResponse])
def list_regions(page_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.list_regions(page_id)

@router.patch("/regions/{region_id}", response_model=AnnotationRegionResponse)
def update_region(region_id: int, req: AnnotationRegionUpdate, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.update_region(region_id, req, str(current_user.id))

@router.delete("/regions/{region_id}")
def delete_region(region_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    service.delete_region(region_id, str(current_user.id))
    return {"message": "Deleted"}

# LINES
@router.post("/pages/{page_id}/lines", response_model=AnnotationLineResponse)
def create_line(page_id: int, req: AnnotationLineCreate, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.create_line(page_id, req, str(current_user.id))

@router.get("/pages/{page_id}/lines", response_model=List[AnnotationLineResponse])
def list_lines(page_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.list_lines(page_id)

@router.get("/lines/{line_id}", response_model=AnnotationLineResponse)
def get_line(line_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.get_line(line_id)

@router.patch("/lines/{line_id}", response_model=AnnotationLineResponse)
def update_line(line_id: int, req: AnnotationLineUpdate, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.update_line(line_id, req, str(current_user.id))

@router.delete("/lines/{line_id}")
def delete_line(line_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    service.delete_line(line_id, str(current_user.id))
    return {"message": "Deleted"}

# REVIEWS
@router.post("/lines/{line_id}/needs-correction")
def mark_needs_correction(line_id: int, req: NeedsCorrectionRequest, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    service.mark_needs_correction(line_id, req, str(current_user.id))
    return {"message": "Marked for correction"}

@router.post("/lines/{line_id}/verify")
def human_verify_line(line_id: int, req: HumanVerificationRequest, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    service.human_verify_line(line_id, req, str(current_user.id))
    return {"message": "Verified"}

@router.post("/lines/{line_id}/second-review")
def second_review_line(line_id: int, req: SecondReviewRequest, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    service.second_review_line(line_id, req, str(current_user.id))
    return {"message": "Second review submitted"}

# AUDIT
@router.get("/lines/{line_id}/history", response_model=List[AnnotationAuditEventResponse])
def get_line_history(line_id: int, service: AnnotationService = Depends(get_service), current_user: User = Depends(get_current_user)):
    return service.get_line_history(line_id)
