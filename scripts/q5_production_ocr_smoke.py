from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

import numpy as np
import torch
from PIL import Image

from app.services.document_processing.ocr_engine import OttomanOCREngine


async def main() -> int:
    image_path = PROJECT_ROOT / "evidence" / "ocr_quality_real" / "input" / "images" / "page_002.png"
    evidence_dir = PROJECT_ROOT / "evidence" / "line_segmentation_q5"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(image_path).convert("RGB")
    engine = OttomanOCREngine(enable_easyocr=True, enable_trocr=False, enable_tesseract=True, gpu=True)
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    result = await engine.extract(np.array(image))
    elapsed_ms = (time.perf_counter() - started) * 1000
    gpu_memory_mb = torch.cuda.max_memory_allocated() / (1024 * 1024) if torch.cuda.is_available() else 0
    payload = {
        "status": "PASS" if result.lines else "FAIL_EMPTY_OUTPUT",
        "image_path": str(image_path),
        "line_count": len(result.lines),
        "engine": result.engine_name,
        "engine_version": result.engine_version,
        "device": result.device,
        "page_confidence": result.page_confidence,
        "elapsed_ms": elapsed_ms,
        "gpu_available": torch.cuda.is_available(),
        "gpu_memory_mb": gpu_memory_mb,
        "model_metadata": result.model_metadata,
        "first_lines": [line.text for line in result.lines[:5]],
    }
    (evidence_dir / "production_ocr_smoke.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

