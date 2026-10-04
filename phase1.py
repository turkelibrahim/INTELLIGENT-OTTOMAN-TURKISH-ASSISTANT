import sqlite3
import hashlib
import os
import json
import time

DB_PATH = 'backend/ottoman_assistant.db'

def get_file_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath,"rb") as f:
        for byte_block in iter(lambda: f.read(4096),b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def phase1_production_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    integrity = cursor.execute("PRAGMA integrity_check").fetchone()[0]
    fk_check = cursor.execute("PRAGMA foreign_key_check").fetchall()
    
    conn.close()
    
    stat = os.stat(DB_PATH)
    
    out = {
        "sha256": get_file_sha256(DB_PATH),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "integrity_check": integrity,
        "foreign_key_check": fk_check
    }
    
    os.makedirs('evidence/annotation_export_final_gate', exist_ok=True)
    with open('evidence/annotation_export_final_gate/production_db_before_repair.json', 'w') as f:
        json.dump(out, f, indent=2)

def phase1_legacy_snapshot():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Dataset ID 2 pages
    pages = cursor.execute("SELECT id, external_id, status FROM pages WHERE dataset_id = 2 ORDER BY id").fetchall()
    
    lines_data = []
    for page in pages:
        lines = cursor.execute("SELECT id, text_content, bounding_box, baseline, reading_order, human_verified FROM lines WHERE page_id = ? ORDER BY id", (page[0],)).fetchall()
        for line in lines:
            lines_data.append({
                "line_id": line[0],
                "page_id": page[0],
                "text_content": line[1],
                "bounding_box": line[2],
                "baseline": line[3],
                "reading_order": line[4],
                "human_verified": line[5]
            })
            
    conn.close()
    
    serialized = json.dumps({"pages": len(pages), "lines": lines_data}, sort_keys=True)
    h = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    
    out = {
        "pages": len(pages),
        "lines": len(lines_data),
        "complete_hash": h
    }
    
    with open('evidence/annotation_export_final_gate/legacy_before_hash_repair.json', 'w') as f:
        json.dump(out, f, indent=2)

if __name__ == '__main__':
    phase1_production_db()
    phase1_legacy_snapshot()
    print("Phase 1 complete.")
