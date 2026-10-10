"""
File upload, validation, storage and page-rendering service.
"""
import hashlib
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


ALLOWED_MIME_TYPES = {
    "image/jpeg": ["jpg", "jpeg"],
    "image/png": ["png"],
    "image/tiff": ["tiff", "tif"],
    "application/pdf": ["pdf"],
}

MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"II\x2a\x00": "image/tiff",
    b"MM\x00\x2a": "image/tiff",
    b"%PDF": "application/pdf",
}


class FileService:
    """File upload, validation and derived-file management service."""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    def validate_file(self, file: UploadFile) -> Tuple[str, str]:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dosya adi bos olamaz",
            )

        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Desteklenmeyen dosya uzantisi: .{ext}. "
                    f"Izin verilen: {', '.join(settings.ALLOWED_EXTENSIONS)}"
                ),
            )

        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Desteklenmeyen MIME tipi: {file.content_type}",
            )

        if ext not in ALLOWED_MIME_TYPES[file.content_type]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dosya uzantisi MIME tipiyle eslesmiyor",
            )

        return file.content_type, ext

    def validate_magic_bytes(self, file_path: str) -> bool:
        with open(file_path, "rb") as f:
            header = f.read(8)

        return any(header.startswith(magic) for magic in MAGIC_BYTES)

    def calculate_hash(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def save_upload(self, file: UploadFile, document_id: int) -> Tuple[str, str, int]:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        unique_name = f"{document_id}_{uuid.uuid4().hex[:8]}.{ext}"
        save_dir = self.upload_dir / "originals" / str(document_id)
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / unique_name

        file_size = 0
        with open(save_path, "wb") as buffer:
            while True:
                chunk = await file.read(8192)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > self.max_size:
                    buffer.close()
                    os.remove(save_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f"Dosya boyutu {settings.MAX_FILE_SIZE_MB} MB sinirini asiyor",
                    )
                buffer.write(chunk)

        if not self.validate_magic_bytes(str(save_path)):
            os.remove(save_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dosya icerigi uzantisiyla eslesmiyor (sahte uzanti tespit edildi)",
            )

        file_hash = self.calculate_hash(str(save_path))
        return str(save_path), file_hash, file_size

    def create_thumbnail(
        self,
        image_path: str,
        document_id: int,
        page_no: int,
        size: Tuple[int, int] = (300, 400),
    ) -> Optional[str]:
        try:
            thumb_dir = self.upload_dir / "thumbnails" / str(document_id)
            thumb_dir.mkdir(parents=True, exist_ok=True)
            thumb_path = thumb_dir / f"page_{page_no}_thumb.jpg"

            with Image.open(image_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(str(thumb_path), "JPEG", quality=85)

            return str(thumb_path)
        except Exception:
            return None

    def split_pdf_to_pages(self, pdf_path: str, document_id: int) -> List[dict]:
        pages_dir = self.upload_dir / "originals" / str(document_id) / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        pages_info = self._split_pdf_with_poppler(pdf_path, pages_dir)
        if pages_info:
            return pages_info
        return self._split_pdf_with_pdfium(pdf_path, pages_dir)

    def _split_pdf_with_poppler(self, pdf_path: str, pages_dir: Path) -> List[dict]:
        pages_info = []
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(pdf_path, dpi=200)
            for i, img in enumerate(images, start=1):
                page_path = pages_dir / f"page_{i}.png"
                img.save(str(page_path), "PNG")
                pages_info.append({
                    "page_no": i,
                    "image_path": str(page_path),
                    "width": img.width,
                    "height": img.height,
                })
        except Exception as e:
            logger.warning(f"Poppler PDF split failed: {e}")
            pages_info = []
        return pages_info

    def _split_pdf_with_pdfium(self, pdf_path: str, pages_dir: Path) -> List[dict]:
        pages_info = []
        try:
            import pypdfium2 as pdfium

            pdf = pdfium.PdfDocument(pdf_path)
            try:
                for index in range(len(pdf)):
                    page = pdf[index]
                    try:
                        bitmap = page.render(scale=200 / 72)
                        image = bitmap.to_pil()
                        if image.mode != "RGB":
                            image = image.convert("RGB")
                        page_path = pages_dir / f"page_{index + 1}.png"
                        image.save(str(page_path), "PNG")
                        pages_info.append({
                            "page_no": index + 1,
                            "image_path": str(page_path),
                            "width": image.width,
                            "height": image.height,
                        })
                    finally:
                        page.close()
            finally:
                pdf.close()
        except Exception as e:
            logger.warning(f"PDFium PDF split failed: {e}")
            pages_info = []
        return pages_info

    def get_image_dimensions(self, image_path: str) -> Tuple[int, int]:
        with Image.open(image_path) as img:
            return img.width, img.height

    def delete_document_files(self, document_id: int) -> None:
        for subdir in ["originals", "thumbnails", "processed"]:
            doc_dir = self.upload_dir / subdir / str(document_id)
            if doc_dir.exists():
                shutil.rmtree(doc_dir)


file_service = FileService()
