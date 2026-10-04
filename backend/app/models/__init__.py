"""
Modeller paketi.
Tüm SQLAlchemy modellerini burada import ederek Base.metadata'ya kayıt olmaları sağlanır.
"""
from app.models.user import User
from app.models.document import Document
from app.models.page import Page
from app.models.processing_job import ProcessingJob
from app.models.audit_log import AuditLog
from app.models.image_variant import ImageVariant
from app.models.processing_outputs import (
    ChatMessage,
    ChatSession,
    Citation,
    Entity,
    ExportRecord,
    ModelRegistryEntry,
    OCRResult,
    TextVersion,
)
from app.models.ground_truth import (
    Dataset,
    GroundTruthPage,
    GroundTruthLine,
    GroundTruthReviewAudit,
)

__all__ = [
    "User",
    "Document",
    "Page",
    "ProcessingJob",
    "AuditLog",
    "ImageVariant",
    "ModelRegistryEntry",
    "OCRResult",
    "TextVersion",
    "Entity",
    "ChatSession",
    "ChatMessage",
    "Citation",
    "ExportRecord",
    "Dataset",
    "GroundTruthPage",
    "GroundTruthLine",
    "GroundTruthReviewAudit",
]
