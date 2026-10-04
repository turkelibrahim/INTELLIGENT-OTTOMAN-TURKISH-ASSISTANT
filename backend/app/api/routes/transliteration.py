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

router = APIRouter(prefix="/transliteration", tags=["Transliteration"])


class TransliterationRequest(BaseModel):
    text: Optional[str] = Field(default=None, min_length=1)


class TransliterationCandidateResponse(BaseModel):
    text: str
    rationale: str
    ambiguity_level: str


class TransliterationResponse(BaseModel):
    text_version_id: int
    document_id: int
    page_id: int
    ocr_result_id: int
    source_text: str
    transliterated_text: str
    previous_text: Optional[str]
    confidence_score: float
    ambiguity_level: str
    method_version: str
    candidates: List[TransliterationCandidateResponse]
    created_at: datetime


@router.post(
    "/ocr-results/{ocr_result_id}",
    response_model=TransliterationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transliteration(
    ocr_result_id: int,
    payload: TransliterationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ocr_result = db.query(OCRResult).filter(OCRResult.id == ocr_result_id).first()
    if not ocr_result:
        raise HTTPException(status_code=404, detail="OCR sonucu bulunamadi")

    page, document = _get_authorized_page(ocr_result.page_id, current_user, db)
    latest = _latest_transliteration(ocr_result.id, db)
    source_text = payload.text or _latest_correction_text(ocr_result.id, db) or ocr_result.raw_text
    result = Translator().transliterate_line(
        source_text,
        source_ocr_result_id=ocr_result.id,
        line_no=ocr_result.line_no,
    )
    previous_text = latest.text if latest else None

    text_version = TextVersion(
        document_id=document.id,
        page_id=page.id,
        ocr_result_id=ocr_result.id,
        user_id=current_user.id,
        version_type="transliteration",
        text=result.transliterated_text,
        previous_text=previous_text,
        source_version_id=latest.id if latest else None,
        confidence_score=result.confidence,
    )
    db.add(text_version)
    db.commit()
    db.refresh(text_version)

    action = "transliteration.correction.create" if latest else "transliteration.create"
    audit = AuditLog(
        actor_id=current_user.id,
        action=action,
        object_type="text_version",
        object_id=text_version.id,
        old_value=json.dumps({"text": previous_text}, ensure_ascii=False),
        new_value=json.dumps(
            {
                "text": result.transliterated_text,
                "source_ocr_result_id": ocr_result.id,
                "method_version": result.method_version,
                "ambiguity_level": result.ambiguity_level,
            },
            ensure_ascii=False,
        ),
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()

    return TransliterationResponse(
        text_version_id=text_version.id,
        document_id=document.id,
        page_id=page.id,
        ocr_result_id=ocr_result.id,
        source_text=source_text,
        transliterated_text=result.transliterated_text,
        previous_text=previous_text,
        confidence_score=result.confidence,
        ambiguity_level=result.ambiguity_level,
        method_version=result.method_version,
        candidates=[candidate.__dict__ for candidate in result.candidates],
        created_at=text_version.created_at,
    )


def _latest_transliteration(ocr_result_id: int, db: Session) -> Optional[TextVersion]:
    return (
        db.query(TextVersion)
        .filter(
            TextVersion.ocr_result_id == ocr_result_id,
            TextVersion.version_type == "transliteration",
        )
        .order_by(TextVersion.created_at.desc(), TextVersion.id.desc())
        .first()
    )


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
