import os
from app.core.config import settings
from app.services.document_processing.ocr_engine import OttomanOCREngine
from app.services.document_processing.vlm_ocr_engine import VLMOCREngine

_ENGINE_CACHE = None

def create_ottoman_ocr_engine():
    """
    Creates and configures the OCR Engine according to the active settings.
    If an OpenAI compatible LLM_API_KEY is provided, it prioritizes the powerful VLMOCREngine.
    Otherwise, it falls back to the local OttomanOCREngine (Kraken/EasyOCR/TrOCR).
    """
    global _ENGINE_CACHE
    if _ENGINE_CACHE is not None:
        return _ENGINE_CACHE

    api_key = settings.LLM_API_KEY or os.getenv("LLM_API_KEY")
    if api_key and settings.OCR_ENGINE != "trocr":
        # We have a valid Vision API key and the user hasn't explicitly forced trocr
        model = "gemini-2.5-flash"  # Can be configured via env if needed
        _ENGINE_CACHE = VLMOCREngine(api_key=api_key, model_name=model)
        return _ENGINE_CACHE

    enable_kraken = (settings.OCR_ENGINE == "kraken")
    enable_easyocr = (settings.OCR_ENGINE == "easyocr") or enable_kraken
    enable_trocr = (settings.OCR_ENGINE == "trocr")
    enable_tesseract = (settings.OCR_ENGINE == "tesseract")
    
    # Always make sure we have at least one fallback or segmenter
    if enable_kraken or enable_trocr:
        enable_easyocr = True
        
    if not (enable_kraken or enable_easyocr or enable_trocr or enable_tesseract):
        enable_easyocr = True
        
    engine = OttomanOCREngine(
        enable_kraken=enable_kraken,
        enable_easyocr=enable_easyocr,
        enable_trocr=enable_trocr,
        enable_tesseract=enable_tesseract,
        trocr_model=settings.OCR_MODEL_NAME,
        gpu=True
    )
    
    # Force the primary engine to be what the user requested, overriding the auto-selection order
    if settings.OCR_ENGINE in engine.engines:
        engine._primary_engine = settings.OCR_ENGINE
        
    _ENGINE_CACHE = engine
    return _ENGINE_CACHE
