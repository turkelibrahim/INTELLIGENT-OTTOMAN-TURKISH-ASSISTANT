from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentAnalysisDocument(BaseModel):
    filename: str
    document_type: str = "Tespit edilemedi"
    language: str = "Ottoman Turkish"
    document_id: Optional[int] = None
    page_count: int = 0


class ImageProcessingInfo(BaseModel):
    applied: List[str] = Field(default_factory=list)
    ocr_safe_image: str = ""
    warnings: List[str] = Field(default_factory=list)


class OCRInfo(BaseModel):
    ottoman_text: str = ""
    confidence: float = 0.0
    engine: str = ""
    fallback_used: bool = False
    lines: List[Dict[str, Any]] = Field(default_factory=list)


class TransliterationInfo(BaseModel):
    latin_text: str = ""
    confidence: float = 0.0
    method: str = ""
    lines: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ModernTurkishInfo(BaseModel):
    text: str = ""
    confidence: float = 0.0
    provider: str = ""
    lines: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class EntitiesInfo(BaseModel):
    persons: List[Dict[str, Any]] = Field(default_factory=list)
    places: List[Dict[str, Any]] = Field(default_factory=list)
    institutions: List[Dict[str, Any]] = Field(default_factory=list)
    dates: List[Dict[str, Any]] = Field(default_factory=list)
    titles: List[Dict[str, Any]] = Field(default_factory=list)
    document_marks: List[Dict[str, Any]] = Field(default_factory=list)


class HistoricalAnalysisInfo(BaseModel):
    possible_period: str = "Tespit edilemedi"
    possible_sultan_period: str = "Tespit edilemedi"
    possible_author: str = "Tespit edilemedi"
    possible_institution: str = "Tespit edilemedi"
    document_type: str = "Tespit edilemedi"
    historical_context: str = "Tespit edilemedi"
    confidence: float = 0.0
    provisional: bool = True


class EvidenceInfo(BaseModel):
    document_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    historical_external_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    model_inference: List[Dict[str, Any]] = Field(default_factory=list)
    document_claims: List[Dict[str, Any]] = Field(default_factory=list)


class ConfidenceInfo(BaseModel):
    ocr: float = 0.0
    transliteration: float = 0.0
    modern_turkish: float = 0.0
    entities: float = 0.0
    retrieval_strength: float = 0.0
    evidence_coverage: float = 0.0
    combined: Optional[float] = None
    combined_provisional: bool = True


class FullDocumentAnalysisResponse(BaseModel):
    document: DocumentAnalysisDocument
    image_processing: ImageProcessingInfo
    ocr: OCRInfo
    transliteration: TransliterationInfo
    modern_turkish: ModernTurkishInfo
    entities: EntitiesInfo
    historical_analysis: HistoricalAnalysisInfo
    evidence: EvidenceInfo
    confidence: ConfidenceInfo
    uncertainties: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
