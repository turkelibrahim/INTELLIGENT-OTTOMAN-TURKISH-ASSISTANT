import os
import shutil
import hashlib
import json
import sys

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(root_dir, "backend", "models", "easyocr")
    os.makedirs(target_dir, exist_ok=True)
    
    source_dir = os.path.join(os.path.expanduser("~"), ".EasyOCR", "model")
    models = ["arabic.pth", "craft_mlt_25k.pth"]
    
    manifest_path = os.path.join(root_dir, "backend", "model_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {}

    for model_name in models:
        src = os.path.join(source_dir, model_name)
        dst = os.path.join(target_dir, model_name)
        
        if not os.path.exists(src):
            print(f"ERROR: Source model {src} not found. Run easyocr once to download it first.")
            sys.exit(1)
            
        print(f"Copying {src} to {dst}...")
        shutil.copy2(src, dst)
        
        print(f"Calculating SHA-256 for {dst}...")
        file_hash = calculate_sha256(dst)
        file_size = os.path.getsize(dst)
        
        # Add to manifest
        manifest[f"easyocr/{model_name}"] = {
            "source": "https://github.com/JaidedAI/EasyOCR",
            "license": "Apache-2.0",
            "sha256": file_hash,
            "size_bytes": file_size,
            "description": f"EasyOCR {'detection' if 'craft' in model_name else 'recognition (arabic)'} model"
        }
        
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully installed and registered EasyOCR models in {target_dir}")
    print(f"Manifest updated: {manifest_path}")

if __name__ == "__main__":
    main()
