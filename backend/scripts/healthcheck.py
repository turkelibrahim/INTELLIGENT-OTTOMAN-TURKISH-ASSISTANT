import os
import sys
import requests
import psycopg2
from pathlib import Path
import json

def check_database():
    try:
        from sqlalchemy import create_engine
        engine = create_engine("sqlite:///./ottoman_assistant.db")
        with engine.connect() as conn:
            pass
        return True, "SQLite database is accessible."
    except Exception as e:
        return False, f"Database connection failed: {e}"

def check_qdrant():
    try:
        res = requests.get("http://localhost:6333/collections")
        if res.status_code == 200:
            return True, "Qdrant is running."
    except Exception:
        pass
    
    # Try local Qdrant directory
    qdrant_path = os.getenv("HISTORICAL_QDRANT_PATH", r"C:\ottoman_ai_data\qdrant")
    if Path(qdrant_path).exists():
        return True, f"Local Qdrant directory found at {qdrant_path}."
        
    return False, "Qdrant is not running and local directory not found."

def check_ollama():
    try:
        res = requests.get("http://localhost:11434/api/tags")
        if res.status_code == 200:
            models = [m["name"] for m in res.json().get("models", [])]
            return True, f"Ollama is running. Models: {', '.join(models)}"
    except Exception as e:
        return False, f"Ollama connection failed: {e}"

def check_gpu():
    import torch
    if torch.cuda.is_available():
        return True, f"CUDA is available. Device: {torch.cuda.get_device_name(0)}"
    elif torch.backends.mps.is_available():
        return True, "MPS (Apple Silicon) is available."
    else:
        return True, "[WARNING] No GPU available, running on CPU (will be slow)."

def main():
    print("=== OTTOMAN AI DEMO HEALTHCHECK ===")
    checks = {
        "Database": check_database,
        "Qdrant": check_qdrant,
        "Ollama": check_ollama,
        "GPU Acceleration": check_gpu,
    }
    
    all_passed = True
    for name, func in checks.items():
        print(f"Checking {name}...")
        passed, msg = func()
        if passed:
            print(f"  [OK] {msg}")
        else:
            print(f"  [FAIL] {msg}")
            all_passed = False
            
    print("\nCheck Models in models/ directory:")
    models_dir = Path(__file__).resolve().parents[1] / "models"
    if models_dir.exists():
        easyocr = models_dir / "easyocr"
        if easyocr.exists():
            print(f"  [OK] EasyOCR models found at {easyocr}")
        else:
            print(f"  [FAIL] EasyOCR models missing.")
    
    if all_passed:
        print("\n=== SYSTEM IS READY FOR DEMO ===")
        sys.exit(0)
    else:
        print("\n=== SYSTEM IS NOT READY ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
