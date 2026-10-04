"""
Kimlik doğrulama API endpoint'leri.
FR-AUTH-001: Oturum açma
FR-AUTH-002: Rol bazlı erişim
FR-AUTH-004: Oturum kapatma ve zaman aşımı
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, TokenResponse, UserProfileUpdate,
)
from app.core.security import (
    get_password_hash, verify_password, create_access_token, get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Kimlik Doğrulama"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Yeni kullanıcı kaydı oluşturur."""
    user_data.email = user_data.email.lower()
    # E-posta kontrolü
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu e-posta adresi zaten kayıtlı",
        )

    # Kullanıcı adı kontrolü
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu kullanıcı adı zaten kullanılıyor",
        )

    # Kullanıcı oluştur
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role="user",
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit log
    audit = AuditLog(
        actor_id=user.id,
        action="user.register",
        object_type="user",
        object_id=user.id,
        new_value=json.dumps({"email": user.email, "username": user.username}),
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()

    # Token oluştur
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """Kullanıcı girişi yapar ve JWT token döner."""
    user_data.email = user_data.email.lower()
    # Kullanıcıyı bul
    user = db.query(User).filter(User.email == user_data.email).first()

    # Genel hata mesajı (güvenlik için — FR-AUTH-001)
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya parola hatalı",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesabınız devre dışı bırakılmış. Yöneticiyle iletişime geçin.",
        )

    # Son giriş zamanını güncelle
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Audit log
    audit = AuditLog(
        actor_id=user.id,
        action="user.login",
        object_type="user",
        object_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()

    # Token oluştur
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Mevcut kullanıcının bilgilerini döner."""
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Oturum kapatma (FR-AUTH-004).
    JWT stateless olduğu için sunucu tarafında token iptal etmek yerine,
    client tarafta token silinir. Audit kaydı oluşturulur.
    """
    audit = AuditLog(
        actor_id=current_user.id,
        action="user.logout",
        object_type="user",
        object_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()

    return {"message": "Oturum başarıyla kapatıldı"}


@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: UserProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kullanıcının kendi profilini güncellemesi."""
    # Ad güncelleme
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name

    # Parola değiştirme
    if update_data.new_password:
        if not update_data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mevcut parolanızı girmelisiniz.",
            )
        if not verify_password(update_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Mevcut parola hatalı.",
            )
        current_user.password_hash = get_password_hash(update_data.new_password)

    db.commit()
    db.refresh(current_user)

    # Audit log
    audit = AuditLog(
        actor_id=current_user.id,
        action="user.profile_update",
        object_type="user",
        object_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.add(audit)
    db.commit()

    return UserResponse.model_validate(current_user)


@router.get("/me/stats")
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kullanıcının istatistiklerini döner (toplam belge, favori, arşiv vb.)."""
    from app.models.document import Document

    total_docs = db.query(Document).filter(Document.user_id == current_user.id).count()
    favorite_docs = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.is_favorite == True  # noqa: E712
    ).count()
    archived_docs = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.is_archived == True  # noqa: E712
    ).count()

    return {
        "total_documents": total_docs,
        "favorite_documents": favorite_docs,
        "archived_documents": archived_docs,
        "member_since": current_user.created_at.isoformat() if current_user.created_at else None,
        "last_login": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
    }
