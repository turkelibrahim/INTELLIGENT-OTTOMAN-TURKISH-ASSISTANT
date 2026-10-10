import sys
import time
import cv2
import easyocr
import numpy as np
import asyncio
import os

# Add backend to path
sys.path.insert(0, os.path.abspath('.'))

from app.services.document_processing.ocr_engine import KrakenWSLEngine, OCRLineResult
def main():
    print("Loading EasyOCR...")
    reader = easyocr.Reader(['ar'], gpu=True)
    print("Loading Kraken...")
    kraken = KrakenWSLEngine(
        model_path="C:\\projeler\\INTELLIGENT OTTOMAN TURKISH ASSISTANT\\models\\recognition\\ottoman_recognition_final_v1.mlmodel",
        model_sha256="f5abbba1976e9782ddf5d7185d911722c74558e12b57a12566c96e22a3e3b963",
        distro="Ubuntu-24.04",
        python_path="/home/black_man/venvs/ottoman_kraken/bin/python"
    )
    
    img_path = "..\\uploads\\originals\\1\\1_64e34610.png"
    print(f"Reading image {img_path}")
    image = cv2.imread(img_path)
    
    # 1. Preprocessing (none really, just timing)
    t0 = time.perf_counter()
    # 2. EasyOCR detection ONLY
    t1 = time.perf_counter()
    horizontal_list, free_list = reader.detect(image)
    t2 = time.perf_counter()
    
    # 3. EasyOCR full readtext (for comparison)
    t3 = time.perf_counter()
    results = reader.readtext(image, detail=1, paragraph=False)
    t4 = time.perf_counter()
    
    # 4. Kraken Inference
    # Convert horizontal_list to OCRLineResult
    lines = []
    if horizontal_list and len(horizontal_list) > 0:
        for idx, bbox in enumerate(horizontal_list[0]):
            x_min, x_max, y_min, y_max = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            lines.append(OCRLineResult(
                text="", 
                confidence=1.0, 
                bbox=(x_min, y_min, x_max - x_min, y_max - y_min), 
                line_index=idx,
                engine_name="easyocr",
                engine_version="",
                device="",
                processing_time_ms=0.0
            ))
            
    t5 = time.perf_counter()
    kraken_lines, elapsed_ms = asyncio.run(kraken.extract_batch(image, lines))
    t6 = time.perf_counter()
    
    print("\n--- PERFORMANCE BENCHMARK (Full Page Pipeline) ---")
    print(f"Image: {img_path}")
    print(f"Total Lines: {len(lines)}")
    print("\n[EasyOCR]")
    print(f"  Detection Only (CRAFT): {t2 - t1:.4f}s")
    print(f"  Full Pipeline (detect + readtext): {t4 - t3:.4f}s")
    print(f"  Time Wasted on CRNN Recognition: {(t4-t3) - (t2-t1):.4f}s")
    
    print("\n[Kraken]")
    kraken_inference_time = t6 - t5
    print(f"  Inference (Network + WSL + GPU): {kraken_inference_time:.4f}s")
    print(f"  Reported internal elapsed: {elapsed_ms} ms")
    if elapsed_ms and isinstance(elapsed_ms, (int, float)) and elapsed_ms > 0:
        overhead = kraken_inference_time - (elapsed_ms / 1000.0)
        print(f"  Communication Overhead: {overhead:.4f}s")
        
    print("\n[Methodology Note]")
    print("This measures FULL PAGE pipelines, not single crops. Performance benchmark is separate from accuracy benchmark.")
    
if __name__ == "__main__":
    main()
