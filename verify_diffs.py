import json
import os

with open("evidence/annotation_export_final_gate/production_db_before_repair.json") as f:
    before_db = json.load(f)
with open("evidence/annotation_export_final_gate/production_db_before.json") as f:
    after_db = json.load(f)

db_diff = {
    "sha256_same": before_db["sha256"] == after_db["sha256"],
    "size_same": before_db["size"] == after_db["size"],
    "integrity_check": after_db["integrity_check"],
    "foreign_key_check": after_db["foreign_key_check"]
}
if before_db["sha256"] == after_db["sha256"] and before_db["mtime"] != after_db["mtime"]:
    db_diff["mtime_changed_but_hash_same"] = True
    
with open("evidence/annotation_export_final_gate/production_db_diff.json", "w") as f:
    json.dump(db_diff, f, indent=2)

with open("evidence/annotation_export_final_gate/legacy_before_hash_repair.json") as f:
    before_legacy = json.load(f)
with open("evidence/annotation_export_final_gate/legacy_before_hash.json") as f:
    after_legacy = json.load(f)
    
legacy_diff = []
if before_legacy["hash"] != after_legacy["hash"]:
    legacy_diff.append(f"Hash mismatch: {before_legacy['hash']} != {after_legacy['hash']}")
    
with open("evidence/annotation_export_final_gate/legacy_diff.json", "w") as f:
    json.dump(legacy_diff, f, indent=2)

# Also rename the files to match the 'after' names properly
os.rename("evidence/annotation_export_final_gate/production_db_before.json", "evidence/annotation_export_final_gate/production_db_after.json")
os.rename("evidence/annotation_export_final_gate/legacy_before_hash.json", "evidence/annotation_export_final_gate/legacy_after_hash.json")

print("Diffs created successfully.")
