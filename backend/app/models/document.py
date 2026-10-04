"""
Belge veritabanı modeli.
FR-DOC-001 ~ FR-DOC-008: Belge yükleme ve yönetim.
SRS Bölüm 7.2: İş durumları (UPLOADED → PREPROCESSING → ... → READY).
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Enum as SAEnum, BigInteger, Boolean,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(500), nullable=True)  # Kaynak bilgisi
    period = Column(String(200), nullable=True)   # Tarih/dönem
    original_filename = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    file_size = Column(BigInteger, nullable=False)  # Byte cinsinden
    mime_type = Column(String(100), nullable=False)
    page_count = Column(Integer, default=1)
    is_favorite = Column(Boolean, default=False, nullable=False, index=True)

    # İş durumları (SRS 7.2)
    status = Column(
        SAEnum(
            "uploaded", "preprocessing", "layout_analysis",
            "ocr", "ocr_review", "transliteration", "modernization",
            "analysis", "ready", "failed", "archived",
            name="document_status",
        ),
        default="uploaded",
        nullable=False,
        index=True,
    )

    # Erişim seviyesi
    access_level = Column(
        SAEnum("private", "shared", "public", name="access_level"),
        default="private",
        nullable=False,
    )

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # İlişkiler
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    owner = relationship("User", backref="documents")

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"
