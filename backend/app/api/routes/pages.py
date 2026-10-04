"""
Sayfa yönetimi API endpoint'leri.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.page import Page
from app.schemas.page import PageResponse, PageListResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/documents/{document_id}/pages", tags=["Sayfalar"])


@router.get("", response_model=PageListResponse)
async def list_pages(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Belgenin sayfalarını listeler."""
    document = _get_authorized_document(document_id, current_user, db)

    pages = (
        db.query(Page)
        .filter(Page.document_id == document.id)
        .order_by(Page.page_no)
        .all()
    )

    return PageListResponse(
        pages=[PageResponse.model_validate(p) for p in pages],
        total=len(pages),
    )


@router.get("/{page_no}", response_model=PageResponse)
async def get_page(
    document_id: int,
    page_no: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Belirli bir sayfanın bilgilerini döner."""
    document = _get_authorized_document(document_id, current_user, db)

    page = (
        db.query(Page)
        .filter(Page.document_id == document.id, Page.page_no == page_no)
        .first()
    )

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sayfa {page_no} bulunamadı",
        )

    return PageResponse.model_validate(page)


@router.get("/{page_no}/image")
async def get_page_image(
    document_id: int,
    page_no: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sayfa görüntüsünü döner (FR-DOC-005)."""
    document = _get_authorized_document(document_id, current_user, db)

    page = (
        db.query(Page)
        .filter(Page.document_id == document.id, Page.page_no == page_no)
        .first()
    )

    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sayfa {page_no} bulunamadı",
        )

    import os
    if not os.path.exists(page.original_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sayfa görüntü dosyası bulunamadı",
        )

    return FileResponse(
        page.original_path,
        media_type="image/png",
        filename=f"page_{page_no}.png",
    )


@router.get("/{page_no}/thumbnail")
async def get_page_thumbnail(
    document_id: int,
    page_no: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sayfa küçük resmini döner."""
    document = _get_authorized_document(document_id, current_user, db)

    page = (
        db.query(Page)
        .filter(Page.document_id == document.id, Page.page_no == page_no)
        .first()
    )

    if not page or not page.thumbnail_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Küçük resim bulunamadı",
        )

    import os
    if not os.path.exists(page.thumbnail_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Küçük resim dosyası bulunamadı",
        )

    return FileResponse(
        page.thumbnail_path,
        media_type="image/jpeg",
        filename=f"page_{page_no}_thumb.jpg",
    )


def _get_authorized_document(
    document_id: int, current_user: User, db: Session
) -> Document:
    """Yetki kontrollü belge erişimi."""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Belge bulunamadı",
        )

    if document.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu belgeye erişim yetkiniz yok",
        )

    return document
