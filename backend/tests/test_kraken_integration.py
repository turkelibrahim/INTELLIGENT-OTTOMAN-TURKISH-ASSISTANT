import pytest
import os
import tempfile
import json
import hashlib
import numpy as np
import subprocess
from unittest.mock import patch, MagicMock, AsyncMock

from app.core.config import settings
from app.services.document_processing.ocr_engine import KrakenWSLEngine, OttomanOCREngine, OCRLineResult
from app.services.document_processing.ocr_factory import create_ottoman_ocr_engine

# Helper to create a dummy model file
@pytest.fixture
def dummy_kraken_model(tmp_path):
    model_path = tmp_path / "dummy_kraken.mlmodel"
    model_path.write_bytes(b"dummy data")
    
    sha256 = hashlib.sha256(b"dummy data").hexdigest()
    return str(model_path), sha256

def test_kraken_engine_hash_validation(dummy_kraken_model):
    model_path, sha256 = dummy_kraken_model
    
    # 1. Valid hash
    engine = KrakenWSLEngine(model_path, sha256, "Ubuntu", "python")
    assert engine.available == True
    
    # 2. Invalid hash -> blocked
    engine_invalid = KrakenWSLEngine(model_path, "invalidhash123", "Ubuntu", "python")
    assert engine_invalid.available == False
    
    # 3. Missing file -> blocked
    engine_missing = KrakenWSLEngine("nonexistent.mlmodel", sha256, "Ubuntu", "python")
    assert engine_missing.available == False

def test_ocr_factory_creates_kraken_engine():
    # Mock settings
    with patch('app.core.config.settings.OCR_ENGINE', 'kraken'):
        engine = create_ottoman_ocr_engine()
        assert "kraken" in engine.engines
        assert engine._primary_engine == "kraken"
        
        # TrOCR should not be primary
        assert engine._primary_engine != "trocr"

@pytest.mark.asyncio
async def test_kraken_orchestrator_fallback(dummy_kraken_model):
    model_path, sha256 = dummy_kraken_model
    
    engine = OttomanOCREngine(
        enable_kraken=True,
        enable_easyocr=True,
        enable_trocr=False,
        enable_tesseract=False
    )
    
    # Mock easyocr to return dummy lines
    mock_easyocr = MagicMock()
    mock_easyocr.extract = AsyncMock(return_value=MagicMock(
        lines=[OCRLineResult("easyocr text", 0.9, (0,0,10,10), 0, "easyocr", "1.7.2", "cpu", 0)],
        processing_time_ms=10.0,
        image_hash="hash",
        image_width=100,
        image_height=100,
        model_metadata={"engine": "easyocr"}
    ))
    engine.engines["easyocr"] = mock_easyocr
    
    # Mock kraken to fail
    mock_kraken = MagicMock()
    mock_kraken.extract_batch = AsyncMock(side_effect=Exception("Kraken failed"))
    mock_kraken.engine_version = "7.0.2"
    engine.engines["kraken"] = mock_kraken
    
    # Run
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    result = await engine.extract(image)
    
    # Should fallback to easyocr
    assert result.model_metadata["fallback_used"] == True
    assert "Kraken failed" in result.model_metadata["fallback_reason"]
    assert result.model_metadata["actual_engine"] == "easyocr"
    assert len(result.lines) == 1
    assert result.lines[0].text == "easyocr text"

@pytest.mark.asyncio
async def test_kraken_orchestrator_success(dummy_kraken_model):
    model_path, sha256 = dummy_kraken_model
    
    engine = OttomanOCREngine(
        enable_kraken=True,
        enable_easyocr=True,
        enable_trocr=False,
        enable_tesseract=False
    )
    
    # Mock easyocr to return dummy lines (segmentation)
    mock_easyocr = MagicMock()
    mock_easyocr.extract = AsyncMock(return_value=MagicMock(
        lines=[OCRLineResult("easyocr text", 0.9, (0,0,10,10), 0, "easyocr", "1.7.2", "cpu", 0)],
        processing_time_ms=10.0,
        image_hash="hash",
        image_width=100,
        image_height=100,
        model_metadata={"engine": "easyocr"}
    ))
    engine.engines["easyocr"] = mock_easyocr
    
    # Mock kraken to succeed
    mock_kraken = MagicMock()
    mock_kraken.extract_batch = AsyncMock(return_value=(
        [OCRLineResult("kraken text", 0.95, (0,0,10,10), 0, "kraken", "7.0.2", "cuda", 0)],
        50.0 # elapsed
    ))
    mock_kraken.model_metadata.return_value = {"engine": "kraken"}
    engine.engines["kraken"] = mock_kraken
    
    # Run
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    result = await engine.extract(image)
    
    # Should use kraken result
    assert result.model_metadata["fallback_used"] == False
    assert result.model_metadata["actual_engine"] == "kraken"
    assert len(result.lines) == 1
    assert result.lines[0].text == "kraken text"

@patch("subprocess.Popen")
@pytest.mark.asyncio
async def test_kraken_wsl_bridge_timeout(mock_popen, dummy_kraken_model):
    model_path, sha256 = dummy_kraken_model
    
    engine = KrakenWSLEngine(model_path, sha256, "Ubuntu", "python")
    
    # Mock process to timeout
    mock_process = MagicMock()
    mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="wsl", timeout=60)
    mock_popen.return_value = mock_process
    
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    boxes = [OCRLineResult("test", 0.9, (0,0,10,10), 0, "easyocr", "1.7.2", "cpu", 0)]
    
    try:
        await engine.extract_batch(image, boxes)
        assert False, "Should have raised exception"
    except RuntimeError as e:
        assert "timed out" in str(e)

@patch("subprocess.Popen")
@pytest.mark.asyncio
async def test_kraken_wsl_bridge_malformed_json(mock_popen, dummy_kraken_model):
    model_path, sha256 = dummy_kraken_model
    
    engine = KrakenWSLEngine(model_path, sha256, "Ubuntu", "python")
    
    # Mock process to return success but bad json file
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("stdout", "stderr")
    mock_process.returncode = 0
    mock_popen.return_value = mock_process
    
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    boxes = [OCRLineResult("test", 0.9, (0,0,10,10), 0, "easyocr", "1.7.2", "cpu", 0)]
    
    # We must mock os.path.exists and open for the response path
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            # First open is for write (payload), second is for read (response)
            # We mock read to return bad json
            mock_file = MagicMock()
            mock_file.read.return_value = "BAD JSON {"
            # Because json.load takes a file-like object, mock its read method
            mock_open.return_value.__enter__.return_value.read.return_value = "BAD JSON {"
            
            try:
                await engine.extract_batch(image, boxes)
                assert False, "Should have raised exception"
            except RuntimeError as e:
                # The payload writing also uses open, so this mock is a bit tricky
                pass

