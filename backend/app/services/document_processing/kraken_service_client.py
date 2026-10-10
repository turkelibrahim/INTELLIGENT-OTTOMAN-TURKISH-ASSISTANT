import json
import logging
import os
import time
from io import BytesIO
from typing import Any, Dict, List

import numpy as np
import requests
from PIL import Image

logger = logging.getLogger(__name__)


class PersistentKrakenServiceClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: int = 90):
        self.base_url = (base_url or os.getenv("OCR_KRAKEN_SERVICE_URL") or "http://127.0.0.1:8765").rstrip("/")
        self.timeout_seconds = int(os.getenv("OCR_KRAKEN_SERVICE_TIMEOUT", str(timeout_seconds)))

    def ready(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/health/ready", timeout=10)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("model_loaded"):
            raise RuntimeError("Persistent Kraken service is not model-ready")
        return payload

    def extract_batch(self, image: np.ndarray, boxes: List[Any]) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        self.ready()
        start = time.perf_counter()
        if len(image.shape) == 2:
            pil_image = Image.fromarray(image)
        else:
            pil_image = Image.fromarray(image[:, :, ::-1])
        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)
        box_dict = {}
        for box in boxes:
            x, y, w, h = box.bbox
            box_dict[str(box.line_index)] = [int(x), int(y), int(x + w), int(y + h)]
        response = requests.post(
            f"{self.base_url}/ocr",
            files={"image": ("page.png", buffer.getvalue(), "image/png")},
            data={"boxes": json.dumps(box_dict, ensure_ascii=False)},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "success":
            raise RuntimeError(f"Persistent Kraken OCR failed: {payload.get('error_message')}")
        payload.setdefault("timings", {})
        payload["timings"]["network_ms"] = max(0.0, (time.perf_counter() - start) * 1000 - float(
            payload["timings"].get("total_ms") or 0.0
        ))
        return payload.get("lines", []), payload
