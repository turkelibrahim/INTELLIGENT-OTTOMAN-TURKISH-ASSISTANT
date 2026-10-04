from __future__ import annotations

import csv
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.ground_truth import (
    Dataset,
    GroundTruthLine,
    GroundTruthPage,
    GroundTruthReviewAudit,
    GroundTruthStatus,
)
from app.models.page import Page
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.services.evaluation.metrics import evaluate_page

router = APIRouter(prefix="/ground-truth", tags=["ground-truth"])

PROJECT_ROOT = Path(__file__).resolve().parents[4]
PILOT_INPUT_ROOT = PROJECT_ROOT / "evidence" / "ocr_quality_real" / "input"


class ReviewLineRequest(BaseModel):
    text_content: str = Field(min_length=1)
    bounding_box: List[float] = Field(min_length=4, max_length=4)
    text_reviewed: bool
    bbox_reviewed: bool
    reviewer_display_name: str | None = None


class ReadyToLockRequest(BaseModel):
    rights_confirmed: bool


def reviewer_name(user: User) -> str:
    return user.full_name or user.username or user.email


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pilot_metadata() -> list[dict[str, str]]:
    metadata_path = PILOT_INPUT_ROOT / "metadata.csv"
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="Pilot metadata.csv not found")
    with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def load_line_boxes() -> dict[str, list[dict[str, Any]]]:
    sidecar = PILOT_INPUT_ROOT / "line_boxes.draft.json"
    if not sidecar.exists():
        raise HTTPException(status_code=404, detail="Pilot line_boxes.draft.json not found")
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    return {page["page_id"]: page.get("lines", []) for page in payload.get("pages", [])}


def get_owned_dataset(db: Session, dataset_id: int, user: User) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this dataset")
    return dataset


