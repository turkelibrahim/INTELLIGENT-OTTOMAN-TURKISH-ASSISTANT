"""
TASK-034 Real OCR Test — Run EasyOCR on actual Ottoman document.
This script tests the real OCR engine on an uploaded Ottoman page image.
"""
import asyncio
import json
import sys
import os
import time
import io

# Fix Windows console encoding for Arabic text
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from PIL import Image


async def run_real_ocr_test():
    print("=" * 60)
    print("TASK-034: Real Ottoman OCR Test")
    print("=" * 60)

    # 1. Load real Ottoman document image
    image_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "uploads", "processed", "1", "page_1_226f233e.png"
    )

    if not os.path.exists(image_path):
        print(f"FAIL: Test image not found at {image_path}")
        return False

    image_pil = Image.open(image_path)
    image = np.array(image_pil)
    # Convert RGB to BGR for OpenCV compatibility
    if len(image.shape) == 3 and image.shape[2] == 3:
        image = image[:, :, ::-1].copy()

    if image is None:
        print(f"FAIL: Could not read image at {image_path}")
        return False

    print(f"Image loaded: {image.shape[1]}x{image.shape[0]} pixels")
    print(f"Image path: {image_path}")

    # 2. Initialize real OCR engine
    print("\nInitializing OttomanOCREngine...")
    start = time.perf_counter()

    from app.services.document_processing.ocr_engine import OttomanOCREngine

    engine = OttomanOCREngine(
        enable_easyocr=True,
        enable_trocr=False,  # Skip TrOCR for now (CPU-only)
        enable_tesseract=False,  # Tesseract not installed yet
        gpu=False,  # CPU torch installed
    )

    init_time = (time.perf_counter() - start) * 1000
    print(f"Engine initialized in {init_time:.0f}ms")
    print(f"Available engines: {list(engine.engines.keys())}")
    print(f"Primary engine: {engine._primary_engine}")

    # 3. Run real OCR
    print("\nRunning OCR on real Ottoman document...")
    result = await engine.extract(image)

    print(f"\nOCR Results:")
    print(f"  Engine: {result.engine_name} v{result.engine_version}")
    print(f"  Device: {result.device}")
    print(f"  Lines detected: {len(result.lines)}")
    print(f"  Page confidence: {result.page_confidence:.4f}")
    print(f"  Processing time: {result.processing_time_ms:.0f}ms")
    print(f"  Image hash: {result.image_hash}")
    print(f"  Image size: {result.image_width}x{result.image_height}")

    # 4. Print each detected line
    print(f"\n{'='*60}")
    print("Detected Lines (RTL text):")
    print(f"{'='*60}")
    for line in result.lines:
        print(f"  [{line.line_index:2d}] conf={line.confidence:.3f} "
              f"bbox=({line.bbox[0]},{line.bbox[1]},{line.bbox[2]},{line.bbox[3]}) "
              f"text: {line.text}")

    # 5. Verify no mock/placeholder text
    for line in result.lines:
        if "[FALLBACK_OCR]" in line.text or "Ornek Osmanlica" in line.text:
            print("\nFAIL: Mock/placeholder text detected!")
            return False

    # 6. Verify we got actual Arabic-script text
    has_arabic = any(
        any('\u0600' <= c <= '\u06FF' or '\uFB50' <= c <= '\uFDFF' or '\uFE70' <= c <= '\uFEFF'
            for c in line.text)
        for line in result.lines
    )

    print(f"\nArabic/Ottoman script detected: {has_arabic}")

    # 7. Save evidence
    evidence_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "evidence", "task034_real_ocr"
    )
    os.makedirs(evidence_dir, exist_ok=True)

    evidence = {
        "test": "TASK-034 Real Ottoman OCR",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "image_path": image_path,
        "image_size": f"{result.image_width}x{result.image_height}",
        "image_hash": result.image_hash,
        "engine": result.engine_name,
        "engine_version": result.engine_version,
        "device": result.device,
        "lines_detected": len(result.lines),
        "page_confidence": result.page_confidence,
        "processing_time_ms": result.processing_time_ms,
        "model_metadata": result.model_metadata,
        "has_arabic_script": has_arabic,
        "lines": [
            {
                "index": l.line_index,
                "text": l.text,
                "confidence": l.confidence,
                "bbox": list(l.bbox),
            }
            for l in result.lines
        ],
    }

    evidence_path = os.path.join(evidence_dir, "real_ocr_result.json")
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, ensure_ascii=False, indent=2)
    print(f"\nEvidence saved to: {evidence_path}")

    # 8. Final verdict
    if len(result.lines) > 0 and has_arabic:
        print("\n✓ PASS: Real OCR produced actual Arabic/Ottoman text from document.")
        return True
    elif len(result.lines) > 0:
        print("\n⚠ PARTIAL: OCR produced text but no Arabic script detected.")
        return True
    else:
        print("\n✗ FAIL: OCR produced no lines.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_real_ocr_test())
    sys.exit(0 if success else 1)
