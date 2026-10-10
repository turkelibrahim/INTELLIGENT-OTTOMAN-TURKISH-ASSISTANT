import pytest
import numpy as np
from app.services.document_processing.ocr_engine import EasyOCREngine, KrakenWSLEngine

@pytest.mark.asyncio
async def test_easyocr_detection_only_returns_valid_bboxes():
    # Arrange
    engine = EasyOCREngine()
    # Create a dummy image (e.g., 800x600 white image with some black rectangles acting as text)
    dummy_image = np.full((600, 800, 3), 255, dtype=np.uint8)
    dummy_image[100:150, 100:700] = 0  # Dummy line 1
    dummy_image[200:250, 100:700] = 0  # Dummy line 2
    
    # Act
    # detect_only=True
    result = await engine.extract(dummy_image, detect_only=True)
    
    # Assert
    assert result is not None
    assert result.lines is not None
    # Depending on EasyOCR dummy inference, it should find at least one or nothing, but the contract is valid list
    assert isinstance(result.lines, list)

@pytest.mark.asyncio
async def test_kraken_engine_receives_and_processes_bboxes(monkeypatch):
    from app.services.document_processing.ocr_engine import OttomanOCREngine, KrakenWSLEngine, OCRLineResult
    
    orchestrator = OttomanOCREngine.__new__(OttomanOCREngine)
    orchestrator.engines = {}
    orchestrator._primary_engine = None
    
    # Manually inject our engines
    kraken = KrakenWSLEngine(
        model_path="dummy_path",
        model_sha256="dummy_sha",
        distro="dummy_distro",
        python_path="dummy_python"
    )
    kraken._available = True  # bypass hash check
    
    from app.services.document_processing.ocr_engine import OCRPageResult
    
    async def mock_extract(image, detect_only=False):
        assert detect_only is True
        return OCRPageResult(
            lines=[
                OCRLineResult(text="dummy", bbox=(10, 10, 100, 50), confidence=0.9, line_index=0, engine_name="easyocr", engine_version="1", device="cpu", processing_time_ms=0),
                OCRLineResult(text="dummy2", bbox=(10, 60, 100, 100), confidence=0.9, line_index=1, engine_name="easyocr", engine_version="1", device="cpu", processing_time_ms=0)
            ],
            engine_name="easyocr",
            engine_version="1",
            device="cpu",
            processing_time_ms=0,
            image_width=800,
            image_height=600,
            model_metadata={},
            page_confidence=0.9,
            image_hash="dummy_hash"
        )
    
    class DummyEasyOcrEngine:
        async def extract(self, image, detect_only=False):
            return await mock_extract(image, detect_only)
        def model_metadata(self):
            return {}

    orchestrator.engines = {"kraken": kraken, "easyocr": DummyEasyOcrEngine()}
    orchestrator._primary_engine = "kraken"
    
    # Mock kraken.extract_batch
    async def mock_extract_batch(image, boxes):
        # kraken received 2 boxes
        assert len(boxes) == 2
        return [
            OCRLineResult(text="kraken text 1", confidence=0.9, bbox=(10,10,100,50), line_index=0, engine_name="kraken", engine_version="7", device="cpu", processing_time_ms=0),
            OCRLineResult(text="kraken text 2", confidence=0.8, bbox=(10,60,100,100), line_index=1, engine_name="kraken", engine_version="7", device="cpu", processing_time_ms=0)
        ], 1.0

    kraken.extract_batch = mock_extract_batch
    
    dummy_image = np.full((600, 800, 3), 255, dtype=np.uint8)
    result = await orchestrator.extract(dummy_image)
    
    assert len(result.lines) == 2
    assert result.lines[0].text == "kraken text 1"
    assert result.lines[1].text == "kraken text 2"
    assert result.engine_name == "kraken"
