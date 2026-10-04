"""
Kullanıcı veritabanı modeli.
FR-AUTH-001 ~ FR-AUTH-005: Kimlik doğrulama ve rol yönetimi.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    # Roller: user, expert, admin (FR-AUTH-002)
    role = Column(
        SAEnum("user", "expert", "admin", name="user_role"),
        default="user",
        nullable=False,
    )

    # Hesap durumu: active, inactive, suspended
    status = Column(
        SAEnum("active", "inactive", "suspended", name="user_status"),
        default="active",
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
    last_login_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
