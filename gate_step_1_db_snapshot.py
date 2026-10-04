import sqlite3
import hashlib
import os
import json

db_path = "backend/ottoman_assistant.db"

def get_db_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_legacy_dataset_hash(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Pages
    # Pages
    cur.execute("SELECT id, image_path, image_width, image_height FROM ground_truth_pages WHERE dataset_id=2 ORDER BY id")
    pages = [dict(r) for r in cur.fetchall()]
    # Lines
    cur.execute("SELECT id, page_id, text_content, bounding_box, baseline, reading_order, human_verified, status FROM ground_truth_lines WHERE page_id IN (SELECT id FROM ground_truth_pages WHERE dataset_id=2) ORDER BY id")
    lines = [dict(r) for r in cur.fetchall()]
    
    canonical = {"pages": pages, "lines": lines}
    canonical_str = json.dumps(canonical, sort_keys=True)
    conn.close()
    return hashlib.sha256(canonical_str.encode()).hexdigest(), len(pages), len(lines)

if not os.path.exists(db_path):
    print(f"Error: {db_path} does not exist.")
    exit(1)

sha256 = get_db_hash(db_path)
size = os.path.getsize(db_path)
mtime = os.path.getmtime(db_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("PRAGMA integrity_check;")
integrity = cur.fetchone()[0]

cur.execute("PRAGMA foreign_key_check;")
fk_check = cur.fetchall()

cur.execute("SELECT split_name, COUNT(*) FROM annotation_lines GROUP BY split_name;")
splits = cur.fetchall()
split_data = {
    "total_lines": sum(r[1] for r in splits),
    "null_split_count": next((r[1] for r in splits if r[0] is None), 0),
    "train_count": next((r[1] for r in splits if r[0] == "TRAIN"), 0),
    "internal_validation_count": next((r[1] for r in splits if r[0] == "INTERNAL_VALIDATION"), 0),
    "development_test_count": next((r[1] for r in splits if r[0] == "DEVELOPMENT_TEST"), 0),
    "final_holdout_count": next((r[1] for r in splits if r[0] == "FINAL_HOLDOUT_TEST"), 0)
}
other = split_data["total_lines"] - sum([split_data["null_split_count"], split_data["train_count"], split_data["internal_validation_count"], split_data["development_test_count"], split_data["final_holdout_count"]])
split_data["other_split_count"] = other

legacy_hash, legacy_pages, legacy_lines = get_legacy_dataset_hash(db_path)
conn.close()

db_snapshot = {
    "sha256": sha256,
    "size": size,
    "mtime": mtime,
    "integrity_check": integrity,
    "foreign_key_check": fk_check
}

legacy_data = {
    "hash": legacy_hash,
    "pages": legacy_pages,
    "lines": legacy_lines
}

with open("evidence/annotation_export_final_gate/production_db_before.json", "w") as f:
    json.dump(db_snapshot, f, indent=2)

with open("evidence/annotation_export_final_gate/production_split_state.json", "w") as f:
    json.dump(split_data, f, indent=2)

with open("evidence/annotation_export_final_gate/legacy_before_hash.json", "w") as f:
    json.dump(legacy_data, f, indent=2)

print("DB Snapshot before tests saved successfully.")
