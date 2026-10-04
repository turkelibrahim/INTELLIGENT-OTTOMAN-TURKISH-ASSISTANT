"""
Belge API şemaları (Pydantic v2).
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Belge oluşturma şeması (meta veri kısmı, dosya ayrıca gönderilir)."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    source: Optional[str] = None
    period: Optional[str] = None
    access_level: str = Field(default="private", pattern="^(private|shared|public)$")


class DocumentResponse(BaseModel):
    """Belge yanıt şeması."""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    source: Optional[str] = None
    period: Optional[str] = None
    original_filename: str
    file_size: int
    mime_type: str
    page_count: int
    status: str
    is_favorite: bool = False
    access_level: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Belge listesi yanıt şeması."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentUpdate(BaseModel):
    """Belge güncelleme şeması."""
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    period: Optional[str] = None
    access_level: Optional[str] = None
