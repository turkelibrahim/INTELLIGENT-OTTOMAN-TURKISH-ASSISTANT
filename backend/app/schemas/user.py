"""
Kullanıcı API şemaları (Pydantic v2).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Yeni kullanıcı kayıt şeması."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Kullanıcı giriş şeması."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Kullanıcı bilgileri yanıt şeması."""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    role: str
    status: str
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token yanıt şeması."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    """Kullanıcı güncelleme şeması (yönetici)."""
    full_name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """Kullanıcının kendi profilini güncellemesi için şema."""
    full_name: Optional[str] = Field(None, max_length=255)
    current_password: Optional[str] = Field(None, min_length=6, max_length=128)
    new_password: Optional[str] = Field(None, min_length=6, max_length=128)
