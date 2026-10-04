import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.page import Page
from app.models.processing_outputs import OCRResult, TextVersion
from app.models.user import User

router = APIRouter(prefix="/ocr-review", tags=["OCR Review"])


class OCRLineResponse(BaseModel):
    id: int
    page_id: int
    line_no: Optional[int]
    bbox: Optional[dict]
    raw_text: str
    confidence_score: Optional[float]
    latest_correction: Optional[str] = None


class CorrectionCreate(BaseModel):
    text: str = Field(..., min_length=1)
    expected_previous_text: Optional[str] = None


class TextVersionResponse(BaseModel):
    id: int
    document_id: int
    page_id: Optional[int]
    ocr_result_id: Optional[int]
    version_type: str
    text: str
    previous_text: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/pages/{page_id}/lines", response_model=List[OCRLineResponse])
async def list_review_lines(
    page_id: int,
    low_confidence_only: bool = False,
    threshold: float = 0.75,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    page, _ = _get_authorized_page(page_id, current_user, db)
    query = db.query(OCRResult).filter(OCRResult.page_id == page.id)
    if low_confidence_only:
        query = query.filter(OCRResult.confidence_score < threshold)

    lines = query.order_by(OCRResult.line_no.asc().nullslast(), OCRResult.id.asc()).all()
    return [
        OCRLineResponse(
            id=line.id,
            page_id=line.page_id,
            line_no=line.line_no,
            bbox=line.bbox,
            raw_text=line.raw_text,
            confidence_score=line.confidence_score,
            latest_correction=_latest_correction_text(line.id, db),
        )
        for line in lines
    ]


@router.post(
    "/ocr-results/{ocr_result_id}/corrections",
    response_model=TextVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_correction(
    ocr_result_id: int,
    correction: CorrectionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ocr_result = db.query(OCRResult).filter(OCRResult.id == ocr_result_id).first()
    if not ocr_result:
        raise HTTPException(status_code=404, detail="OCR sonucu bulunamadi")

    page, document = _get_authorized_page(ocr_result.page_id, current_user, db)
    previous_text = _latest_correction_text(ocr_result.id, db) or ocr_result.raw_text
    
    if correction.expected_previous_text is not None and previous_text != correction.expected_previous_text:
        raise HTTPException(status_code=409, detail="Conflict: Bu satir baska bir oturum tarafindan degistirilmis. Lutfen sayfayi yenileyin.")

    text_version = TextVersion(
        document_id=document.id,
        page_id=page.id,
        ocr_result_id=ocr_result.id,
        user_id=current_user.id,
        version_type="ocr_correction",
        text=correction.text,
        previous_text=previous_text,
        confidence_score=ocr_result.confidence_score,
    )
    db.add(text_version)
    db.commit()
    db.refresh(text_version)

    audit = AuditLog(
        actor_id=current_user.id,
        action="ocr.correction.create",
        object_type="text_version",
        object_id=text_version.id,
        old_value=json.dumps({"text": previous_text}, ensure_ascii=False),
        new_value=json.dumps({"text": correction.text}, ensure_ascii=False),
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    
    # Mark downstreams as stale by appending _stale to version_type
    db.query(TextVersion).filter(
        TextVersion.ocr_result_id == ocr_result.id,
        TextVersion.version_type.in_(["transliteration", "modern_turkish"])
    ).update(
        {"version_type": TextVersion.version_type + "_stale"},
        synchronize_session=False
    )
    db.commit()

    return TextVersionResponse.model_validate(text_version)


def _latest_correction_text(ocr_result_id: int, db: Session) -> Optional[str]:
    latest = (
        db.query(TextVersion)
        .filter(
            TextVersion.ocr_result_id == ocr_result_id,
            TextVersion.version_type == "ocr_correction",
        )
        .order_by(TextVersion.created_at.desc(), TextVersion.id.desc())
        .first()
    )
    return latest.text if latest else None


def _get_authorized_page(page_id: int, current_user: User, db: Session) -> tuple[Page, Document]:
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Sayfa bulunamadi")

    document = db.query(Document).filter(Document.id == page.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Belge bulunamadi")
    if document.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Bu belgeye erisim yetkiniz yok")

    return page, document
