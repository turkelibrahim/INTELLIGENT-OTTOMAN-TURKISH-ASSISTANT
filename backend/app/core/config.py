"""
Uygulama yapılandırma ayarları.
Tüm konfigürasyon değerleri .env dosyasından okunur.
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Ana uygulama ayarları."""

    # Uygulama
    APP_NAME: str = "Intelligent Ottoman Turkish Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Güvenlik
    SECRET_KEY: str = "change-this-secret-key-in-production-minimum-32-chars!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 saat
    ALGORITHM: str = "HS256"

    # Veritabanı
    DATABASE_URL: str = "sqlite:///./ottoman_assistant.db"

    # Dosya yükleme
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] = ["jpg", "jpeg", "png", "tiff", "tif", "pdf"]

    # LLM Ayarları
    LLM_PROVIDER: str = "openai"  # openai, gemini, ollama
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: Optional[str] = None  # Ollama için: http://localhost:11434/v1

    # OCR Ayarları
    OCR_ENGINE: str = "kraken"  # kraken, easyocr, trocr, tesseract
    OCR_MODEL_NAME: str = "microsoft/trocr-base-printed"
    OCR_CONFIDENCE_THRESHOLD: float = 0.7
    OCR_KRAKEN_MODEL_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "models", "recognition", "ottoman_recognition_final_v1.mlmodel")
    OCR_KRAKEN_MODEL_SHA256: str = "f5abbba1976e9782ddf5d7185d911722c74558e12b57a12566c96e22a3e3b963"
    OCR_KRAKEN_WSL_DISTRO: str = "Ubuntu-24.04"
    OCR_KRAKEN_WSL_PYTHON: str = "/home/black_man/venvs/ottoman_kraken/bin/python"

    # NER Ayarları
    NER_MODEL_NAME: str = "ottoman-ner"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod"}:
                return False
            if normalized in {"debug", "development", "dev"}:
                return True
        return value


# Singleton ayar nesnesi
settings = Settings()

# Upload dizinini oluştur
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "originals"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "thumbnails"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "processed"), exist_ok=True)
