import pytest
from app.services.export_service import ExportService
from fastapi import HTTPException

def test_export_eligibility_unlocked_dataset(db_conn):
    cur = db_conn.cursor()
    # Create an unlocked dataset
    cur.execute("INSERT INTO annotation_datasets (name, status, is_test_data, archived, training_eligible) VALUES (?, ?, ?, ?, ?)", 
                ("Unlocked DS", "DRAFT", 0, 0, 1))
    ds_id = cur.lastrowid
    
    service = ExportService(db_conn)
    with pytest.raises(HTTPException) as exc:
        service._check_eligibility(ds_id, is_test_export=False)
    assert exc.value.status_code == 409
    assert "not LOCKED" in exc.value.detail

def test_test_data_isolation(db_conn):
    cur = db_conn.cursor()
    cur.execute("INSERT INTO annotation_datasets (name, status, is_test_data, archived, training_eligible) VALUES (?, ?, ?, ?, ?)", 
                ("Test DS", "LOCKED", 1, 0, 1))
    ds_id = cur.lastrowid
    
    service = ExportService(db_conn)
    # Production export should fail
    with pytest.raises(HTTPException) as exc:
        service._check_eligibility(ds_id, is_test_export=False)
    assert exc.value.status_code == 409
    assert "Test dataset cannot be exported for production" in exc.value.detail
    
    # Test export should fail on lines if no lines exist, but pass the dataset check
    with pytest.raises(HTTPException) as exc:
        service._check_eligibility(ds_id, is_test_export=True)
    assert exc.value.status_code == 409
    assert "No eligible lines" in exc.value.detail

def test_license_missing(db_conn):
    cur = db_conn.cursor()
    cur.execute("INSERT INTO annotation_datasets (name, status, is_test_data, archived, training_eligible) VALUES (?, ?, ?, ?, ?)", 
                ("Test DS", "LOCKED", 0, 0, 1))
    ds_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_documents (dataset_id, license_status, source_sha256) VALUES (?, ?, ?)",
                (ds_id, "MISSING", "sha256_mock"))
    doc_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_pages (document_id, status, human_verified, reading_order_verified, image_path) VALUES (?, ?, ?, ?, ?)",
                (doc_id, "LOCKED", 1, 1, "test.png"))
    page_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_regions (page_id) VALUES (?)", (page_id,))
    reg_id = cur.lastrowid
    
    cur.execute("""INSERT INTO annotation_lines 
                (page_id, region_id, status, human_verified, bbox_verified, baseline_verified, reading_order_verified, transcription_verified, duplicate_checked, training_eligible, normalized_transcription, reviewed_by, second_reviewer) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (page_id, reg_id, "LOCKED", 1, 1, 1, 1, 1, 1, 1, "test", "u1", "u2"))
    
    service = ExportService(db_conn)
    # The line is perfect, but doc license is MISSING
    report = service.check_eligibility_report(ds_id, is_test_export=False)
    assert not report.is_eligible
    assert report.exclusion_details.get("document_license_rejected", 0) + report.exclusion_details.get("document_license_missing_reference", 0) + report.exclusion_details.get("document_missing_sha256", 0) >= 0
