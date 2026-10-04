import subprocess
import json
import os
import sys
from pathlib import Path

# Proje kök dizini ayarları
BACKEND_DIR = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = BACKEND_DIR.parent / "evidence" / "qa_gate"
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def run_tests_with_coverage():
    print("Running pytest with coverage...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--cov=app", "--cov-report=json:coverage.json", "tests/"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("Tests failed! Quality Gate blocked.")
        print(result.stdout)
        print(result.stderr)
        return False, result.stdout
    
    print("Tests passed successfully.")
    return True, result.stdout

def extract_coverage():
    cov_file = BACKEND_DIR / "coverage.json"
    if not cov_file.exists():
        return 0.0
    
    with open(cov_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    return data.get("totals", {}).get("percent_covered", 0.0)

def main():
    print("Starting Quality Gate...")
    
    success, test_output = run_tests_with_coverage()
    
    coverage_percent = extract_coverage()
    print(f"Test Coverage: {coverage_percent:.2f}%")
    
    # QA Raporu oluştur
    report = {
        "tests_passed": success,
        "coverage_percent": coverage_percent,
        "metrics": {
            # Gelecekte EvaluationService ile CER/WER vs eklenecek
            "ocr_cer_mock": 0.05,
            "transliteration_wer_mock": 0.08
        }
    }
    
    try:
        report_path = EVIDENCE_DIR / "qa_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"QA Report saved to: {report_path}")
    except Exception as e:
        print(f"Failed to generate QA report: {e}")
        sys.exit(1)
    
    if not success:
        sys.exit(1)
        
    if coverage_percent < 90.0:
        print(f"Error: Coverage {coverage_percent:.2f}% is below the 90.0% threshold.")
        sys.exit(1)
        
    print("Quality Gate: PASS")
    sys.exit(0)

if __name__ == "__main__":
    main()
