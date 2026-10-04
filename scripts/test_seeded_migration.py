import os
import sys
import uuid
import datetime

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from alembic.config import Config
from alembic import command
import app.models

def run_seeded_migration_test():
    # Setup temporary database
    db_path = os.path.abspath("test_seeded_migration.db")
    db_url = f"sqlite:///{db_path}"
    
    # Clean up previous runs
    if os.path.exists(db_path):
        os.remove(db_path)

    # 1. First, create the database and apply migrations up to just BEFORE the ground truth migration.
    # The ground truth migration is "43496331c0dd", we want the one before it: "77edebbaa993"
    alembic_ini_path = "alembic.ini" if os.path.exists("alembic.ini") else "backend/alembic.ini"
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    
    print("Downgrading to before Ground Truth migration (77edebbaa993)...")
    # Actually since it's a new DB, we need to upgrade to 77edebbaa993
    command.upgrade(alembic_cfg, "77edebbaa993")
    
    # 2. Seed some data
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        from app.models.user import User
        from app.models.document import Document
        from app.models.processing_job import ProcessingJob
        
        user = User(email="testseed@example.com", username="testseed", password_hash="hash", status="active")
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id
        
        doc = Document(
            user_id=user_id,
            title="Test Doc",
            original_filename="test.jpg",
            file_hash="hash",
            file_size=123,
            mime_type="image/jpeg",
            status="uploaded"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        doc_id = doc.id
        
        job = ProcessingJob(document_id=doc_id, user_id=user_id, status="pending", job_type="ocr")
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id
        
        print(f"Seeded User ID: {user_id}, Document ID: {doc_id}, Job ID: {job_id}")
        
    finally:
        db.close()
        
    # 3. Apply the Ground Truth migration (upgrade head)
    print("Upgrading to head (applying ground truth migration)...")
    command.upgrade(alembic_cfg, "head")
    
    # 4. Verify old data exists and new tables exist
    db = SessionLocal()
    try:
        from app.models.user import User
        from app.models.ground_truth import Dataset
        
        user = db.query(User).filter_by(email="testseed@example.com").first()
        assert user is not None, "User data lost!"
        
        # Test new ground truth table
        ds = Dataset(name="TestDS", owner_id=user.id)
        db.add(ds)
        db.commit()
        db.refresh(ds)
        
        ds_id = ds.id
        print(f"Created Dataset ID: {ds_id} to verify table exists.")
        
    finally:
        db.close()
        
    # 5. Downgrade -1 (remove ground truth migration)
    print("Downgrading -1...")
    command.downgrade(alembic_cfg, "-1")
    
    # 6. Verify old data STILL exists
    db = SessionLocal()
    try:
        from app.models.user import User
        user = db.query(User).filter_by(email="testseed@example.com").first()
        assert user is not None, "User data lost after downgrade!"
        print("User data verified after downgrade.")
    finally:
        db.close()
        
    # 7. Upgrade head again
    print("Upgrading to head again...")
    command.upgrade(alembic_cfg, "head")
    print("Seeded migration roundtrip successful.")
    
if __name__ == "__main__":
    run_seeded_migration_test()
