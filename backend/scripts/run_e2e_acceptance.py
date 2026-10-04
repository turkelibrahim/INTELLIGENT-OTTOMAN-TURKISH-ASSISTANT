import asyncio
import json
import os
import sys
import time
import os
from pathlib import Path

os.environ["OCR_ENGINE"] = "kraken"
os.environ["UPLOAD_DIR"] = str(Path("backend/uploads").absolute())
from fastapi.testclient import TestClient

# Adjust path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.core.security import get_password_hash, create_access_token
from worker import process_job
from app.models.document import Document
from app.models.processing_job import ProcessingJob
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from app.db.database import Base, get_db

# Setup Test DB
DB_PATH = Path("e2e_test.db")
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

# Evidence dir
EVIDENCE_DIR = Path("backend/evidence/real_document_e2e")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

def write_evidence(filename, content):
    with open(EVIDENCE_DIR / filename, "w", encoding="utf-8") as f:
        f.write(content)

def get_auth_headers(db: Session):
    user = db.query(User).filter_by(username="e2e_test_user").first()
    if not user:
        user = User(
            email="e2e@example.com",
            username="e2e_test_user",
            password_hash=get_password_hash("password"),
            role="user",
            status="active"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}

async def run_e2e():
    db = TestingSessionLocal()
    client = TestClient(app)
    headers = get_auth_headers(db)
    
    print("1. Health Check")
    health = client.get("/health")
    print("Health:", health.status_code)
    
    # 2. Selected Documents
    png_path = Path(r"C:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT\datasets\Ottoman_OCR_Training_Pack_v1\05_real_sources\review_queue\real08_selcuk_page.png")
    pdf_path = Path("backend/evidence/real_document_e2e/test_document.pdf").absolute()
    
    # Create PDF from PNG
    from PIL import Image
    with Image.open(png_path) as img:
        img.convert("RGB").save(pdf_path, "PDF", resolution=100.0)
    
    # 3. Test PNG E2E
    print(f"\nTesting PNG: {png_path}")
    t0 = time.time()
    with open(png_path, "rb") as f:
        resp = client.post("/api/v1/documents", headers=headers, data={"title": "E2E PNG"}, files={"file": ("test.png", f, "image/png")})
    
    if resp.status_code != 201:
        print("Upload Failed:", resp.json())
        sys.exit(1)
        
    doc_id = resp.json()["id"]
    print("Upload successful, Document ID:", doc_id)
    
    # Trigger OCR job
    resp = client.post(f"/api/v1/documents/{doc_id}/ocr", headers=headers)
    if resp.status_code != 202:
        print("Trigger OCR Failed:", resp.json())
        sys.exit(1)
        
    # Simulate worker picking up the job
    job = db.query(ProcessingJob).filter_by(document_id=doc_id).first()
    if not job:
        print("No job created!")
        sys.exit(1)
        
    print("Running pipeline (Preprocessing -> Layout -> Kraken OCR -> Persistence)...")
    t1 = time.time()
    await process_job(db, job, "e2e_worker")
    t2 = time.time()
    
    db.expire_all()
    job = db.query(ProcessingJob).filter_by(document_id=doc_id).first()
    print("Job status:", job.status)
    
    # Fetch result via API
    resp = client.get(f"/api/v1/documents/{doc_id}/ocr/status", headers=headers)
    ocr_results = resp.json()
    
    write_evidence("image_e2e_result.json", json.dumps(ocr_results, indent=2))
    
    if not ocr_results.get("result"):
        print("FAIL: No OCR results returned from API.")
        sys.exit(1)
        
    first_page_ocr = ocr_results["result"]
    meta = json.loads(job.result_summary).get("model_info", {})
    
    print("PNG Metadata:", meta)
    
    # Test PDF E2E
    print(f"\nTesting PDF: {pdf_path}")
    with open(pdf_path, "rb") as f:
        resp = client.post("/api/v1/documents", headers=headers, data={"title": "E2E PDF"}, files={"file": ("test.pdf", f, "application/pdf")})
    
    pdf_doc_id = resp.json()["id"]
    print("Upload successful, Document ID:", pdf_doc_id)
    
    # Trigger OCR for PDF
    client.post(f"/api/v1/documents/{pdf_doc_id}/ocr", headers=headers)
    
    pdf_job = db.query(ProcessingJob).filter_by(document_id=pdf_doc_id).first()
    t3 = time.time()
    await process_job(db, pdf_job, "e2e_worker")
    t4 = time.time()
    
    resp = client.get(f"/api/v1/documents/{pdf_doc_id}/ocr/status", headers=headers)
    pdf_ocr_results = resp.json()
    write_evidence("pdf_e2e_result.json", json.dumps(pdf_ocr_results, indent=2))
    
    # Save timings
    timings = {
        "png_total": t2 - t0,
        "png_ocr": t2 - t1,
        "pdf_total": t4 - t3,
        "pdf_ocr": t4 - t3
    }
    write_evidence("timings.json", json.dumps(timings, indent=2))
    write_evidence("kraken_runtime_metadata.json", json.dumps(meta, indent=2))
    
    # The API returns mapped payload
    sample_text = first_page_ocr.get("pipeline_results", {}).get("original_ocr_text", "")
    write_evidence("ocr_sample.txt", sample_text)

    
    print("\n--- RESULTS ---")
    print(f"Primary Engine: {meta.get('primary_engine')}")
    print(f"Actual Engine: {meta.get('actual_engine')}")
    print(f"Fallback Used: {meta.get('fallback_used')}")
    print(f"Sample length: {len(sample_text)}")

if __name__ == "__main__":
    asyncio.run(run_e2e())
