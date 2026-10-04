"""
Belge yönetimi API endpoint'leri.
FR-DOC-001 ~ FR-DOC-008: Belge yükleme, listeleme, detay, silme.
"""
import json
from typing import Optional

from fastapi import (
    APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request,
)
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.page import Page
from app.models.audit_log import AuditLog
from app.schemas.document import (
    DocumentResponse, DocumentListResponse, DocumentUpdate,
)
from app.schemas.document_analysis import FullDocumentAnalysisResponse
from app.models.processing_job import ProcessingJob
from app.core.security import get_current_user
from app.services.file_service import file_service

router = APIRouter(prefix="/documents", tags=["Belgeler"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    period: Optional[str] = Form(None),
    access_level: str = Form("private"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Yeni belge yükler (FR-DOC-001).
    Dosya doğrulanır, kaydedilir, PDF ise sayfalara ayrılır.
    """
    # 1. Dosya doğrulama (uzantı + MIME)
    mime_type, ext = file_service.validate_file(file)

    # 2. Belge kaydı oluştur (dosya kaydından önce ID lazım)
    document = Document(
        user_id=current_user.id,
        title=title,
        description=description,
        source=source,
        period=period,
        original_filename=file.filename,
        file_hash="pending",  # Dosya kaydedildikten sonra güncellenecek
        file_size=0,
        mime_type=mime_type,
        status="uploaded",
        access_level=access_level,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        # 3. Dosyayı kaydet
        saved_path, file_hash, file_size = await file_service.save_upload(
            file, document.id
        )

        # 4. Hash ile duplicate kontrolü (FR-DOC-008)
        existing = (
            db.query(Document)
            .filter(
                Document.file_hash == file_hash,
                Document.id != document.id,
                Document.user_id == current_user.id,
            )
            .first()
        )
        if existing:
            # Uyarı ver ama yüklemeye izin ver
            pass  # İleride frontend'e uyarı dönülebilir

        # 5. Belge kaydını güncelle
        document.file_hash = file_hash
        document.file_size = file_size

        # 6. PDF ise sayfalara ayır (FR-DOC-004)
        if ext == "pdf":
            pages_info = file_service.split_pdf_to_pages(saved_path, document.id)
            document.page_count = len(pages_info) if pages_info else 1

            for p_info in pages_info:
                thumb_path = file_service.create_thumbnail(
                    p_info["image_path"], document.id, p_info["page_no"]
                )
                page = Page(
                    document_id=document.id,
                    page_no=p_info["page_no"],
                    original_path=p_info["image_path"],
                    thumbnail_path=thumb_path,
                    width=p_info["width"],
                    height=p_info["height"],
                    status="pending",
                )
                db.add(page)
        else:
            # Tek görüntü dosyası → tek sayfa
            width, height = file_service.get_image_dimensions(saved_path)
            thumb_path = file_service.create_thumbnail(
                saved_path, document.id, 1
            )
            page = Page(
                document_id=document.id,
                page_no=1,
                original_path=saved_path,
                thumbnail_path=thumb_path,
                width=width,
                height=height,
                status="pending",
            )
            db.add(page)
            document.page_count = 1

        db.commit()
        db.refresh(document)

        # 7. Audit log
        audit = AuditLog(
            actor_id=current_user.id,
            action="document.create",
            object_type="document",
            object_id=document.id,
            new_value=json.dumps({
                "title": title,
                "filename": file.filename,
                "pages": document.page_count,
            }),
            ip_address=request.client.host if request.client else None,
        )
        db.add(audit)
        db.commit()

    except HTTPException:
        # Doğrulama hatası → belge kaydını temizle
        db.delete(document)
        db.commit()
        raise
    except Exception as e:
        db.delete(document)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dosya işlenirken hata oluştu: {str(e)}",
        )

    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kullanıcının belgelerini listeler (FR-SRC-001)."""
    query = db.query(Document).filter(Document.user_id == current_user.id)

    if search:
        query = query.filter(Document.title.ilike(f"%{search}%"))

    if status_filter:
        query = query.filter(Document.status == status_filter)

    if is_favorite is not None:
        query = query.filter(Document.is_favorite == is_favorite)

    total = query.count()
    documents = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Belge detayını döner."""
    document = _get_user_document(document_id, current_user, db)
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/result", response_model=FullDocumentAnalysisResponse)
async def get_document_result(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Belgeye ait en son tamamlanmış analiz sonucunu döner."""
    document = _get_user_document(document_id, current_user, db)
    job = (
        db.query(ProcessingJob)
        .filter(
            ProcessingJob.document_id == document.id,
            ProcessingJob.job_type.in_(["full_document_analysis", "full_pipeline"]),
            ProcessingJob.status.ilike("COMPLETED")
        )
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )
    if not job or not job.result_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu belge için tamamlanmış analiz sonucu bulunamadı"
        )
    try:
        payload = json.loads(job.result_summary)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Stored analysis result is malformed") from exc
    return FullDocumentAnalysisResponse.model_validate(payload)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    update_data: DocumentUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Belge meta verilerini günceller."""
    document = _get_user_document(document_id, current_user, db)

    old_values = {}
    update_dict = update_data.model_dump(exclude_unset=True)

    for key, value in update_dict.items():
        old_values[key] = getattr(document, key)
        setattr(document, key, value)

    db.commit()
    db.refresh(document)

    # Audit log
    audit = AuditLog(
        actor_id=current_user.id,
        action="document.update",
        object_type="document",
        object_id=document.id,
        old_value=json.dumps(old_values),
        new_value=json.dumps(update_dict),
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()

    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Belgeyi siler (FR-DOC-007: onay frontend tarafında yapılır)."""
    document = _get_user_document(document_id, current_user, db)

    # Audit log (silmeden önce)
    audit = AuditLog(
        actor_id=current_user.id,
        action="document.delete",
        object_type="document",
        object_id=document.id,
        old_value=json.dumps({
            "title": document.title,
            "filename": document.original_filename,
        }),
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)

    # Dosyaları sil
    file_service.delete_document_files(document.id)

    # DB kaydını sil (cascade ile sayfalar da silinir)
    db.delete(document)
    db.commit()


@router.patch("/{document_id}/favorite", response_model=DocumentResponse)
async def toggle_favorite(
    document_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Belgeyi favorilere ekler veya çıkarır."""
    document = _get_user_document(document_id, current_user, db)
    
    old_value = document.is_favorite
    document.is_favorite = not document.is_favorite
    
    db.commit()
    db.refresh(document)
    
    audit = AuditLog(
        actor_id=current_user.id,
        action="document.favorite_toggle",
        object_type="document",
        object_id=document.id,
        old_value=json.dumps({"is_favorite": old_value}),
        new_value=json.dumps({"is_favorite": document.is_favorite}),
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()
    
    return DocumentResponse.model_validate(document)


@router.patch("/{document_id}/archive", response_model=DocumentResponse)
async def toggle_archive(
    document_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Belgeyi arşive kaldırır veya arşivden çıkarır."""
    document = _get_user_document(document_id, current_user, db)
    
    old_status = document.status
    if document.status == "archived":
        document.status = "ready"
    else:
        document.status = "archived"
    
    db.commit()
    db.refresh(document)
    
    audit = AuditLog(
        actor_id=current_user.id,
        action="document.archive_toggle",
        object_type="document",
        object_id=document.id,
        old_value=json.dumps({"status": old_status}),
        new_value=json.dumps({"status": document.status}),
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()
    
    return DocumentResponse.model_validate(document)


def _get_user_document(
    document_id: int, current_user: User, db: Session
) -> Document:
    """Kullanıcının erişim yetkisi olan belgeyi döner veya 404 fırlatır."""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Belge bulunamadı",
        )

    # Yetki kontrolü: sahip veya yönetici
    if document.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu belgeye erişim yetkiniz yok",
        )

    return document
