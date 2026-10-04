import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

import torch

def calculate_file_hash(filepath: Path) -> str:
    if not filepath.exists():
        return ""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    backend_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "backend"
    models_dir = backend_dir / "models" / "easyocr"
    
    if not models_dir.exists():
        print(f"Directory {models_dir} does not exist.")
        return

    files_info = {}
    for filepath in models_dir.glob("*.pth"):
        if filepath.is_file():
            filename = filepath.name
            size_bytes = filepath.stat().st_size
            files_info[filename] = {
                "sha256": calculate_file_hash(filepath),
                "size_bytes": size_bytes,
            }
            
    manifest = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "engine": "EasyOCR",
        "engine_version": "1.7.2",
        "pytorch_version": torch.__version__,
        "source": "https://github.com/JaidedAI/EasyOCR",
        "license": "Apache-2.0",
        "model_type": "CRAFT (Text Detection) + ResNet-CRNN (Arabic Text Recognition)",
        "download_enabled": False,
        "files": files_info
    }
    
    manifest_path = backend_dir / "models" / "easyocr" / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"EasyOCR manifest written to {manifest_path}")

if __name__ == "__main__":
    main()
