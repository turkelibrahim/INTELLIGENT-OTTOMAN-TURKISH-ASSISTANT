import time
import asyncio
import os
from pathlib import Path
from PIL import Image

from app.db.database import get_db, SessionLocal
from app.models.document import Document
from app.models.page import Page
from app.services.document_analysis_pipeline import DocumentAnalysisPipeline
from app.core.config import settings

def create_dummy_image(path: str):
    img = Image.new('RGB', (800, 600), color = 'white')
    img.save(path)

async def run_benchmark():
    db = SessionLocal()
    # Ensure there is a dummy document
    doc = db.query(Document).filter(Document.title == "Benchmark Doc").first()
    if not doc:
        doc = Document(
            user_id=1,
            title="Benchmark Doc",
            original_filename="bench.jpg",
            file_hash="benchhash",
            file_size=1000,
            mime_type="image/jpeg",
            status="uploaded",
            access_level="private",
            page_count=1
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
    page = db.query(Page).filter(Page.document_id == doc.id).first()
    if not page:
        save_dir = Path(settings.UPLOAD_DIR) / "originals" / str(doc.id)
        save_dir.mkdir(parents=True, exist_ok=True)
        img_path = save_dir / "bench.jpg"
        create_dummy_image(str(img_path))
        
        page = Page(
            document_id=doc.id,
            page_no=1,
            original_path=str(img_path),
            width=800,
            height=600,
            status="pending"
        )
        db.add(page)
        db.commit()
        db.refresh(page)

    pipeline = DocumentAnalysisPipeline()
    start_time = time.time()
    
    # Run analysis
    res = await pipeline.analyze_document(document=doc, pages=[page], db=db, user_id=1)
    
    end_time = time.time()
    print(f"Total Wall Time: {end_time - start_time:.2f} seconds")
    
    # Print individual stages if possible
    # We can't easily extract without instrumenting pipeline, but overall time is good.
    db.close()

if __name__ == "__main__":
    asyncio.run(run_benchmark())
