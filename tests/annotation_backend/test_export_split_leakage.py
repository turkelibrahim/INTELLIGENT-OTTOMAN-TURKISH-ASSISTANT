import pytest
import os
from app.services.export_service import ExportService
from fastapi import HTTPException

def test_split_leakage_conflicting_splits_on_same_page(db_conn):
    cur = db_conn.cursor()
    cur.execute("INSERT INTO annotation_datasets (name, status, is_test_data, archived, training_eligible) VALUES (?, ?, ?, ?, ?)", 
                ("Leak DS", "LOCKED", 0, 0, 1))
    ds_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_documents (dataset_id, license_status, source_sha256, license_reference) VALUES (?, ?, ?, ?)",
                (ds_id, "APPROVED", "sha256_mock", "ref"))
    doc_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_pages (document_id, status, human_verified, reading_order_verified, image_path) VALUES (?, ?, ?, ?, ?)",
                (doc_id, "LOCKED", 1, 1, "test.png"))
    page_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_regions (page_id) VALUES (?)", (page_id,))
    reg_id = cur.lastrowid
    
    # Line 1 in TRAIN
    cur.execute("""INSERT INTO annotation_lines 
                (page_id, region_id, status, human_verified, bbox_verified, baseline_verified, reading_order_verified, transcription_verified, duplicate_checked, training_eligible, normalized_transcription, reviewed_by, second_reviewer, split_name) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (page_id, reg_id, "LOCKED", 1, 1, 1, 1, 1, 1, 1, "test1", "u1", "u2", "TRAIN"))
                
    # Line 2 in FINAL_HOLDOUT_TEST on same page!
    cur.execute("""INSERT INTO annotation_lines 
                (page_id, region_id, status, human_verified, bbox_verified, baseline_verified, reading_order_verified, transcription_verified, duplicate_checked, training_eligible, normalized_transcription, reviewed_by, second_reviewer, split_name) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (page_id, reg_id, "LOCKED", 1, 1, 1, 1, 1, 1, 1, "test2", "u1", "u2", "FINAL_HOLDOUT_TEST"))
    
    service = ExportService(db_conn)
    with pytest.raises(HTTPException) as exc:
        service.export_kraken(ds_id, is_test_export=False, user_id="test_usr")
    
    assert exc.value.status_code == 409
    assert "conflicting splits" in exc.value.detail
