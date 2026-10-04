import os
import shutil
import hashlib
import json
from pathlib import Path
from datetime import datetime

root = Path(r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT")
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = root / f"backups/pre_annotation_api_{ts}"
backup_dir.mkdir(parents=True, exist_ok=True)
ev_dir = root / "evidence/annotation_fastapi_core"
ev_dir.mkdir(parents=True, exist_ok=True)

manifest = []

def backup_file(src, dst_name):
    if src.exists():
        dst = backup_dir / dst_name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        h = hashlib.sha256()
        with open(dst, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""): h.update(chunk)
        manifest.append({
            "path": str(src.relative_to(root)),
            "size": dst.stat().st_size,
            "sha256": h.hexdigest(),
            "backup_path": str(dst.relative_to(root))
        })

# Backup core files
db_path = root / "backend/ottoman_assistant.db"
backup_file(db_path, "ottoman_assistant.db")

app_dir = root / "backend/app"
if app_dir.exists():
    for py_file in app_dir.rglob("*.py"):
        backup_file(py_file, str(py_file.relative_to(app_dir)))

with open(ev_dir / "backup_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

audit = {
    "app_entrypoint": "backend/app/main.py",
    "router_injection": "app.include_router(api_router) inside main.py",
    "db_dependency": "get_db from app.db.database",
    "auth_dependency": "needs inspection, will mock if not present",
    "api_prefix": "settings.API_V1_PREFIX (usually /api/v1)",
    "health_endpoint": "/health"
}
with open(ev_dir / "existing_fastapi_architecture_audit.json", "w", encoding="utf-8") as f:
    json.dump(audit, f, indent=2)
