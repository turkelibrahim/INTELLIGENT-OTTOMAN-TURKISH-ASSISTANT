import os
import json
import hashlib
from typing import Any, Dict, Optional
from app.core.config import settings

CACHE_DIR = os.path.join(settings.UPLOAD_DIR, ".ai_cache")

class PersistentCache:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        if self.enabled:
            os.makedirs(CACHE_DIR, exist_ok=True)

    def _generate_key(
        self,
        image_region_hash: str,
        ocr_text: str,
        task_type: str,
        prompt_version: str,
        model_name: str
    ) -> str:
        raw = f"{image_region_hash}|{ocr_text}|{task_type}|{prompt_version}|{model_name}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, *args, **kwargs) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        
        key = self._generate_key(*args, **kwargs)
        file_path = os.path.join(CACHE_DIR, f"{key}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def set(self, result: Dict[str, Any], *args, **kwargs):
        if not self.enabled:
            return
        
        key = self._generate_key(*args, **kwargs)
        file_path = os.path.join(CACHE_DIR, f"{key}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False)
        except Exception:
            pass

cache_store = PersistentCache(enabled=settings.NVIDIA_CACHE_ENABLED)
