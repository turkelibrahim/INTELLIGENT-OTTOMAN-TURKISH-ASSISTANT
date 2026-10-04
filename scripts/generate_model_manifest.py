import json
import hashlib
from pathlib import Path
from huggingface_hub import snapshot_download

def calculate_file_hash(filepath: Path) -> str:
    if not filepath.exists():
        return ""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    repo_id = "sentence-transformers/all-MiniLM-L6-v2"
    revision = "e4ce9877abf3edfe10b0d82785e83bdcb973e22e" # A known commit hash for this model
    
    print(f"Downloading/Locating model {repo_id} at {revision}...")
    snapshot_path = snapshot_download(
        repo_id=repo_id,
        revision=revision
    )
    
    files_hashes = {}
    snapshot_dir = Path(snapshot_path)
    for filepath in snapshot_dir.rglob("*"):
        if filepath.is_file():
            rel_path = filepath.relative_to(snapshot_dir).as_posix()
            files_hashes[rel_path] = calculate_file_hash(filepath)
            
    manifest = {
        "schema_version": "1.0",
        "model_id": repo_id,
        "revision": revision,
        "license": "Apache-2.0",
        "embedding_dimension": 384,
        "trust_remote_code": False,
        "files": files_hashes
    }
    
    manifest_path = Path("backend/app/services/chat/model_manifest.json")
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"Manifest written to {manifest_path}")

if __name__ == "__main__":
    main()
