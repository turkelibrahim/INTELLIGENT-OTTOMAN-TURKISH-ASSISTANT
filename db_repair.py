import sqlite3
import json
import shutil
import os

db_path = "backend/ottoman_assistant.db"
backup_path = "backend/ottoman_assistant.db.bak"

shutil.copy2(db_path, backup_path)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get legacy stats
cur.execute("SELECT split_name, COUNT(*) as count FROM annotation_lines GROUP BY split_name")
split_counts = {row["split_name"]: row["count"] for row in cur.fetchall()}

cur.execute("SELECT id, status, split_name FROM annotation_lines WHERE id = 1")
row_1 = cur.fetchone()

# Check contamination
contamination = split_counts.get("TRAIN", 0) > 0 or split_counts.get("FINAL_HOLDOUT_TEST", 0) > 0

forensic_data = {
    "split_counts": split_counts,
    "id_1_info": dict(row_1) if row_1 else None,
    "production_split_contamination": contamination
}

with open("evidence/annotation_export_api_repair/production_split_forensic.json", "w") as f:
    json.dump(forensic_data, f, indent=2)

# Repair split_name
if contamination:
    cur.execute("UPDATE annotation_lines SET split_name = NULL")
    conn.commit()

# Integrity checks
cur.execute("PRAGMA integrity_check")
integrity = cur.fetchone()[0]
cur.execute("PRAGMA foreign_key_check")
fk_check = cur.fetchall()

repair_manifest = {
    "repaired": contamination,
    "integrity_check": integrity,
    "foreign_key_check_passed": len(fk_check) == 0
}

with open("evidence/annotation_export_api_repair/split_repair_manifest.json", "w") as f:
    json.dump(repair_manifest, f, indent=2)

conn.close()
