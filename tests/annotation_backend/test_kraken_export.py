import pytest
import os
from app.services.export_service import ExportService

def test_kraken_manifests(db_conn):
    cur = db_conn.cursor()
    cur.execute("INSERT INTO annotation_datasets (name, status, is_test_data, archived, training_eligible) VALUES (?, ?, ?, ?, ?)", 
                ("Kraken DS", "LOCKED", 0, 0, 1))
    ds_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_documents (dataset_id, license_status, source_sha256, license_reference) VALUES (?, ?, ?, ?)",
                (ds_id, "APPROVED", "sha256_mock", "ref"))
    doc_id = cur.lastrowid
    
    # Page 1 (TRAIN)
    cur.execute("INSERT INTO annotation_pages (document_id, status, human_verified, reading_order_verified, image_path) VALUES (?, ?, ?, ?, ?)",
                (doc_id, "LOCKED", 1, 1, "test.png"))
    p1 = cur.lastrowid
    cur.execute("INSERT INTO annotation_regions (page_id) VALUES (?)", (p1,))
    r1 = cur.lastrowid
    cur.execute("""INSERT INTO annotation_lines 
                (page_id, region_id, status, human_verified, bbox_verified, baseline_verified, reading_order_verified, transcription_verified, duplicate_checked, training_eligible, normalized_transcription, reviewed_by, second_reviewer, split_name) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (p1, r1, "LOCKED", 1, 1, 1, 1, 1, 1, 1, "test1", "u1", "u2", "TRAIN"))
                
    # Page 2 (FINAL_HOLDOUT_TEST)
    cur.execute("INSERT INTO annotation_pages (document_id, status, human_verified, reading_order_verified, image_path) VALUES (?, ?, ?, ?, ?)",
                (doc_id, "LOCKED", 1, 1, "test.png"))
    p2 = cur.lastrowid
    cur.execute("INSERT INTO annotation_regions (page_id) VALUES (?)", (p2,))
    r2 = cur.lastrowid
    cur.execute("""INSERT INTO annotation_lines 
                (page_id, region_id, status, human_verified, bbox_verified, baseline_verified, reading_order_verified, transcription_verified, duplicate_checked, training_eligible, normalized_transcription, reviewed_by, second_reviewer, split_name) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (p2, r2, "LOCKED", 1, 1, 1, 1, 1, 1, 1, "test2", "u1", "u2", "FINAL_HOLDOUT_TEST"))
    
    service = ExportService(db_conn)
    res = service.export_kraken(ds_id, is_test_export=False, user_id="test_usr")
    
    assert res["split_counts"]["TRAIN"] == 1
    assert res["split_counts"]["FINAL_HOLDOUT_TEST"] == 1
    
    export_id = res["export_id"]
    ds_name = res["dataset_name"]
    
    train_manifest = f"exports/annotation/{ds_name}/{export_id}/manifests/train.txt"
    holdout_manifest = f"exports/annotation/{ds_name}/{export_id}/manifests/final_holdout_test.txt"
    
    assert os.path.exists(train_manifest)
    assert os.path.exists(holdout_manifest)
    
    with open(train_manifest, "r") as f:
        train_lines = f.read().splitlines()
    assert len(train_lines) == 1
    assert f"page_{p1}.xml" in train_lines[0]
    
    with open(holdout_manifest, "r") as f:
        hold_lines = f.read().splitlines()
    assert len(hold_lines) == 1
    assert f"page_{p2}.xml" in hold_lines[0]
