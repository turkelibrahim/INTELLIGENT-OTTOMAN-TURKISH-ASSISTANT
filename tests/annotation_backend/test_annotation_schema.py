
import sys
import sqlite3
import pytest

sys.path.append(r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT")
from backend.migrations.annotation import schema_mig

def setup_db(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    schema_mig.upgrade(conn)
    return conn

def test_tables_created(tmp_path):
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    assert "annotation_datasets" in tables
    assert "annotation_documents" in tables
    assert "annotation_pages" in tables
    assert "annotation_regions" in tables
    assert "annotation_lines" in tables
    assert "annotation_reviews" in tables
    assert "annotation_audit_events" in tables
    assert "annotation_exports" in tables
    assert "annotation_schema_version" in tables
    conn.close()

def test_mandatory_columns(tmp_path):
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(annotation_lines)")
    cols = [r[1] for r in cur.fetchall()]
    assert "id" in cols
    assert "bbox_json" in cols
    assert "transcription" in cols
    conn.close()

def test_foreign_keys(tmp_path):
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_key_list(annotation_pages)")
    fk = cur.fetchall()
    assert len(fk) > 0
    assert fk[0][2] == "annotation_documents"
    conn.close()

def test_indices(tmp_path):
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute("PRAGMA index_list(annotation_lines)")
    indices = [r[1] for r in cur.fetchall()]
    assert any("idx_page_line_order" in i for i in indices)
    conn.close()

def test_status_constraint(tmp_path):
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO annotation_datasets (status) VALUES ('INVALID_STATUS')")
    conn.close()

def test_region_type_constraint(tmp_path):
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO annotation_datasets (id, status) VALUES (1, 'DRAFT')")
    cur.execute("INSERT INTO annotation_documents (id, dataset_id, license_status) VALUES (1, 1, 'UNKNOWN')")
    cur.execute("INSERT INTO annotation_pages (id, document_id) VALUES (1, 1)")
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO annotation_regions (page_id, region_type) VALUES (1, 'INVALID_REGION')")
    conn.close()

def test_license_constraint(tmp_path):
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO annotation_datasets (id, status) VALUES (1, 'DRAFT')")
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO annotation_documents (dataset_id, license_status) VALUES (1, 'INVALID_LICENSE')")
    conn.close()

def test_duplicate_document_sha(tmp_path):
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO annotation_datasets (id, status) VALUES (1, 'DRAFT')")
    cur.execute("INSERT INTO annotation_documents (dataset_id, source_sha256, license_status) VALUES (1, 'sha1', 'UNKNOWN')")
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO annotation_documents (dataset_id, source_sha256, license_status) VALUES (1, 'sha1', 'UNKNOWN')")
    conn.close()

def test_duplicate_page_line_order(tmp_path):
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO annotation_datasets (id, status) VALUES (1, 'DRAFT')")
    cur.execute("INSERT INTO annotation_documents (id, dataset_id, license_status) VALUES (1, 1, 'UNKNOWN')")
    cur.execute("INSERT INTO annotation_pages (id, document_id) VALUES (1, 1)")
    cur.execute("INSERT INTO annotation_regions (id, page_id, region_type) VALUES (1, 1, 'TEXT')")
    cur.execute("INSERT INTO annotation_lines (page_id, region_id, line_order) VALUES (1, 1, 1)")
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO annotation_lines (page_id, region_id, line_order) VALUES (1, 1, 1)")
    conn.close()

def test_audit_event(tmp_path):
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO annotation_audit_events (entity_type, entity_id, action, actor_id) VALUES ('LINE', 1, 'UPDATE', 'user1')")
    assert cur.rowcount == 1
    conn.close()

def test_review_record(tmp_path):
    conn = setup_db(tmp_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO annotation_reviews (entity_type, entity_id, decision) VALUES ('LINE', 1, 'APPROVE')")
    assert cur.rowcount == 1
    conn.close()
