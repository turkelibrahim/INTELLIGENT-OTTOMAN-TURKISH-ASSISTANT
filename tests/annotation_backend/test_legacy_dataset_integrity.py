
import sys
import sqlite3
import pytest

# We mock legacy db tables to test if migration harms them
sys.path.append(r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT")
from backend.migrations.annotation import schema_mig

def test_legacy_data_preservation(tmp_path):
    db = tmp_path / "leg1.db"
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    # Create legacy table mock
    cur.execute("CREATE TABLE ground_truth_lines (id INTEGER, page_id INTEGER, text TEXT, bbox TEXT)")
    cur.execute("INSERT INTO ground_truth_lines VALUES (1, 1, 'merhaba', '[0,0,10,10]')")
    conn.commit()
    
    schema_mig.upgrade(conn) # run migration
    
    cur.execute("SELECT count(*) FROM ground_truth_lines")
    assert cur.fetchone()[0] == 1
    cur.execute("SELECT text FROM ground_truth_lines WHERE id=1")
    assert cur.fetchone()[0] == 'merhaba'
    conn.close()

def test_integrity_checks(tmp_path):
    db = tmp_path / "leg2.db"
    conn = sqlite3.connect(db)
    schema_mig.upgrade(conn)
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check;")
    assert cur.fetchone()[0] == "ok"
    cur.execute("PRAGMA foreign_key_check;")
    assert cur.fetchone() is None
    conn.close()
