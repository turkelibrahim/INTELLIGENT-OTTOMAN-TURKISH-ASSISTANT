import os
import sys
import urllib.request
import json

print("=" * 60)
print("INTELLIGENT OTTOMAN TURKISH ASSISTANT - COMPONENT CHECK")
print("=" * 60)

# 1. Check Python & Paths
print(f"\n[1] Python Executable: {sys.executable}")
print(f"    Current Directory: {os.getcwd()}")

# 2. Check Backend Core & FastAPI
try:
    from app.main import app
    from app.core.config import settings
    print(f"[2] FastAPI App: SUCCESS")
    print(f"    - APP_NAME: {settings.APP_NAME}")
    print(f"    - OCR_ENGINE: {settings.OCR_ENGINE}")
    print(f"    - LLM_PROVIDER: {settings.LLM_PROVIDER}")
    print(f"    - LLM_MODEL: {settings.LLM_MODEL}")
    print(f"    - LLM_BASE_URL: {getattr(settings, 'LLM_BASE_URL', 'http://127.0.0.1:11434')}")
except Exception as e:
    print(f"[2] FastAPI App: FAILED -> {e}")

# 3. Check Database
try:
    from app.db.database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    count = db.execute(text("SELECT count(id) FROM processing_jobs")).scalar()
    print(f"[3] Database Connection: SUCCESS (Jobs Count: {count})")
    db.close()
except Exception as e:
    print(f"[3] Database Connection: FAILED -> {e}")

# 4. Check OCR Engine & EasyOCR
try:
    from app.services.document_processing.ocr_factory import create_ottoman_ocr_engine
    engine = create_ottoman_ocr_engine()
    print(f"[4] OCR Engine Instance: SUCCESS ({type(engine).__name__})")
except Exception as e:
    print(f"[4] OCR Engine Instance: FAILED -> {e}")

# 5. Check Ollama Connectivity
try:
    req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
    with urllib.request.urlopen(req, timeout=3) as response:
        data = json.loads(response.read().decode('utf-8'))
        models = [m.get('name') for m in data.get('models', [])]
        print(f"[5] Ollama LLM Service: ONLINE (Available Models: {models})")
except Exception as e:
    print(f"[5] Ollama LLM Service: OFFLINE / WARNING -> {e}")

print("\n" + "=" * 60)
print("CHECK COMPLETED")
print("=" * 60)
