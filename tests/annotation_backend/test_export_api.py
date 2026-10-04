import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_api_export_pagexml_unauthorized():
    client = TestClient(app)
    # No auth token
    response = client.post("/api/v1/annotation/datasets/1/exports/pagexml")
    assert response.status_code == 401

def test_api_export_pagexml_authorized(client, db_conn):
    cur = db_conn.cursor()
    # Create valid dataset
    cur.execute("INSERT INTO annotation_datasets (name, status, is_test_data, archived, training_eligible) VALUES (?, ?, ?, ?, ?)", 
                ("API DS", "LOCKED", 0, 0, 1))
    ds_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_documents (dataset_id, license_status, source_sha256, license_reference) VALUES (?, ?, ?, ?)",
                (ds_id, "APPROVED", "sha256_mock", "ref"))
    doc_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_pages (document_id, status, human_verified, reading_order_verified, image_path) VALUES (?, ?, ?, ?, ?)",
                (doc_id, "LOCKED", 1, 1, "test.png"))
    page_id = cur.lastrowid
    
    cur.execute("INSERT INTO annotation_regions (page_id) VALUES (?)", (page_id,))
    reg_id = cur.lastrowid
    
    cur.execute("""INSERT INTO annotation_lines 
                (page_id, region_id, status, human_verified, bbox_verified, baseline_verified, reading_order_verified, transcription_verified, duplicate_checked, training_eligible, normalized_transcription, reviewed_by, second_reviewer, bbox_json) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (page_id, reg_id, "LOCKED", 1, 1, 1, 1, 1, 1, 1, "test", "u1", "u2", '{"x":0, "y":0, "width":10, "height":10}'))
    
    # Needs to be a POST request to /api/v1/annotation/datasets/{dataset_id}/exports/pagexml
    response = client.post(f"/api/v1/annotation/datasets/{ds_id}/exports/pagexml")
    assert response.status_code == 201
    data = response.json()
    assert data["dataset_name"] == "API DS"
    assert data["line_count"] == 1
    
    # Check if audit event is written
    cur.execute("SELECT action, entity_type, entity_id, success FROM annotation_audit_events ORDER BY id DESC LIMIT 1")
    audit = cur.fetchone()
    assert audit[0] == "export.pagexml"
    assert audit[1] == "dataset"
    assert str(audit[2]) == str(ds_id)
    
def test_api_list_exports(client, db_conn):
    cur = db_conn.cursor()
    cur.execute("INSERT INTO annotation_datasets (name, status, is_test_data, archived, training_eligible) VALUES (?, ?, ?, ?, ?)", 
                ("API DS 2", "LOCKED", 0, 0, 1))
    ds_id = cur.lastrowid
    
    cur.execute("""INSERT INTO annotation_exports (dataset_id, export_type, status, output_path, output_sha256, is_test_export, created_by, created_at, completed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ds_id, "PAGEXML", "COMPLETED", "test_path", "sha", 0, "u1", "2023", "2023"))
                
    response = client.get(f"/api/v1/annotation/datasets/{ds_id}/exports")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["export_type"] == "PAGEXML"
