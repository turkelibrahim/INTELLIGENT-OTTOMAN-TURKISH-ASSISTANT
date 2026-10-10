import os
import sys
import time
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

import torch
import cv2
import numpy as np

def get_vram():
    if torch.cuda.is_available():
        return torch.cuda.memory_allocated() / (1024**2) # MB
    return 0

async def run_benchmark():
    print("=== OCR PERFORMANCE AUDIT BENCHMARK ===")
    
    # 1. Image Loading
    start_vram = get_vram()
    start_time = time.perf_counter()
    image_path = Path(os.path.dirname(__file__)) / ".." / "backend" / "uploads" / "originals" / "175" / "175_230f03eb.jpg"
    if not image_path.exists():
        print("Image not found!")
    
    from app.services.image_io import read_image_unicode_safe
    image = read_image_unicode_safe(image_path)
    print(f"[Image Loading] Time: {(time.perf_counter()-start_time)*1000:.2f} ms | VRAM: {get_vram():.2f} MB (+{get_vram()-start_vram:.2f} MB)")
    
    # 2. Preprocessing
    from app.services.document_processing.preprocessor import ImagePreprocessor
    start_time = time.perf_counter()
    preprocessor = ImagePreprocessor()
    safe_image, prep = preprocessor.process(image)
    print(f"[Preprocessing] Time: {(time.perf_counter()-start_time)*1000:.2f} ms | VRAM: {get_vram():.2f} MB")
    
    # 3. OCR Load
    start_time = time.perf_counter()
    from app.services.document_processing.ocr_factory import create_ottoman_ocr_engine
    ocr_engine = create_ottoman_ocr_engine()
    print(f"[OCR Engine Load] Time: {(time.perf_counter()-start_time)*1000:.2f} ms | VRAM: {get_vram():.2f} MB")
    
    # 4. OCR Inference
    start_time = time.perf_counter()
    ocr_result = await ocr_engine.extract(safe_image)
    print(f"[OCR Inference] Time: {(time.perf_counter()-start_time)*1000:.2f} ms | VRAM: {get_vram():.2f} MB")
    
    ocr_text = "\n".join(line.text for line in ocr_result.lines).strip()
    if not ocr_text:
        ocr_text = "نمونه متين" # dummy text
    
    os.environ["LLM_PROVIDER"] = "gemini" # bypass the openai error, but we'll use mock anyway
    
    # 5. Transliteration Load
    start_time = time.perf_counter()
    from app.services.transliteration_service import TransliterationEngine
    trans_engine = TransliterationEngine(use_mock=True)
    print(f"[Transliteration Engine Load] Time: {(time.perf_counter()-start_time)*1000:.2f} ms | VRAM: {get_vram():.2f} MB")
    
    # 6. Transliteration Inference
    start_time = time.perf_counter()
    latin_text = trans_engine.transliterate_academic(ocr_text)
    print(f"[Transliteration Inference] Time: {(time.perf_counter()-start_time)*1000:.2f} ms | VRAM: {get_vram():.2f} MB")
    
    if type(latin_text) is tuple: latin_text = latin_text[0]
    
    # 7. Translator
    start_time = time.perf_counter()
    from app.services.document_processing.translator import Translator
    translator = Translator()
    print(f"[Translator Engine Load] Time: {(time.perf_counter()-start_time)*1000:.2f} ms | VRAM: {get_vram():.2f} MB")
    
    start_time = time.perf_counter()
    # Translator is usually not async directly or uses ollama API which handles its own memory
    modern_text = translator.translate(latin_text) if hasattr(translator, 'translate') else "mock"
    print(f"[Translation Inference] Time: {(time.perf_counter()-start_time)*1000:.2f} ms | VRAM: {get_vram():.2f} MB")
    
    # 8. NER Extractor
    start_time = time.perf_counter()
    from app.services.document_processing.ner_extractor import NERExtractor
    ner_extractor = NERExtractor(enable_hf=False)
    print(f"[NER Engine Load] Time: {(time.perf_counter()-start_time)*1000:.2f} ms | VRAM: {get_vram():.2f} MB")
    
    start_time = time.perf_counter()
    entities = ner_extractor.extract(modern_text if modern_text else "mock")
    print(f"[NER Inference] Time: {(time.perf_counter()-start_time)*1000:.2f} ms | VRAM: {get_vram():.2f} MB")
    
    # 9. Intelligence
    start_time = time.perf_counter()
    from app.services.document_intelligence_service import DocIntelligenceEngine
    intelligence = DocIntelligenceEngine(use_mock=True)
    print(f"[Intelligence Engine Load] Time: {(time.perf_counter()-start_time)*1000:.2f} ms | VRAM: {get_vram():.2f} MB")

    print("=== BENCHMARK COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
