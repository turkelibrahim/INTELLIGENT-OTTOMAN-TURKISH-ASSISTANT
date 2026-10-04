import pytest
import os
import json
import hashlib
from pathlib import Path
from app.services.document_processing.ocr_engine import EasyOCREngine

@pytest.fixture
def temp_models_dir(tmp_path):
    models_dir = tmp_path / "models" / "easyocr"
    models_dir.mkdir(parents=True)
    
    model_bytes = b"clean"
    model_hash = hashlib.sha256(model_bytes).hexdigest()

    # Create fake models and manifest
    manifest = {
        "schema_version": "1.0",
        "generated_at_utc": "2026-08-02T00:00:00+00:00",
        "engine": "EasyOCR",
        "engine_version": "1.7.2",
        "download_enabled": False,
        "files": {
            "fake_model.pth": {
                "sha256": model_hash,
                "size_bytes": len(model_bytes),
            }
        }
    }
    
    with open(models_dir / "manifest.json", "w") as f:
        json.dump(manifest, f)
        
    Path(models_dir / "fake_model.pth").write_bytes(model_bytes)
    
    return models_dir

def test_easyocr_manifest_missing(tmp_path):
    models_dir = tmp_path / "models" / "easyocr"
    models_dir.mkdir(parents=True)
    
    engine = EasyOCREngine.__new__(EasyOCREngine)
    with pytest.raises(RuntimeError, match="EasyOCR model manifest not found"):
        engine._verify_models(str(models_dir))

def test_easyocr_model_missing(temp_models_dir):
    os.remove(temp_models_dir / "fake_model.pth")
    engine = EasyOCREngine.__new__(EasyOCREngine)
    with pytest.raises(RuntimeError, match="EasyOCR model file fake_model.pth missing"):
        engine._verify_models(str(temp_models_dir))

def test_easyocr_model_corrupted(temp_models_dir):
    with open(temp_models_dir / "fake_model.pth", "wb") as f:
        f.write(b"dirty")
        
    engine = EasyOCREngine.__new__(EasyOCREngine)
    with pytest.raises(RuntimeError, match="Checksum mismatch for EasyOCR model"):
        engine._verify_models(str(temp_models_dir))

def test_easyocr_model_size_mismatch(temp_models_dir):
    manifest_path = temp_models_dir / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["files"]["fake_model.pth"]["size_bytes"] = 1
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    engine = EasyOCREngine.__new__(EasyOCREngine)
    with pytest.raises(RuntimeError, match="Size mismatch for EasyOCR model"):
        engine._verify_models(str(temp_models_dir))

def test_easyocr_model_valid(temp_models_dir):
    engine = EasyOCREngine.__new__(EasyOCREngine)
    engine._verify_models(str(temp_models_dir))
    # Should not raise exception
