from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Enum as SAEnum, Boolean, Float, JSON
)
from sqlalchemy.orm import relationship
from app.db.database import Base

class GroundTruthStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    REVIEWED = "REVIEWED"
    REVIEWED_READY_TO_LOCK = "REVIEWED_READY_TO_LOCK"
    LOCKED = "LOCKED"
    REJECTED = "REJECTED"

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(255), nullable=True)
    license = Column(String(255), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="ACTIVE")
    version = Column(String(50), default="1.0.0")
    manifest_sha256 = Column(String(64), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    locked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", backref="datasets", foreign_keys=[owner_id])
    locked_by = relationship("User", foreign_keys=[locked_by_id])
    pages = relationship("GroundTruthPage", back_populates="dataset", cascade="all, delete-orphan")

class GroundTruthPage(Base):
    __tablename__ = "ground_truth_pages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=True)
    
    original_image_hash = Column(String(64), nullable=False)
    image_path = Column(String(1000), nullable=True)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    document_type = Column(String(100), nullable=True) # e.g. printed, handwritten
    print_quality = Column(String(50), nullable=True) # clean, degraded, multi_column
    font_type = Column(String(100), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    split_type = Column(String(50), default="unassigned") # train, val, test, unassigned
    annotation_status = Column(SAEnum(GroundTruthStatus), default=GroundTruthStatus.DRAFT)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    dataset = relationship("Dataset", back_populates="pages")
    lines = relationship("GroundTruthLine", back_populates="page", cascade="all, delete-orphan")

class GroundTruthLine(Base):
    __tablename__ = "ground_truth_lines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    page_id = Column(Integer, ForeignKey("ground_truth_pages.id"), nullable=False)
    
    # Coordinates in normalized format [x_min, y_min, x_max, y_max] or polygon [[x,y],...]
    bounding_box = Column(JSON, nullable=False)
    reading_order = Column(Integer, nullable=False) # 0-indexed, Right-to-Left priority
    
    text_content = Column(Text, nullable=False) # The actual ground truth transcription
    draft_text = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    annotator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    version = Column(Integer, default=1)
    status = Column(SAEnum(GroundTruthStatus), default=GroundTruthStatus.DRAFT)
    text_reviewed = Column(Boolean, default=False, nullable=False)
    bbox_reviewed = Column(Boolean, default=False, nullable=False)
    text_changed = Column(Boolean, default=False, nullable=False)
    bbox_changed = Column(Boolean, default=False, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_action_id = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    page = relationship("GroundTruthPage", back_populates="lines")
    annotator = relationship("User", foreign_keys=[annotator_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])


class GroundTruthReviewAudit(Base):
    __tablename__ = "ground_truth_review_audits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    page_id = Column(Integer, ForeignKey("ground_truth_pages.id"), nullable=False)
    line_id = Column(Integer, ForeignKey("ground_truth_lines.id"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewer_display_name = Column(String(255), nullable=False)
    action = Column(String(80), nullable=False)
    previous_text = Column(Text, nullable=True)
    new_text = Column(Text, nullable=True)
    text_changed = Column(Boolean, default=False, nullable=False)
    previous_bbox = Column(JSON, nullable=True)
    new_bbox = Column(JSON, nullable=True)
    bbox_changed = Column(Boolean, default=False, nullable=False)
    source_image_hash = Column(String(64), nullable=True)
    review_action_id = Column(String(64), nullable=False, unique=True, index=True)
    dataset_version = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    reviewer = relationship("User", foreign_keys=[reviewer_id])

