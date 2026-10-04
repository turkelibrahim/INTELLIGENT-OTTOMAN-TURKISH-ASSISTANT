from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, validator, model_validator
import re
import unicodedata

# ---------------------------------------------------------
# BBOX & BASELINE
# ---------------------------------------------------------
class BBox(BaseModel):
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)

class Point(BaseModel):
    x: float
    y: float

class Baseline(BaseModel):
    points: List[Point]

    @validator('points')
    def check_min_points(cls, v):
        if len(v) < 2:
            raise ValueError("Baseline must have at least 2 points")
        return v

# ---------------------------------------------------------
# DATASET
# ---------------------------------------------------------
class AnnotationDatasetCreate(BaseModel):
    legacy_dataset_id: Optional[int] = None
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_test_data: bool = False
    training_eligible: bool = False
    target_verified_lines: int = Field(..., gt=0)
    double_review_required: bool = False

class AnnotationDatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_test_data: Optional[bool] = None
    archived: Optional[bool] = None
    training_eligible: Optional[bool] = None
    target_verified_lines: Optional[int] = None
    double_review_required: Optional[bool] = None

class AnnotationDatasetResponse(BaseModel):
    id: int
    legacy_dataset_id: Optional[int]
    name: str
    description: Optional[str]
    status: str
    is_test_data: bool
    archived: bool
    training_eligible: bool
    target_verified_lines: int
    double_review_required: bool
    created_by: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    locked_at: Optional[str]

class AnnotationDatasetProgressResponse(BaseModel):
    dataset_id: int
    dataset_name: str
    target_verified_lines: int
    total_documents: int
    total_pages: int
    total_regions: int
    total_lines: int
    draft_lines: int
    auto_preannotated_lines: int
    in_review_lines: int
    needs_correction_lines: int
    human_verified_lines: int
    double_reviewed_lines: int
    locked_lines: int
    rejected_lines: int
    verified_training_eligible_lines: int
    remaining_to_target: int

# ---------------------------------------------------------
# DOCUMENT
# ---------------------------------------------------------
class AnnotationDocumentCreate(BaseModel):
    source_name: str
    source_path: str
    source_sha256: str = Field(..., min_length=1)
    license_status: str = "UNKNOWN"
    license_reference: Optional[str] = None
    document_type: Optional[str] = None
    script_style: Optional[str] = None
    printed_or_handwritten: Optional[str] = None

class AnnotationDocumentResponse(BaseModel):
    id: int
    dataset_id: int
    source_name: str
    source_path: str
    source_sha256: str
    license_status: str
    license_reference: Optional[str]
    document_type: Optional[str]
    script_style: Optional[str]
    printed_or_handwritten: Optional[str]
    created_by: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

# ---------------------------------------------------------
# PAGE
# ---------------------------------------------------------
class AnnotationPageCreate(BaseModel):
    page_number: int
    image_path: str
    image_sha256: str = Field(..., min_length=1)
    image_width: int = Field(..., gt=0)
    image_height: int = Field(..., gt=0)

class AnnotationPageResponse(BaseModel):
    id: int
    document_id: int
    page_number: int
    image_path: str
    image_sha256: str
    image_width: int
    image_height: int
    status: Optional[str]
    human_verified: bool
    reading_order_verified: bool
    created_at: Optional[str]
    updated_at: Optional[str]
    locked_at: Optional[str]

# ---------------------------------------------------------
# REGION
# ---------------------------------------------------------
class AnnotationRegionCreate(BaseModel):
    region_type: str
    bbox_json: BBox
    reading_order: int = Field(..., ge=0)

class AnnotationRegionUpdate(BaseModel):
    region_type: Optional[str] = None
    bbox_json: Optional[BBox] = None
    reading_order: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None

class AnnotationRegionResponse(BaseModel):
    id: int
    page_id: int
    region_type: str
    bbox_json: Optional[str]
    reading_order: int
    status: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

# ---------------------------------------------------------
# LINE
# ---------------------------------------------------------
class AnnotationLineCreate(BaseModel):
    region_id: Optional[int] = None
    line_order: int = Field(..., ge=0)
    bbox_json: BBox
    baseline_json: Optional[Baseline] = None
    transcription: Optional[str] = None
    machine_suggestion: Optional[str] = None
    machine_confidence: Optional[float] = None
    crop_sha256: Optional[str] = None

    @validator('transcription')
    def validate_transcription(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("Transcription cannot be empty or just whitespace")
            if bool(re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', v)):
                raise ValueError("Transcription cannot contain control characters")
        return v

class AnnotationLineUpdate(BaseModel):
    line_order: Optional[int] = Field(None, ge=0)
    bbox_json: Optional[BBox] = None
    baseline_json: Optional[Baseline] = None
    transcription: Optional[str] = None
    
    @validator('transcription')
    def validate_transcription(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("Transcription cannot be empty or just whitespace")
            if bool(re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', v)):
                raise ValueError("Transcription cannot contain control characters")
        return v

class AnnotationLineResponse(BaseModel):
    id: int
    page_id: int
    region_id: Optional[int]
    line_order: int
    bbox_json: Optional[str]
    baseline_json: Optional[str]
    transcription: Optional[str]
    normalized_transcription: Optional[str]
    machine_suggestion: Optional[str]
    machine_confidence: Optional[float]
    status: Optional[str]
    human_verified: bool
    bbox_verified: bool
    baseline_verified: bool
    reading_order_verified: bool
    transcription_verified: bool
    duplicate_checked: bool
    training_eligible: bool
    crop_sha256: Optional[str]
    created_by: Optional[str]
    reviewed_by: Optional[str]
    second_reviewer: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    reviewed_at: Optional[str]
    second_reviewed_at: Optional[str]
    locked_at: Optional[str]

# ---------------------------------------------------------
# REVIEWS
# ---------------------------------------------------------
class NeedsCorrectionRequest(BaseModel):
    comment: str

class HumanVerificationRequest(BaseModel):
    pass # reviewer_id is taken from user context

class SecondReviewRequest(BaseModel):
    decision: str # e.g. APPROVED, REJECTED
    comment: Optional[str] = None

class DatasetLockRequest(BaseModel):
    pass

# ---------------------------------------------------------
# AUDIT
# ---------------------------------------------------------
class AnnotationAuditEventResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    before_json: Optional[str]
    after_json: Optional[str]
    actor_id: str
    success: bool
    error_code: Optional[str]
    created_at: Optional[str]

