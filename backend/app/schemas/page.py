"""
Sayfa API şemaları (Pydantic v2).
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class PageResponse(BaseModel):
    """Sayfa yanıt şeması."""
    id: int
    document_id: int
    page_no: int
    original_path: str
    thumbnail_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PageListResponse(BaseModel):
    """Sayfa listesi yanıt şeması."""
    pages: List[PageResponse]
    total: int
