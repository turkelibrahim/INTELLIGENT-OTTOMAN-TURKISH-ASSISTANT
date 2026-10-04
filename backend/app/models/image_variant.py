"""
Image Variant veritabanı modeli.
Ön işlemden geçen sayfaların (ör. eşikleme uygulanmış, gürültüsü temizlenmiş kopyalar) tutulduğu tablo.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class ImageVariant(Base):
    __tablename__ = "image_variants"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    page_id = Column(
        Integer, ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    job_id = Column(
        Integer, ForeignKey("processing_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )

    # İşlem profili (ör. "temiz_baski", "lekeli_sayfa")
    profile = Column(String(100), nullable=False)

    # Kullanılan gerçek parametreler (tekrarlanabilirlik için)
    parameters = Column(JSON, nullable=False)

    # İşlenmiş dosyanın yolu
    file_path = Column(String(1000), nullable=False)

    # Görüntü kalitesi/netlik skoru
    quality_score = Column(Integer, nullable=True)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def __repr__(self):
        return f"<ImageVariant(id={self.id}, page_id={self.page_id}, profile='{self.profile}')>"
