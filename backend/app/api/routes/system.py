import os
from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/status")
def get_system_status(current_user: User = Depends(get_current_user)):
    """Returns the current system configuration and health status."""
    return {
        "models": {
            "ocr_engine": settings.OCR_ENGINE.upper(),
            "ocr_model": settings.OCR_MODEL_NAME if settings.OCR_ENGINE != "kraken" else "ottoman_recognition_final_v1.mlmodel",
            "llm": settings.LLM_PROVIDER.upper() + (f" ({settings.LLM_MODEL})" if settings.LLM_PROVIDER != "openai" else ""),
            "ner": settings.NER_MODEL_NAME,
            "vector_db": "Qdrant (Local)",
            "embedding": os.getenv("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:0.6b"),
            "fallback_model": settings.NVIDIA_PRIMARY_MODEL if settings.NVIDIA_OCR_FALLBACK_ENABLED else "Devre Dışı"
        },
        "api_integrations": {
            "nvidia_nim": "active" if settings.NVIDIA_API_KEY else "inactive",
            "nvidia_primary_model": settings.NVIDIA_PRIMARY_MODEL,
            "nvidia_vision_model": settings.NVIDIA_VISION_MODEL
        },
        "system": {
            "status": "Hazır",
            "data_privacy": "Local",
            "version": settings.APP_VERSION,
            "debug_mode": settings.DEBUG
        }
    }
