import sys
from pathlib import Path
import json

# Add backend directory to sys path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.transliteration_service import TransliterationEngine

def main():
    engine = TransliterationEngine(use_mock=True)
    
    # First 2 lines of Yapıştırılan metin(11).txt as test cases
    test_lines = [
        "ياپدى گورديكم جنگله الماز قريشسنده قيلوجه طرفندن بر",
        "حواله ياپدى قرداش اوغلى اق تيمورى اوزرنده قودى غايت"
    ]
    
    results = []
    
    print("Testing Transliteration Engine (Mock Mode)...\n")
    
    for i, line in enumerate(test_lines, 1):
        academic = engine.transliterate_academic(line)
        simple = engine.transliterate_simple(line)
        
        results.append({
            "line": i,
            "ottoman": line,
            "academic": academic,
            "simple": simple
        })
        
        print(f"Line {i} processed.")
        
    out_dir = Path(__file__).resolve().parents[1] / "evidence" / "transliteration_q10"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / "transliteration_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"Results saved to {out_dir}/transliteration_test_results.json")

if __name__ == "__main__":
    main()