def get_owned_page(db: Session, page_id: int, user: User) -> GroundTruthPage:
    page = db.query(GroundTruthPage).filter(GroundTruthPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    if page.dataset.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this page")
    return page


def review_progress(db: Session, dataset: Dataset) -> dict[str, Any]:
    pages = db.query(GroundTruthPage).filter(GroundTruthPage.dataset_id == dataset.id).order_by(GroundTruthPage.id).all()
    page_ids = [page.id for page in pages]
    lines = (
        db.query(GroundTruthLine)
        .filter(GroundTruthLine.page_id.in_(page_ids))
        .order_by(GroundTruthLine.page_id, GroundTruthLine.reading_order)
        .all()
        if page_ids
        else []
    )
    total = len(lines)
    text_reviewed = sum(1 for line in lines if line.text_reviewed)
    bbox_reviewed = sum(1 for line in lines if line.bbox_reviewed)
    corrected = sum(1 for line in lines if line.text_changed or line.bbox_changed)
    page_progress = []
    for page in pages:
        page_lines = [line for line in lines if line.page_id == page.id]
        page_progress.append(
            {
                "page_id": page.id,
                "source_page_id": page.metadata_json.get("source_page_id") if page.metadata_json else None,
                "total": len(page_lines),
                "text_reviewed": sum(1 for line in page_lines if line.text_reviewed),
                "bbox_reviewed": sum(1 for line in page_lines if line.bbox_reviewed),
                "status": page.annotation_status,
            }
        )
    return {
        "dataset_id": dataset.id,
        "dataset_status": dataset.status,
        "annotation_status": "LOCKED" if dataset.status == "LOCKED" else dataset.metadata_json.get("annotation_status", "ASSISTED_ANNOTATION_DRAFT") if dataset.metadata_json else dataset.status,
        "total_lines": total,
        "text_reviewed": text_reviewed,
        "bbox_reviewed": bbox_reviewed,
        "corrected": corrected,
        "pending": max(total - min(text_reviewed, bbox_reviewed), 0),
        "percent": round((min(text_reviewed, bbox_reviewed) / total) * 100, 2) if total else 0,
        "pages": page_progress,
    }


@router.post("/pilot-draft/import")
def import_pilot_draft(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = load_pilot_metadata()
    line_boxes = load_line_boxes()
    manifest_path = PROJECT_ROOT / "evidence" / "ocr_quality_real" / "source_zip_provenance.md"
    source_manifest_hash = file_sha256(PILOT_INPUT_ROOT / "metadata.csv")

    existing = (
        db.query(Dataset)
        .filter(Dataset.owner_id == current_user.id, Dataset.source == "osmaluca_pilot_001")
        .first()
    )
    if existing:
        return {"dataset": existing, "progress": review_progress(db, existing), "created": False}

    dataset = Dataset(
        name="Osmanlica Pilot Review",
        description="AI destekli taslak - insan dogrulamasi gereklidir",
        source="osmaluca_pilot_001",
        license="user_provided_rights_not_independently_verified",
        owner_id=current_user.id,
        status="ASSISTED_ANNOTATION_DRAFT",
        version="1.0.0",
        manifest_sha256=source_manifest_hash,
        metadata_json={
            "annotation_status": "ASSISTED_ANNOTATION_DRAFT",
            "human_verified": False,
            "review_type": "HUMAN_REVIEWED_ASSISTED_ANNOTATION",
            "source_provenance": str(manifest_path),
        },
    )
    db.add(dataset)
    db.flush()

    for row in rows:
        source_page_id = row["page_id"]
        image_path = PILOT_INPUT_ROOT / "images" / f"{source_page_id}.png"
        gt_path = PILOT_INPUT_ROOT / "transcriptions" / f"{source_page_id}.gt.txt"
        page = GroundTruthPage(
            dataset_id=dataset.id,
            original_image_hash=file_sha256(image_path),
            image_path=os.fspath(image_path),
            image_width=2550,
            image_height=3300,
            document_type=row.get("print_or_handwriting"),
            print_quality=row.get("image_quality"),
            font_type=row.get("typography"),
            split_type="dev" if source_page_id == "page_001" else "test",
            annotation_status=GroundTruthStatus.IN_REVIEW,
            metadata_json={**row, "source_page_id": source_page_id},
        )
        db.add(page)
        db.flush()

        texts = gt_path.read_text(encoding="utf-8").splitlines()
        boxes = line_boxes.get(source_page_id, [])
        for index, text in enumerate(texts):
            bbox = boxes[index]["bbox_xyxy"] if index < len(boxes) else [0, 0, 0, 0]
            db.add(
                GroundTruthLine(
                    page_id=page.id,
                    bounding_box=bbox,
                    reading_order=index,
                    text_content=text,
                    draft_text=text,
                    annotator_id=current_user.id,
                    status=GroundTruthStatus.IN_REVIEW,
                    notes="AI destekli taslak - insan dogrulamasi gereklidir",
                )
            )

    db.commit()
    db.refresh(dataset)
    return {"dataset": dataset, "progress": review_progress(db, dataset), "created": True}


@router.post("/datasets")
def create_dataset(
    name: str,
    description: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = Dataset(name=name, description=description, owner_id=current_user.id)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Dataset).filter(Dataset.owner_id == current_user.id).order_by(Dataset.created_at.desc()).all()


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_owned_dataset(db, dataset_id, current_user)


@router.get("/datasets/{dataset_id}/progress")
def get_dataset_progress(dataset_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return review_progress(db, get_owned_dataset(db, dataset_id, current_user))


@router.get("/datasets/{dataset_id}/pages")
def list_dataset_pages(dataset_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_owned_dataset(db, dataset_id, current_user)
    return db.query(GroundTruthPage).filter(GroundTruthPage.dataset_id == dataset_id).order_by(GroundTruthPage.id).all()


@router.post("/datasets/{dataset_id}/pages")
def add_page_to_dataset(
    dataset_id: int,
    original_image_hash: str,
    document_id: int = None,
    page_id: int = None,
    split_type: str = "test",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_owned_dataset(db, dataset_id, current_user)
    page = GroundTruthPage(
        dataset_id=dataset.id,
        original_image_hash=original_image_hash,
        document_id=document_id,
        page_id=page_id,
        split_type=split_type,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


@router.get("/pages/{page_id}/image")
def get_ground_truth_page_image(page_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    page = get_owned_page(db, page_id, current_user)
    if page.image_path and os.path.exists(page.image_path):
        return FileResponse(page.image_path, media_type="image/png", filename=f"ground_truth_page_{page_id}.png")
    if not page.page_id:
        raise HTTPException(status_code=404, detail="Linked document page not found")
    document_page = db.query(Page).filter(Page.id == page.page_id).first()
    if not document_page or document_page.document_id != page.document_id or not os.path.exists(document_page.original_path):
        raise HTTPException(status_code=404, detail="Linked document page not found")
    return FileResponse(document_page.original_path, media_type="image/png", filename=f"ground_truth_page_{page_id}.png")


@router.get("/pages/{page_id}")
def get_ground_truth_page(page_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_owned_page(db, page_id, current_user)


@router.get("/pages/{page_id}/lines")
def get_page_lines(page_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_owned_page(db, page_id, current_user)
    return db.query(GroundTruthLine).filter(GroundTruthLine.page_id == page_id).order_by(GroundTruthLine.reading_order).all()


@router.post("/pages/{page_id}/lines")
def save_page_lines(
    page_id: int,
    lines_data: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    page = get_owned_page(db, page_id, current_user)
    if page.annotation_status == GroundTruthStatus.LOCKED:
        raise HTTPException(status_code=400, detail="Page is locked and cannot be modified directly.")
    db.query(GroundTruthLine).filter(GroundTruthLine.page_id == page_id).delete()
    new_lines = []
    for item in lines_data:
        line = GroundTruthLine(
            page_id=page_id,
            bounding_box=item.get("bounding_box", []),
            reading_order=item.get("reading_order", 0),
            text_content=item.get("text_content", ""),
            draft_text=item.get("text_content", ""),
            annotator_id=current_user.id,
            status=GroundTruthStatus.IN_REVIEW,
        )
        db.add(line)
        new_lines.append(line)
    page.annotation_status = GroundTruthStatus.IN_REVIEW
    db.commit()
    for line in new_lines:
        db.refresh(line)
    return {"message": f"Saved {len(new_lines)} lines for review.", "lines": new_lines}


@router.patch("/lines/{line_id}/review")
def review_line(
    line_id: int,
    payload: ReviewLineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.reviewer_display_name:
        raise HTTPException(status_code=400, detail="Reviewer identity is derived from authenticated user")
    line = db.query(GroundTruthLine).filter(GroundTruthLine.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    page = get_owned_page(db, line.page_id, current_user)
    if page.annotation_status == GroundTruthStatus.LOCKED:
        raise HTTPException(status_code=400, detail="Locked lines are immutable")
    previous_text = line.text_content
    previous_bbox = line.bounding_box
    action_id = uuid.uuid4().hex
    line.text_content = payload.text_content
    line.bounding_box = payload.bounding_box
    line.text_reviewed = payload.text_reviewed
    line.bbox_reviewed = payload.bbox_reviewed
    line.text_changed = (line.draft_text or previous_text) != payload.text_content
    line.bbox_changed = previous_bbox != payload.bounding_box
    line.reviewer_id = current_user.id
    line.reviewed_at = datetime.now(timezone.utc)
    line.review_action_id = action_id
    line.status = GroundTruthStatus.REVIEWED if payload.text_reviewed and payload.bbox_reviewed else GroundTruthStatus.IN_REVIEW
    db.add(
        GroundTruthReviewAudit(
            dataset_id=page.dataset_id,
            page_id=page.id,
            line_id=line.id,
            reviewer_id=current_user.id,
            reviewer_display_name=reviewer_name(current_user),
            action="ground_truth.line.review",
            previous_text=previous_text,
            new_text=payload.text_content,
            text_changed=previous_text != payload.text_content,
            previous_bbox=previous_bbox,
            new_bbox=payload.bounding_box,
            bbox_changed=previous_bbox != payload.bounding_box,
            source_image_hash=page.original_image_hash,
            review_action_id=action_id,
            dataset_version=page.dataset.version,
        )
    )
    db.commit()
    db.refresh(line)
    return {"line": line, "progress": review_progress(db, page.dataset)}


def validate_dataset_can_lock(db: Session, dataset: Dataset) -> list[str]:
    errors: list[str] = []
    pages = db.query(GroundTruthPage).filter(GroundTruthPage.dataset_id == dataset.id).all()
    if len(pages) != 3:
        errors.append("Pilot dataset must contain exactly 3 pages")
    lines = db.query(GroundTruthLine).filter(GroundTruthLine.page_id.in_([page.id for page in pages])).all()
    if len(lines) != 73:
        errors.append("Pilot dataset must contain exactly 73 lines")
    for line in lines:
        if not line.text_content.strip():
            errors.append(f"Line {line.id} has empty text")
        if not line.text_reviewed:
            errors.append(f"Line {line.id} text is not reviewed")
        if not line.bbox_reviewed:
            errors.append(f"Line {line.id} bbox is not reviewed")
        if not line.reviewer_id or not line.reviewed_at:
            errors.append(f"Line {line.id} lacks authenticated reviewer audit")
    for page in pages:
        page_lines = [line for line in lines if line.page_id == page.id]
        orders = sorted(line.reading_order for line in page_lines)
        if orders != list(range(len(page_lines))):
            errors.append(f"Page {page.id} reading order is not contiguous")
        for line in page_lines:
            x1, y1, x2, y2 = line.bounding_box
            if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
                errors.append(f"Line {line.id} bbox is invalid")
            if page.image_width and page.image_height and (x2 > page.image_width or y2 > page.image_height):
                errors.append(f"Line {line.id} bbox is out of bounds")
    return errors


@router.post("/datasets/{dataset_id}/ready-to-lock")
def mark_dataset_ready_to_lock(
    dataset_id: int,
    payload: ReadyToLockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_owned_dataset(db, dataset_id, current_user)
    if not payload.rights_confirmed:
        raise HTTPException(status_code=400, detail="Rights/provenance confirmation is required")
    errors = validate_dataset_can_lock(db, dataset)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors[:20], "total_errors": len(errors)})
    dataset.status = GroundTruthStatus.REVIEWED_READY_TO_LOCK.value
    dataset.metadata_json = {**(dataset.metadata_json or {}), "rights_confirmed": True, "human_verified": True}
    for page in dataset.pages:
        page.annotation_status = GroundTruthStatus.REVIEWED_READY_TO_LOCK
    db.commit()
    return {"message": "Dataset reviewed and ready to lock", "progress": review_progress(db, dataset)}


def create_evaluation_job(db: Session, dataset: Dataset, user_id: int) -> ProcessingJob:
    idempotency_key = f"pilot-eval:{dataset.id}:{dataset.version}"
    existing = db.query(ProcessingJob).filter(ProcessingJob.idempotency_key == idempotency_key).first()
    if existing:
        return existing
    result_path = os.fspath(PROJECT_ROOT / "evidence" / "human_review_gate" / "automatic_evaluation_job.json")
    job = ProcessingJob(
        document_id=None,
        user_id=user_id,
        job_type="pilot_ocr_evaluation",
        status="pending",
        parameters={
            "dataset_id": dataset.id,
            "dataset_version": dataset.version,
            "split": {"development": ["page_001"], "test": ["page_002", "page_003"]},
        },
        progress=0.0,
        result_path=result_path,
        idempotency_key=idempotency_key,
    )
    db.add(job)
    db.flush()
    Path(result_path).parent.mkdir(parents=True, exist_ok=True)
    Path(result_path).write_text(
        json.dumps(
            {
                "status": "QUEUED",
                "job_id": job.id,
                "dataset_id": dataset.id,
                "dataset_version": dataset.version,
                "idempotency_key": idempotency_key,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return job


@router.post("/datasets/{dataset_id}/lock")
def lock_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = get_owned_dataset(db, dataset_id, current_user)
    if dataset.status == "LOCKED":
        job = create_evaluation_job(db, dataset, current_user.id)
        db.commit()
        return {"message": "Dataset already locked", "job_id": job.id, "progress": review_progress(db, dataset)}
    if dataset.status != GroundTruthStatus.REVIEWED_READY_TO_LOCK.value:
        raise HTTPException(status_code=400, detail="Dataset must be REVIEWED_READY_TO_LOCK before lock")
    errors = validate_dataset_can_lock(db, dataset)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors[:20], "total_errors": len(errors)})
    dataset.status = "LOCKED"
    dataset.locked_at = datetime.now(timezone.utc)
    dataset.locked_by_id = current_user.id
    dataset.metadata_json = {**(dataset.metadata_json or {}), "human_verified": True, "annotation_status": "LOCKED"}
    for page in dataset.pages:
        page.annotation_status = GroundTruthStatus.LOCKED
        for line in page.lines:
            line.status = GroundTruthStatus.LOCKED
    job = create_evaluation_job(db, dataset, current_user.id)
    db.commit()
    return {"message": "Dataset locked and pilot evaluation job queued", "job_id": job.id, "progress": review_progress(db, dataset)}


@router.post("/pages/{page_id}/lock")
def lock_ground_truth(page_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    page = get_owned_page(db, page_id, current_user)
    raise HTTPException(status_code=400, detail="Use dataset-level review and lock workflow")


@router.post("/evaluate/{page_id}")
def evaluate_ocr(
    page_id: int,
    ocr_texts: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    page = get_owned_page(db, page_id, current_user)
    if page.annotation_status != GroundTruthStatus.LOCKED:
        raise HTTPException(status_code=400, detail="Ground truth must be LOCKED to calculate metrics.")
    lines = db.query(GroundTruthLine).filter(GroundTruthLine.page_id == page_id).order_by(GroundTruthLine.reading_order).all()
    return {"page_id": page_id, "metrics": evaluate_page([line.text_content for line in lines], ocr_texts), "gt_lines": len(lines), "ocr_lines": len(ocr_texts)}


@router.get("/datasets/{dataset_id}/export")
def export_dataset(dataset_id: int, format: str = "json", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dataset = get_owned_dataset(db, dataset_id, current_user)
    pages = db.query(GroundTruthPage).filter(GroundTruthPage.dataset_id == dataset_id).order_by(GroundTruthPage.id).all()
    payload = {
        "dataset": {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "status": dataset.status,
            "version": dataset.version,
            "owner_id": dataset.owner_id,
            "metadata": dataset.metadata_json,
        },
        "pages": [
            {
                "id": page.id,
                "source_page_id": page.metadata_json.get("source_page_id") if page.metadata_json else None,
                "original_image_hash": page.original_image_hash,
                "annotation_status": page.annotation_status,
                "split_type": page.split_type,
                "lines": [
                    {
                        "id": line.id,
                        "reading_order": line.reading_order,
                        "bounding_box": line.bounding_box,
                        "text_content": line.text_content,
                        "draft_text": line.draft_text,
                        "text_reviewed": line.text_reviewed,
                        "bbox_reviewed": line.bbox_reviewed,
                        "status": line.status,
                        "version": line.version,
                    }
                    for line in db.query(GroundTruthLine)
                    .filter(GroundTruthLine.page_id == page.id)
                    .order_by(GroundTruthLine.reading_order)
                    .all()
                ],
            }
            for page in pages
        ],
    }
    if format == "txt":
        return {"format": "txt", "content": "\n".join(line["text_content"] for page in payload["pages"] for line in page["lines"])}
    if format != "json":
        raise HTTPException(status_code=400, detail="Unsupported export format")
    return {"format": "json", "content": payload}
