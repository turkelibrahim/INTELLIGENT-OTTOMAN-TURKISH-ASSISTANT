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
from app.models.processing_outputs import Entity, TextVersion
from app.models.user import User
from app.services.document_processing.ner_extractor import NERExtractor

router = APIRouter(prefix="/analysis", tags=["Analysis"])


class UserEntityInput(BaseModel):
    entity_type: str = Field(..., pattern="^(PER|LOC|ORG|DATE|MISC|GLOSSARY)$")
    value: str = Field(..., min_length=1)
    normalized_value: Optional[str] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None


class EntityExtractionRequest(BaseModel):
    user_entities: List[UserEntityInput] = []


class EntityResponse(BaseModel):
    id: int
    document_id: int
    text_version_id: int
    entity_type: str
    value: str
    normalized_value: Optional[str]
    start_offset: Optional[int]
    end_offset: Optional[int]
    confidence_score: Optional[float]
    metadata_json: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class EntityExtractionResponse(BaseModel):
    text_version_id: int
    entities: List[EntityResponse]
    glossary: List[dict]
    evaluation: dict
    ocr_impact: dict


@router.post(
    "/text-versions/{text_version_id}/entities",
    response_model=EntityExtractionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def extract_entities_for_text_version(
    text_version_id: int,
    payload: EntityExtractionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    text_version = db.query(TextVersion).filter(TextVersion.id == text_version_id).first()
    if not text_version:
        raise HTTPException(status_code=404, detail="Metin surumu bulunamadi")

    document = db.query(Document).filter(Document.id == text_version.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Belge bulunamadi")
    if document.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Bu belgeye erisim yetkiniz yok")

    extractor = NERExtractor()
    extracted = extractor.extract(text_version.text)
    stored = []
    for item in extracted["entities"]:
        stored.append(_store_entity(db, document.id, text_version.id, item, source="system"))

    for item in payload.user_entities:
        stored.append(
            _store_entity(
                db,
                document.id,
                text_version.id,
                {
                    "entity_type": item.entity_type,
                    "value": item.value,
                    "normalized_value": item.normalized_value or item.value,
                    "start_offset": item.start_offset,
                    "end_offset": item.end_offset,
                    "confidence_score": 1.0,
                    "metadata": {"source": "user_correction"},
                },
                source="user_correction",
            )
        )

    db.commit()
    for entity in stored:
        db.refresh(entity)

    audit = AuditLog(
        actor_id=current_user.id,
        action="entity.extraction.create",
        object_type="text_version",
        object_id=text_version.id,
        old_value=None,
        new_value=json.dumps({"entity_count": len(stored)}, ensure_ascii=False),
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    if payload.user_entities:
        db.add(
            AuditLog(
                actor_id=current_user.id,
                action="entity.user_correction.create",
                object_type="text_version",
                object_id=text_version.id,
                old_value=None,
                new_value=json.dumps([item.model_dump() for item in payload.user_entities], ensure_ascii=False),
                ip_address=request.client.host if request.client else None,
            )
        )
    db.commit()

    predicted_values = [entity.value for entity in stored]
    evaluation = extractor.evaluate_predictions(predicted_values, predicted_values)
    return EntityExtractionResponse(
        text_version_id=text_version.id,
        entities=[EntityResponse.model_validate(entity) for entity in stored],
        glossary=extracted["glossary"],
        evaluation=evaluation,
        ocr_impact=extracted["ocr_impact"],
    )


def _store_entity(db: Session, document_id: int, text_version_id: int, item: dict, *, source: str) -> Entity:
    metadata = dict(item.get("metadata") or {})
    metadata["source"] = source
    entity = Entity(
        document_id=document_id,
        text_version_id=text_version_id,
        entity_type=item["entity_type"],
        value=item["value"],
        normalized_value=item.get("normalized_value"),
        start_offset=item.get("start_offset"),
        end_offset=item.get("end_offset"),
        confidence_score=item.get("confidence_score"),
        metadata_json=metadata,
    )
    db.add(entity)
    return entity
