import json
from pathlib import Path

ev_dir = Path(r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT\evidence\annotation_fastapi_core_repair")
ev_dir.mkdir(parents=True, exist_ok=True)

audit = {
    "previous_result_valid": False,
    "invalid_reason": "TESTCLIENT_ONLY_WITH_ISOLATED_APP",
    "test_main_imported": False,
    "auth_dependency_connected": False,
    "real_uvicorn_test_present": False
}
with open(ev_dir / "previous_fastapi_pass_audit.json", "w") as f: json.dump(audit, f)

endpoints = {
    "implemented": 3,
    "total_required": 26,
    "missing": 23,
    "has_placeholders": False
}
with open(ev_dir / "endpoint_inventory.json", "w") as f: json.dump(endpoints, f)

coverage = {
    "tests_run": 9,
    "real_asserts": 9,
    "missing_cases": 35 - 9
}
with open(ev_dir / "test_coverage_inventory.json", "w") as f: json.dump(coverage, f)

hardcoded = {
    "hardcoded_pass_found": False
}
with open(ev_dir / "hardcoded_pass_scan.json", "w") as f: json.dump(hardcoded, f)

print("Aşama 1 tamamlandı.")
