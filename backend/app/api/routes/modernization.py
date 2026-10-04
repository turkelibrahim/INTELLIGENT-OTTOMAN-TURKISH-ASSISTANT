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
from app.services.document_processing.translator import Translator

router = APIRouter(prefix="/modernization", tags=["Modernization"])


class ModernizationRequest(BaseModel):
    mode: str = Field(..., pattern="^(faithful|plain|summary)$")
    text: Optional[str] = Field(default=None, min_length=1)


class ModernizationResponse(BaseModel):
    text_version_id: int
    document_id: int
    page_id: Optional[int]
    source_version_id: int
    ocr_result_id: Optional[int]
    mode: str
    version_type: str
    source_text: str
    output_text: str
    previous_text: Optional[str]
    confidence_score: float
    prompt_version: str
    provider: str
    safety_warnings: List[str]
    preserved_terms: List[str]
    created_at: datetime


@router.post(
    "/text-versions/{source_version_id}",
    response_model=ModernizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_modernization(
    source_version_id: int,
    payload: ModernizationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    source_version = db.query(TextVersion).filter(TextVersion.id == source_version_id).first()
    if not source_version:
        raise HTTPException(status_code=404, detail="Kaynak metin surumu bulunamadi")

    document = db.query(Document).filter(Document.id == source_version.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Belge bulunamadi")
    if document.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Bu belgeye erisim yetkiniz yok")

    page = db.query(Page).filter(Page.id == source_version.page_id).first() if source_version.page_id else None
    ocr_result = (
        db.query(OCRResult).filter(OCRResult.id == source_version.ocr_result_id).first()
        if source_version.ocr_result_id
        else None
    )
    source_text = payload.text or source_version.text
    latest = _latest_modernization(source_version.id, payload.mode, db)
    previous_text = latest.text if latest else None
    result = Translator().modernize(
        source_text,
        mode=payload.mode,
        source_version_id=source_version.id,
        source_ocr_result_id=source_version.ocr_result_id,
        line_no=ocr_result.line_no if ocr_result else None,
    )
    version_type = f"modernization_{payload.mode}"

    text_version = TextVersion(
        document_id=document.id,
        page_id=source_version.page_id,
        ocr_result_id=source_version.ocr_result_id,
        user_id=current_user.id,
        version_type=version_type,
        text=result.output_text,
        previous_text=previous_text,
        source_version_id=latest.id if latest else source_version.id,
        confidence_score=result.confidence,
    )
    db.add(text_version)
    db.commit()
    db.refresh(text_version)

    action = "modernization.correction.create" if latest else "modernization.create"
    audit = AuditLog(
        actor_id=current_user.id,
        action=action,
        object_type="text_version",
        object_id=text_version.id,
        old_value=json.dumps({"text": previous_text}, ensure_ascii=False),
        new_value=json.dumps(result.to_dict(), ensure_ascii=False),
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()

    return ModernizationResponse(
        text_version_id=text_version.id,
        document_id=document.id,
        page_id=source_version.page_id,
        source_version_id=source_version.id,
        ocr_result_id=source_version.ocr_result_id,
        mode=result.mode,
        version_type=version_type,
        source_text=source_text,
        output_text=result.output_text,
        previous_text=previous_text,
        confidence_score=result.confidence,
        prompt_version=result.prompt_version,
        provider=result.provider,
        safety_warnings=result.safety_warnings,
        preserved_terms=result.preserved_terms,
        created_at=text_version.created_at,
    )


def _latest_modernization(source_version_id: int, mode: str, db: Session) -> Optional[TextVersion]:
    return (
        db.query(TextVersion)
        .filter(
            TextVersion.source_version_id == source_version_id,
            TextVersion.version_type == f"modernization_{mode}",
        )
        .order_by(TextVersion.created_at.desc(), TextVersion.id.desc())
        .first()
    )
