"""
Sayfa veritabanı modeli.
Çok sayfalı belgelerin (PDF) her sayfası ayrı kayıt olarak tutulur.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    page_no = Column(Integer, nullable=False)  # 1-indexed sayfa numarası
    original_path = Column(String(1000), nullable=False)  # Orijinal görüntü yolu
    thumbnail_path = Column(String(1000), nullable=True)  # Küçük resim yolu
    width = Column(Integer, nullable=True)   # Piksel genişliği
    height = Column(Integer, nullable=True)  # Piksel yüksekliği

    # İşleme durumu (sayfa bazında)
    status = Column(String(50), default="pending", nullable=False)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # İlişkiler
    document = relationship("Document", back_populates="pages")

    # Aynı belgede aynı sayfa numarası tekrarlanamaz
    __table_args__ = (
        UniqueConstraint("document_id", "page_no", name="uq_document_page"),
    )

    def __repr__(self):
        return f"<Page(id={self.id}, document_id={self.document_id}, page_no={self.page_no})>"
