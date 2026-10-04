"""
Görüntü ön işleme ve varyant (Image Variant) yönetimi API endpoint'leri.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.db.database import get_db
from app.models.user import User
from app.models.document import Document
from app.models.page import Page
from app.models.image_variant import ImageVariant
from app.models.audit_log import AuditLog
from app.core.security import get_current_user
from app.core.config import settings
from app.services.document_processing.preprocessor import ImagePreprocessor
from app.services.image_io import ImageIOError, write_image_unicode_safe
from pydantic import BaseModel, Field

router = APIRouter(prefix="/pages/{page_id}/preprocessing", tags=["Ön İşleme"])
preprocessor = ImagePreprocessor()

class PreprocessRequest(BaseModel):
    profile: str = Field(..., description="Profil adı: temiz_baski, lekeli_sayfa, el_yazmasi, ozel")
    params: Optional[dict] = Field(default=None, description="Profil 'ozel' ise ekstra parametreler")

class ImageVariantResponse(BaseModel):
    id: int
    page_id: int
    profile: str
    parameters: dict
    quality_score: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("", response_model=ImageVariantResponse)
async def create_preprocess_variant(
    page_id: int,
    request_data: PreprocessRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Belirtilen sayfa için bir ön işleme kopyası (variant) oluşturur.
    """
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Sayfa bulunamadı")

    document = db.query(Document).filter(Document.id == page.document_id).first()
    if not document or (document.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Bu belgeye erişim yetkiniz yok")

    # Görüntüyü işle
    processed_img, params_used, score = preprocessor.process_with_profile(
        image_path=page.original_path,
        profile=request_data.profile,
        document_id=document.id,
        page_no=page.page_no,
        custom_params=request_data.params
    )

    # Kaydedilecek dizini oluştur
    doc_dir = os.path.join(settings.UPLOAD_DIR, "processed", str(document.id))
    os.makedirs(doc_dir, exist_ok=True)
    
    # Dosyayı kaydet
    file_name = f"page_{page.page_no}_{uuid.uuid4().hex[:8]}.png"
    save_path = os.path.join(doc_dir, file_name)
    try:
        write_image_unicode_safe(save_path, processed_img)
    except ImageIOError as exc:
        raise HTTPException(status_code=500, detail=f"Islenmis goruntu kaydedilemedi: {exc}") from exc

    # Veritabanına kaydet
    variant = ImageVariant(
        page_id=page.id,
        profile=request_data.profile,
        parameters=params_used,
        file_path=save_path,
        quality_score=int(score * 100) if score else None
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)

    # Sayfa durumunu güncelle (eğer preprocessing'e yeni geçiyorsa)
    if document.status == "uploaded":
        document.status = "preprocessing"
        db.commit()

    # Audit log
    audit = AuditLog(
        actor_id=current_user.id,
        action="page.preprocess",
        object_type="image_variant",
        object_id=variant.id,
        new_value=json.dumps({"profile": request_data.profile, "params": params_used}),
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()

    return variant

@router.get("/variants")
async def list_variants(
    page_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sayfaya ait oluşturulmuş tüm varyantları listeler.
    """
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Sayfa bulunamadı")

    document = db.query(Document).filter(Document.id == page.document_id).first()
    if not document or (document.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Bu belgeye erişim yetkiniz yok")

    variants = db.query(ImageVariant).filter(ImageVariant.page_id == page_id).order_by(ImageVariant.created_at.desc()).all()
    
    return [
        {
            "id": v.id,
            "page_id": v.page_id,
            "profile": v.profile,
            "parameters": v.parameters,
            "quality_score": v.quality_score,
            "created_at": v.created_at,
        }
        for v in variants
    ]

@router.get("/variants/{variant_id}/image")
async def get_variant_image(
    page_id: int,
    variant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    İşlenmiş kopyanın görüntüsünü döner.
    """
    variant = db.query(ImageVariant).filter(ImageVariant.id == variant_id, ImageVariant.page_id == page_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Varyant bulunamadı")
        
    page = db.query(Page).filter(Page.id == page_id).first()
    document = db.query(Document).filter(Document.id == page.document_id).first()
    if document.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Erişim engellendi")

    if not os.path.exists(variant.file_path):
        raise HTTPException(status_code=404, detail="Görüntü dosyası bulunamadı")

    return FileResponse(variant.file_path, media_type="image/png")

@router.get("/stages")
async def get_stages_manifest(
    page_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Belirtilen sayfa için işleme aşamalarının listesini döner.
    """
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Sayfa bulunamadı")
    document = db.query(Document).filter(Document.id == page.document_id).first()
    if not document or (document.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Bu belgeye erişim yetkiniz yok")

    manifest_path = os.path.join(settings.UPLOAD_DIR, "processed", str(document.id), f"page_{page.page_no}", "processing_manifest.json")
    if not os.path.exists(manifest_path):
        return {"document_id": document.id, "page_no": page.page_no, "stages": []}
    
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        # Add full URLs for images
        for stage in manifest.get("stages", []):
            if stage.get("file_name"):
                stage["image_url"] = f"/api/v1/pages/{page.id}/preprocessing/stages/{stage['id']}/image"
        
        return manifest
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Manifest okunamadı") from exc

@router.get("/stages/{stage_id}/image")
async def get_stage_image(
    page_id: int,
    stage_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Belirli bir işleme aşamasının görüntüsünü döner.
    """
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Sayfa bulunamadı")
    document = db.query(Document).filter(Document.id == page.document_id).first()
    if not document or (document.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Erişim engellendi")

    image_path = os.path.join(settings.UPLOAD_DIR, "processed", str(document.id), f"page_{page.page_no}", f"{stage_id}.png")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Görüntü bulunamadı")

    return FileResponse(image_path, media_type="image/png")
