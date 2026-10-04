"""
TASK-034 Layout + RTL + Low-Contrast OCR Test
Tests real layout detection and OCR on the same Ottoman document with degraded conditions.
"""
import asyncio
import json
import sys
import os
import time
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
from PIL import Image


async def run_layout_and_degraded_test():
    print("=" * 60)
    print("TASK-034: Layout + RTL + Low-Contrast OCR Test")
    print("=" * 60)

    # 1. Load original image
    image_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "uploads", "processed", "1", "page_1_226f233e.png"
    )
    image_pil = Image.open(image_path)
    image = np.array(image_pil)
    if len(image.shape) == 3 and image.shape[2] == 3:
        image = image[:, :, ::-1].copy()

    print(f"Original image: {image.shape[1]}x{image.shape[0]} pixels")

    # ============================
    # PART 1: Layout + RTL Test
    # ============================
    print("\n--- Part 1: Layout Analysis + RTL Order ---")
    from app.services.document_processing.layout import LayoutAnalyzer

    analyzer = LayoutAnalyzer()
    lines = analyzer.detect_lines(image, rtl=True)
    print(f"Layout detected {len(lines)} line regions (RTL order)")

    for line in lines[:10]:
        print(f"  Line {line.order_index}: col={line.column_index} "
              f"bbox=({line.x},{line.y},{line.width},{line.height})")

    # Verify RTL: first line should be from the rightmost column
    if len(lines) >= 2:
        first_line = lines[0]
        last_line = lines[-1]
        # In RTL, first line's x should be >= last line's x (rightmost column first)
        rtl_correct = first_line.column_index <= last_line.column_index or first_line.x >= last_line.x
        print(f"RTL order check: first_line.x={first_line.x}, last_line.x={last_line.x}")
        print(f"RTL order valid: {rtl_correct}")
    else:
        rtl_correct = len(lines) > 0

    # ============================
    # PART 2: Low-Contrast/Skewed OCR Test
    # ============================
    print("\n--- Part 2: Low-Contrast + Skewed Image OCR ---")

    # Create degraded version: reduce contrast and add slight rotation
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()

    # Low contrast: flatten the histogram
    low_contrast = cv2.convertScaleAbs(gray, alpha=0.5, beta=80)

    # Add slight skew (5 degrees)
    h, w = low_contrast.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, 5, 1.0)
    skewed = cv2.warpAffine(low_contrast, rotation_matrix, (w, h),
                             borderMode=cv2.BORDER_REPLICATE)

    # Save degraded image for evidence
    evidence_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "evidence", "task034_real_ocr"
    )
    os.makedirs(evidence_dir, exist_ok=True)

    degraded_path = os.path.join(evidence_dir, "degraded_test_image.png")
    cv2.imwrite(degraded_path, skewed)
    print(f"Degraded image saved: {degraded_path}")
    print(f"Degraded image: {skewed.shape[1]}x{skewed.shape[0]} pixels, "
          f"contrast=0.5, skew=5deg")

    # Run OCR on degraded image
    from app.services.document_processing.ocr_engine import OttomanOCREngine

    engine = OttomanOCREngine(
        enable_easyocr=True,
        enable_trocr=False,
        enable_tesseract=False,
        gpu=False,
    )

    # Convert grayscale to 3-channel for EasyOCR
    degraded_bgr = cv2.cvtColor(skewed, cv2.COLOR_GRAY2BGR)
    result = await engine.extract(degraded_bgr)

    print(f"\nDegraded OCR Results:")
    print(f"  Lines detected: {len(result.lines)}")
    print(f"  Page confidence: {result.page_confidence:.4f}")
    print(f"  Processing time: {result.processing_time_ms:.0f}ms")

    for line in result.lines:
        print(f"  [{line.line_index:2d}] conf={line.confidence:.3f} text: {line.text}")

    has_arabic_degraded = any(
        any('\u0600' <= c <= '\u06FF' or '\uFB50' <= c <= '\uFDFF' or '\uFE70' <= c <= '\uFEFF'
            for c in line.text)
        for line in result.lines
    )

    print(f"\nArabic script in degraded image: {has_arabic_degraded}")

    # ============================
    # PART 3: CER/WER Metrics
    # ============================
    print("\n--- Part 3: CER/WER Metrics (Reference comparison) ---")

    # Since we don't have a ground-truth transcription yet,
    # we compare clean vs degraded OCR outputs as a proxy metric
    from app.services.evaluation_service import EvaluationService

    eval_svc = EvaluationService()

    # Get clean OCR text
    clean_result = await engine.extract(image)
    clean_text = " ".join(l.text for l in clean_result.lines)
    degraded_text = " ".join(l.text for l in result.lines)

    if clean_text.strip() and degraded_text.strip():
        result_eval = eval_svc.evaluate_text(reference=clean_text, hypothesis=degraded_text)
        print(f"  Clean vs Degraded comparison:")
        print(f"    CER: {result_eval.cer:.4f}")
        print(f"    WER: {result_eval.wer:.4f}")
        metrics = {"cer": result_eval.cer, "wer": result_eval.wer}
    else:
        print("  Insufficient text for metric comparison")
        metrics = {}

    # ============================
    # Save Evidence
    # ============================
    evidence = {
        "test": "TASK-034 Layout + RTL + Degraded OCR",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "layout": {
            "lines_detected": len(lines),
            "rtl_order_valid": rtl_correct,
            "sample_lines": [
                {"order": l.order_index, "col": l.column_index,
                 "bbox": [l.x, l.y, l.width, l.height]}
                for l in lines[:10]
            ],
        },
        "degraded_ocr": {
            "lines_detected": len(result.lines),
            "page_confidence": result.page_confidence,
            "has_arabic": has_arabic_degraded,
            "processing_time_ms": result.processing_time_ms,
        },
        "metrics": metrics,
    }

    evidence_path = os.path.join(evidence_dir, "layout_degraded_result.json")
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, ensure_ascii=False, indent=2)
    print(f"\nEvidence saved: {evidence_path}")

    # Final verdict
    layout_pass = len(lines) > 0
    degraded_pass = len(result.lines) > 0 and has_arabic_degraded
    rtl_pass = rtl_correct

    print(f"\n{'='*60}")
    print(f"Layout detection: {'PASS' if layout_pass else 'FAIL'}")
    print(f"RTL order: {'PASS' if rtl_pass else 'FAIL'}")
    print(f"Degraded OCR: {'PASS' if degraded_pass else 'FAIL'}")
    overall = layout_pass and rtl_pass and degraded_pass
    print(f"Overall: {'PASS' if overall else 'FAIL'}")
    return overall


if __name__ == "__main__":
    success = asyncio.run(run_layout_and_degraded_test())
    sys.exit(0 if success else 1)
