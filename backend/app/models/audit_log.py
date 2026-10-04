"""
Denetim günlüğü (Audit Log) veritabanı modeli.
FR-REV-002: Kullanıcı, zaman, eski değer, yeni değer kaydı.
SRS 11.1: Değiştirilemez log.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.db.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    actor_id = Column(
        Integer, ForeignKey("users.id"),
        nullable=True,  # Sistem işlemleri için null olabilir
    )
    action = Column(String(100), nullable=False, index=True)
    # Örnek action değerleri: "document.create", "ocr.correct",
    # "user.login", "document.delete"

    object_type = Column(String(100), nullable=True)  # "document", "ocr_result" vb.
    object_id = Column(Integer, nullable=True)

    old_value = Column(Text, nullable=True)  # JSON string olarak eski değer
    new_value = Column(Text, nullable=True)  # JSON string olarak yeni değer
    details = Column(Text, nullable=True)    # Ek açıklama

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self):
        return (
            f"<AuditLog(id={self.id}, actor={self.actor_id}, "
            f"action='{self.action}')>"
        )
