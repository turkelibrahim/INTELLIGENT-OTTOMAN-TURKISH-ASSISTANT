from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.export import ExportEligibilityReport, ExportMetadata, ExportResponse
from app.services.export_service import ExportService
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

def get_export_service(db: Session = Depends(get_db)):
    raw_conn = db.connection().connection.dbapi_connection
    return ExportService(raw_conn)

@router.post("/datasets/{dataset_id}/exports/pagexml", response_model=ExportMetadata, status_code=201)
def export_pagexml(
    dataset_id: int, 
    is_test_export: bool = Query(False),
    service: ExportService = Depends(get_export_service), 
    current_user: User = Depends(get_current_user)
):
    return service.export_pagexml(dataset_id, is_test_export, str(current_user.id))

@router.post("/datasets/{dataset_id}/exports/kraken", response_model=ExportMetadata, status_code=201)
def export_kraken(
    dataset_id: int, 
    is_test_export: bool = Query(False),
    service: ExportService = Depends(get_export_service), 
    current_user: User = Depends(get_current_user)
):
    return service.export_kraken(dataset_id, is_test_export, str(current_user.id))

@router.get("/datasets/{dataset_id}/exports", response_model=List[ExportResponse])
def list_exports(dataset_id: int, service: ExportService = Depends(get_export_service), current_user: User = Depends(get_current_user)):
    cur = service.db.cursor()
    cur.execute("SELECT id, dataset_id, export_type, status, output_path, output_sha256, is_test_export, created_by, created_at, completed_at, error_message FROM annotation_exports WHERE dataset_id=?", (dataset_id,))
    exports = []
    for r in cur.fetchall():
        exports.append(ExportResponse(
            id=r[0], dataset_id=r[1], export_type=r[2], status=r[3], output_path=r[4], output_sha256=r[5],
            is_test_export=bool(r[6]), created_by=r[7], created_at=r[8], completed_at=r[9], error_message=r[10]
        ))
    return exports

@router.get("/exports/{export_id}", response_model=ExportResponse)
def get_export(export_id: int, service: ExportService = Depends(get_export_service), current_user: User = Depends(get_current_user)):
    cur = service.db.cursor()
    cur.execute("SELECT id, dataset_id, export_type, status, output_path, output_sha256, is_test_export, created_by, created_at, completed_at, error_message FROM annotation_exports WHERE id=?", (export_id,))
    r = cur.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Export not found")
    return ExportResponse(
        id=r[0], dataset_id=r[1], export_type=r[2], status=r[3], output_path=r[4], output_sha256=r[5],
        is_test_export=bool(r[6]), created_by=r[7], created_at=r[8], completed_at=r[9], error_message=r[10]
    )

@router.get("/exports/{export_id}/manifest")
def get_export_manifest(export_id: int, service: ExportService = Depends(get_export_service), current_user: User = Depends(get_current_user)):
    # Mock
    return {"status": "ok"}

@router.get("/exports/{export_id}/download")
def download_export(export_id: int, service: ExportService = Depends(get_export_service), current_user: User = Depends(get_current_user)):
    # Mock
    return {"status": "ok"}
