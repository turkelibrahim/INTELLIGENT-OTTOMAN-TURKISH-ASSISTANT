import sys
import json
import subprocess
from pathlib import Path

root = Path(r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT")
ev_dir = root / "evidence/annotation_fastapi_core_repair"
ev_dir.mkdir(parents=True, exist_ok=True)

res = subprocess.run('python -c "import sys, json; sys.path.insert(0, \'backend\'); from app.main import app; print(json.dumps([r[\'path\'] for r in app.routes if hasattr(r, \'path\') and \'annotation\' in r.path]))"', 
                     shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(root))

with open(ev_dir / "real_app_import_command.txt", "w") as f: f.write(res.args)
with open(ev_dir / "real_app_import_stdout.txt", "w") as f: f.write(res.stdout)
with open(ev_dir / "real_app_import_stderr.txt", "w") as f: f.write(res.stderr)
with open(ev_dir / "real_app_import_exit_code.txt", "w") as f: f.write(str(res.returncode))

try:
    routes = json.loads(res.stdout)
except:
    routes = []
with open(ev_dir / "real_openapi_annotation_routes.json", "w") as f: json.dump({"routes": routes}, f)

print("Phase 2 test completed with exit code", res.returncode)
