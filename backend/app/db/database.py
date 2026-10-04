"""
Veritabanı bağlantısı ve oturum yönetimi.
MVP'de SQLite, gelişmiş sürümde PostgreSQL kullanılır.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

from sqlalchemy.pool import NullPool
from sqlalchemy import event
from sqlalchemy.engine import Engine

# SQLite için check_same_thread=False gerekli (FastAPI çoklu thread kullanabilir)
connect_args = {}
engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
    **engine_kwargs
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency: Her istek için bir DB oturumu açar ve istek
    sonunda kapatır.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Tüm tabloları oluşturur (geliştirme ortamı için)."""
    # Tüm modelleri import ederek Base.metadata'ya kayıt olmalarını sağla
    import app.models  # noqa: F401
    # Base.metadata.create_all(bind=engine) # Alembic kullandığımız için devre dışı bırakıldı
