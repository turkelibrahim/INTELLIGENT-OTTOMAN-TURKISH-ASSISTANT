import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from app.core.config import settings
from app.services.document_processing.pipeline import DocumentProcessingPipeline
from app.services.document_processing.preprocessor import ImagePreprocessor


def run_async(coro):
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


from app.services.document_processing.ocr_engine import OCRPageResult, OCRLineResult

class StubOCREngine:
    async def extract(self, image: np.ndarray) -> OCRPageResult:
        return OCRPageResult(
            lines=[
                OCRLineResult(
                    line_index=0, 
                    text="نمونه متن", 
                    confidence=0.8, 
                    bbox=(0,0,10,10),
                    engine_name="stub",
                    engine_version="1.0",
                    device="cpu",
                    processing_time_ms=5.0
                )
            ],
            engine_name="stub",
            engine_version="1.0",
            device="cpu",
            page_confidence=0.8,
            processing_time_ms=10.0,
            image_hash="fakehash",
            image_width=100,
            image_height=100,
            model_metadata={}
        )


class StubTranslator:
    async def translate(self, text):
        assert text == "نمونه متن"
        return {
            "transliterated_text": "numune metin",
            "modernized_text": "ornek metin",
            "summary_text": "Ornek metin ozeti.",
            "quality_flags": [],
            "translation_confidence": 0.7,
        }


class StubNERExtractor:
    async def extract_entities(self, text):
        assert text == "ornek metin"
        return {
            "extracted_entities": [{"text": "ornek", "label": "TERM"}],
            "ner_confidence": 0.6,
        }


def _sample_image():
    image = np.full((80, 120, 3), 255, dtype=np.uint8)
    image[25:55, 30:90] = 0
    return image


def test_image_preprocessor_process_contract_returns_scores():
    processed, scores = ImagePreprocessor().process(_sample_image())

    assert processed.ndim == 2
    assert 0.0 <= scores["preprocessing_confidence"] <= 1.0
    assert scores["profile"] == "temiz_baski"
    assert scores["parameters"]["threshold_method"] == "otsu"


def test_preprocessor_skips_deskew_when_text_preservation_would_drop(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    preprocessor = ImagePreprocessor()
    image = _sample_image()
    destructive = np.zeros_like(image)

    monkeypatch.setattr(preprocessor, "correct_skew_with_angle", lambda current: (destructive, 8.0))
    monkeypatch.setattr(preprocessor, "_is_text_preservation_loss", lambda original, candidate: True)

    preprocessor.process_image_array(image, "temiz_baski", document_id=123, page_no=1)

    manifest_path = tmp_path / "uploads" / "processed" / "123" / "page_1" / "processing_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    deskew_stage = next(stage for stage in manifest["stages"] if stage["id"] == "03_deskew")

    assert deskew_stage["status"] == "SKIPPED"


def test_document_processing_pipeline_smoke_with_stubbed_ai_components():
    pipeline = object.__new__(DocumentProcessingPipeline)
    pipeline.preprocessor = ImagePreprocessor()
    pipeline.ocr_engine = StubOCREngine()
    pipeline.translator = StubTranslator()
    pipeline.ner_extractor = StubNERExtractor()

    result = run_async(pipeline.process_document(_sample_image()))

    assert result["status"] == "COMPLETED"
    assert result["raw_ocr_text"] == "نمونه متن"
    assert result["transliterated_text"] == "numune metin"
    assert result["modernized_text"] == "ornek metin"
    assert result["summary_text"] == "Ornek metin ozeti."
    assert result["transformation_quality"]["modernization_distinct_from_transliteration"] is True
    assert result["entities"] == [{"text": "ornek", "label": "TERM"}]
    assert 0.0 <= result["quality"]["ocr_confidence"] <= 1.0


