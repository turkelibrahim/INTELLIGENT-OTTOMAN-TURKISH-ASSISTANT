import cv2
import time
import numpy as np
from app.services.document_processing.ocr_engine import EasyOCREngine, KrakenWSLEngine
from app.core.config import settings

def main():
    img_path = r"C:\projeler\INTELLIGENT OTTOMAN TURKISH ASSISTANT\backend\uploads\processed\81\page_1\00_original.png"
    img = cv2.imread(img_path)
    if img is None:
        print(f"Could not load image: {img_path}")
        return
        
    print("--- 1. EASYOCR ONLY ---")
    easy = EasyOCREngine(languages=["ar"], gpu=True)
    t0 = time.time()
    easy_res = None
    import asyncio
    easy_res = asyncio.run(easy.extract(img))
    t1 = time.time()
    
    print(f"EasyOCR Lines: {len(easy_res.lines)}")
    print(f"EasyOCR Latency: {t1 - t0:.2f}s")
    easy_text = "\n".join([l.text for l in easy_res.lines])
    print(f"EasyOCR Sample text:\n{easy_text[:200]}...")
    
    print("\n--- 2. KRAKEN ONLY (using EasyOCR bbox) ---")
    kraken = KrakenWSLEngine(
        model_path=settings.OCR_KRAKEN_MODEL_PATH,
        model_sha256=settings.OCR_KRAKEN_MODEL_SHA256,
        distro=settings.OCR_KRAKEN_WSL_DISTRO,
        python_path=settings.OCR_KRAKEN_WSL_PYTHON
    )
    t2 = time.time()
    try:
        kraken_lines, kraken_elapsed = asyncio.run(kraken.extract_batch(img, easy_res.lines))
        t3 = time.time()
        print(f"Kraken Lines: {len(kraken_lines)}")
        print(f"Kraken inference internal elapsed: {kraken_elapsed}ms")
        print(f"Kraken total Latency (including EasyOCR bbox time): {(t1-t0) + (t3-t2):.2f}s")
        kraken_text = "\n".join([l.text for l in kraken_lines])
        print(f"Kraken Sample text:\n{kraken_text[:200]}...")
    except Exception as e:
        print(f"Kraken failed: {e}")

if __name__ == "__main__":
    main()
