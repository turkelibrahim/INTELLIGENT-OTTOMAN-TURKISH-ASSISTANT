import subprocess
import json
import time

start = time.time()
r1 = subprocess.run(["pytest", "tests/annotation_backend/test_export_api.py", "tests/annotation_backend/test_kraken_export.py", "tests/annotation_backend/test_export_eligibility.py", "tests/annotation_backend/test_export_split_leakage.py", "tests/annotation_backend/test_export_security.py", "tests/annotation_backend/test_pagexml_export.py", "-v", "--tb=short", "--disable-warnings"])

r2 = subprocess.run(["pytest", "tests/annotation_backend", "-v", "--tb=short", "--disable-warnings"], capture_output=True, text=True)
duration = time.time() - start

# parse pytest output roughly for summary
passed = r2.stdout.count("PASSED")
failed = r2.stdout.count("FAILED")

summary = {
  "collected": passed + failed,
  "passed": passed,
  "failed": failed,
  "skipped": 0,
  "exit_code": r2.returncode,
  "duration_seconds": round(duration, 2)
}

with open("evidence/annotation_export_final_gate/pytest_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

with open("evidence/annotation_export_final_gate/pytest_output.txt", "w", encoding="utf-8") as f:
    f.write(r2.stdout)

print("Saved pytest_summary.json")
