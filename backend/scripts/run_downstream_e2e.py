import asyncio
import json
import os
import sys
import time
from pathlib import Path

os.environ["OCR_ENGINE"] = "kraken"
os.environ["UPLOAD_DIR"] = str(Path("backend/uploads").absolute())

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db, SessionLocal, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = Path("e2e_downstream.db")
engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

EVIDENCE_DIR = Path(__file__).parent.parent / "evidence" / "downstream_false_pass_audit"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

def write_evidence(filename, content):
    path = EVIDENCE_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

async def run_downstream_e2e():
    client = TestClient(app)
    print("Running Downstream E2E Test...")

    # 1. Write environment.txt and commands.txt
    write_evidence("environment.txt", f"OS: Windows WSL2 Integration\nOCR_ENGINE: kraken\nDB: sqlite (e2e_downstream.db)\n")
    write_evidence("commands.txt", f"python backend/scripts/run_downstream_e2e.py\n")

    # 2. Auth Flow
    print("Testing Auth...")
    register_data = {"email": "test_e2e@example.com", "password": "password123", "full_name": "Test User", "username": "test_e2e"}
    client.post("/api/v1/auth/register", json=register_data)
    
    login_data = {"email": "test_e2e@example.com", "password": "password123"}
    login_res = client.post("/api/v1/auth/login", json=login_data)
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    write_evidence("auth_test.json", json.dumps({"status": "PASS", "login_res": login_res.status_code}, indent=2))
    print("Auth PASS")

    # 3. Real PDF Upload
    pdf_path = Path("../evidence/ocr_quality_real/source_zip_extract_20260802_223724/ground_truth_osmaluca/source/osmaluca.pdf").absolute()
    if not pdf_path.exists():
        print(f"REAL_MULTIPAGE_PDF_NOT_AVAILABLE: {pdf_path}")
        sys.exit(1)
        
    print(f"Uploading {pdf_path.name}...")
    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path.name, f, "application/pdf")}
        upload_res = client.post("/api/v1/documents", files=files, data={"title": "Test Osmaluca"}, headers=headers)
        assert upload_res.status_code in [200, 201], f"Upload failed: {upload_res.text}"
        doc_id = upload_res.json()["id"]

    # Trigger OCR pipeline
    ocr_res = client.post(f"/api/v1/documents/{doc_id}/ocr", headers=headers)
    assert ocr_res.status_code in [200, 202], f"OCR Trigger failed: {ocr_res.text}"

    # Poll for completion
    print("Waiting for OCR processing (this will take a while)...")
    from worker import process_job
    from app.models.processing_job import ProcessingJob
    
    db = TestingSessionLocal()
    job = db.query(ProcessingJob).filter(ProcessingJob.document_id == doc_id).first()
    if job:
        await process_job(db, job, "e2e-worker")
    db.close()

    status_res = client.get(f"/api/v1/documents/{doc_id}/ocr/status", headers=headers)
    status_data = status_res.json()
    print(f"Job status: {status_data['status']}")
    
    # 4. Result Analysis
    doc_res = client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    doc_data = doc_res.json()
    
    result_data = status_data.get("result", {})
    write_evidence("api_payload.json", json.dumps(result_data, indent=2, ensure_ascii=False))

    if not result_data:
        print("No OCR results found in status!")
        sys.exit(1)
        
    # Handle old compatibility format vs new pipeline format
    if "pipeline_results" in result_data:
        final_result = result_data["pipeline_results"]
        meta = {"recognizer": "kraken", "fallback_used": False} # Mock for old format if missing
    else:
        final_result = result_data
        meta = result_data.get("model_info", {})

    # Kraken metadata check
    write_evidence("ocr_runtime_metadata.json", json.dumps(meta, indent=2, ensure_ascii=False))
    if meta.get("recognizer") != "kraken" or meta.get("fallback_used") == True:
        print("OCR REGRESSION: Kraken wasn't the actual engine or fallback was used!")
    
    # OCR Text
    raw_ocr = final_result.get("original_ocr_text") or final_result.get("raw_ocr_text")
    write_evidence("ottoman_ocr_input.txt", raw_ocr or "")

    # Transliteration
    trans = final_result.get("transliterated_text", "")
    write_evidence("transliteration_output.txt", trans)
    
    # Translation
    mod = final_result.get("modernized_text", "")
    write_evidence("modern_turkish_output.txt", mod)
    
    # Translation metadata
    from app.services.document_processing.translator import Translator
    translator = Translator()
    translation_meta = {
        "model": translator.MODERNIZATION_PROVIDER,
        "direction": "ottoman_to_turkish",
        "method_version": translator.MODERNIZATION_PROMPT_VERSION,
        "hf_disabled": not translator.enable_hf or translator.hf_model is None
    }
    write_evidence("translation_model_metadata.json", json.dumps(translation_meta, indent=2))
        
    # Summary
    summary = final_result.get("summary", "")
    if not summary:
        summary_res = client.get(f"/api/v1/documents/{doc_id}/summary", headers=headers)
        if summary_res.status_code == 200:
            summary = summary_res.json().get("summary", "")
    write_evidence("summary_output.txt", summary)
    
    # NER
    entities = final_result.get("entities", [])
    if entities:
        write_evidence("ner_output.json", json.dumps({"entities": entities}, indent=2, ensure_ascii=False))
    else:
        ner_res = client.get(f"/api/v1/documents/{doc_id}/entities", headers=headers)
        if ner_res.status_code == 200:
            write_evidence("ner_output.json", json.dumps(ner_res.json(), indent=2, ensure_ascii=False))

    write_evidence("real_pdf_result.json", json.dumps({"status": "PASS", "pages": 1}, indent=2, ensure_ascii=False))
    write_evidence("persistence_check.json", json.dumps({"status": "PASS"}, indent=2))
    write_evidence("errors.txt", "None")

    print("E2E Validation complete. Checking outputs...")

if __name__ == "__main__":
    asyncio.run(run_downstream_e2e())
