"""Tests for the real multi-engine Ottoman OCR system."""
import asyncio
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from app.services.document_processing.ocr_engine import (
    OttomanOCREngine,
    EasyOCREngine,
    OCRPageResult,
    OCRLineResult,
    analyze_line_candidate,
    filter_ocr_lines,
    is_garbage_ocr_text,
    is_non_ottoman_component_text,
    refine_line_bbox_to_text_ink,
)


def run_async(coro):
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


def _sample_image():
    """Create a simple test image with black text-like marks on white."""
    image = np.full((64, 128, 3), 255, dtype=np.uint8)
    # Draw some black marks to simulate text
    image[20:40, 20:110] = 0
    return image


def _line_filter_fixture():
    image = np.full((120, 420, 3), 255, dtype=np.uint8)
    for x in range(80, 350, 22):
        image[40:58, x : x + 10] = 0
        image[52:56, x + 13 : x + 17] = 0
    image[88:90, 10:410] = 0
    return image


def test_ottoman_ocr_engine_initializes_with_easyocr():
    """Verify OttomanOCREngine initializes with at least EasyOCR."""
    engine = OttomanOCREngine(
        enable_easyocr=True,
        enable_trocr=False,
        enable_tesseract=False,
        gpu=False,
    )

    assert "easyocr" in engine.engines
    assert engine._primary_engine == "easyocr"

    metadata = engine.model_metadata()
    assert metadata["orchestrator"] == "OttomanOCREngine"
    assert "easyocr" in metadata["available_engines"]
    assert metadata["engines"]["easyocr"]["engine"] == "easyocr"
    assert metadata["engines"]["easyocr"]["license"] == "Apache-2.0"


def test_ottoman_ocr_engine_extract_returns_page_result():
    """Verify OCR extract returns proper OCRPageResult with no mock text."""
    engine = OttomanOCREngine(
        enable_easyocr=True,
        enable_trocr=False,
        enable_tesseract=False,
        gpu=False,
    )

    result = run_async(engine.extract(_sample_image()))

    assert isinstance(result, OCRPageResult)
    assert result.engine_name == "easyocr"
    assert result.device in {"cpu", "cuda"}
    assert result.image_hash  # non-empty hash
    assert result.image_width == 128
    assert result.image_height == 64

    # CRITICAL: No mock/placeholder text in any line
    for line in result.lines:
        assert "[FALLBACK_OCR]" not in line.text
        assert "Ornek Osmanlica" not in line.text
        assert isinstance(line, OCRLineResult)
        assert isinstance(line.confidence, float)
        assert isinstance(line.bbox, tuple)
        assert len(line.bbox) == 4


def test_ottoman_ocr_engine_metadata_reports_no_fallback():
    """Verify metadata does not claim fallback mode."""
    engine = OttomanOCREngine(
        enable_easyocr=True,
        enable_trocr=False,
        enable_tesseract=False,
        gpu=False,
    )

    metadata = engine.model_metadata()
    assert metadata["primary_engine"] == "easyocr"
    # EasyOCR engine metadata should indicate it's a real engine
    easyocr_meta = metadata["engines"]["easyocr"]
    assert easyocr_meta["model_type"] == "CRAFT+CRNN"
    assert easyocr_meta["script"] == "Arabic"


def test_line_filter_rejects_empty_punctuation_and_low_conf_digit_noise():
    assert is_garbage_ocr_text("", 0.99)[0] is True
    assert is_garbage_ocr_text(" . ، ؛ ", 0.99)[0] is True
    assert is_garbage_ocr_text("اا٢ه٤١١ا١دعاق", 0.38)[0] is True
    assert is_garbage_ocr_text("عثمان غازى بروسه فتح اتدى", 0.88)[0] is False


def test_component_filter_rejects_latin_headers_and_keeps_ottoman_text():
    assert is_non_ottoman_component_text("Osmanlı Türkçesi Metinleri-I") is True
    assert is_non_ottoman_component_text("DIKKAT") is True
    assert is_non_ottoman_component_text("4") is True
    assert is_non_ottoman_component_text("يايدى كورديكم جنكله") is False


def test_line_filter_uses_geometry_ink_and_text_quality():
    image = _line_filter_fixture()
    accepted = analyze_line_candidate(image, (80, 40, 280, 18), "عثمان غازى بروسه فتح اتدى", 0.9)
    empty_text = analyze_line_candidate(image, (80, 40, 280, 18), "", 0.9)
    thin_rule = analyze_line_candidate(image, (10, 88, 400, 2), "ــ", 0.9)

    assert accepted.keep is True
    assert accepted.ink_density > 0
    assert empty_text.keep is False
    assert empty_text.reason == "empty_text"
    assert thin_rule.keep is False
    assert thin_rule.reason == "height_below_minimum"


def test_filter_ocr_lines_reindexes_and_suppresses_phantom_lines():
    image = _line_filter_fixture()
    lines = [
        OCRLineResult("عثمان غازى بروسه فتح اتدى", 0.9, (80, 40, 280, 18), 7, "test", "1", "cpu", 0),
        OCRLineResult("", 0.0, (20, 80, 300, 16), 8, "test", "1", "cpu", 0),
        OCRLineResult("اا٢ه٤١١ا١دعاق", 0.38, (80, 40, 280, 18), 9, "test", "1", "cpu", 0),
    ]

    kept, rejected = filter_ocr_lines(image, lines)

    assert [line.text for line in kept] == ["عثمان غازى بروسه فتح اتدى"]
    assert kept[0].line_index == 0
    assert {item["reason"] for item in rejected} == {"empty_text", "low_confidence_digit_noise"}


def test_refine_line_bbox_trims_isolated_left_margin_cluster():
    image = np.full((120, 500, 3), 255, dtype=np.uint8)
    image[35:55, 20:85] = 0
    for x in range(210, 455, 22):
        image[40:58, x : x + 10] = 0

    refined = refine_line_bbox_to_text_ink(image, (20, 32, 440, 32))

    assert refined[0] > 150
    assert refined[2] < 320



