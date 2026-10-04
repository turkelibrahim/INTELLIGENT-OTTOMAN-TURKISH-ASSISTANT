import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.evaluation.metrics import calculate_metrics, normalize_ottoman_text

def test():
    tests = [
        {"name": "1. Tam ayni cumle", "gt": "merhaba dunya", "hyp": "merhaba dunya"},
        {"name": "2. Tek kelime substitution", "gt": "merhaba dunya", "hyp": "merhaba uzay"},
        {"name": "3. Tek kelime deletion", "gt": "merhaba guzel dunya", "hyp": "merhaba dunya"},
        {"name": "4. Tek kelime insertion", "gt": "merhaba dunya", "hyp": "merhaba guzel dunya"},
        {"name": "5. Iki kelimenin yanlis birlestirilmesi", "gt": "merhaba dunya", "hyp": "merhabadunya"},
        {"name": "6. Bir kelimenin ikiye bolunmesi", "gt": "merhabadunya", "hyp": "merhaba dunya"},
        {"name": "7. Coklu bosluk", "gt": "merhaba dunya", "hyp": "merhaba   dunya"},
        {"name": "8. NBSP", "gt": "merhaba dunya", "hyp": "merhaba\u00A0dunya"},
        {"name": "9. Noktalama", "gt": "merhaba, dunya!", "hyp": "merhaba dunya"},
        {"name": "10. Arapca rakam", "gt": "sayi ١٢٣", "hyp": "sayi ١٢٣"},
        {"name": "11. Tatweel", "gt": "merhaba", "hyp": "merha\u0640ba"},
        {"name": "12. NFC esdegeri", "gt": "\u00e7", "hyp": "c\u0327"}
    ]
    
    results = []
    has_errors = False
    
    for t in tests:
        # Test strict
        res_strict = calculate_metrics(t["gt"], t["hyp"], strict=True)
        # Test normalized
        res_norm = calculate_metrics(t["gt"], t["hyp"], strict=False)
        
        gt_norm = normalize_ottoman_text(t["gt"])
        hyp_norm = normalize_ottoman_text(t["hyp"])
        
        error = ""
        
        # Validation checks
        if t["name"] == "1. Tam ayni cumle":
            if res_norm["wer"] != 0: error = "WER should be 0"
        elif t["name"] == "2. Tek kelime substitution":
            if res_norm["wer"] != 0.5: error = "WER should be 0.5" # 1 / 2 words
        elif t["name"] == "5. Iki kelimenin yanlis birlestirilmesi":
            # GT: 2 words, Hyp: 1 word.
            # substitutions=1, deletions=1 => WER = 2 / 2 = 1.0 or substitution + deletion.
            pass
        elif t["name"] == "7. Coklu bosluk":
            if res_norm["wer"] != 0: error = "WER should be 0 for multiple spaces"
        elif t["name"] == "8. NBSP":
            if res_norm["wer"] != 0: error = "WER should be 0 for NBSP"
        elif t["name"] == "9. Noktalama":
            if res_norm["wer"] != 0: error = "WER should be 0 for ignored punctuation"
        elif t["name"] == "11. Tatweel":
            if res_norm["wer"] != 0: error = "WER should be 0 for ignored tatweel"
        elif t["name"] == "12. NFC esdegeri":
            if res_norm["wer"] != 0: error = "WER should be 0 for NFC eq"
            
        if error:
            has_errors = True
            
        results.append({
            "name": t["name"],
            "gt": t["gt"],
            "hyp": t["hyp"],
            "gt_norm": gt_norm,
            "hyp_norm": hyp_norm,
            "strict_wer": res_strict.get("wer"),
            "normalized_wer": res_norm.get("wer"),
            "error": error
        })
        
    out_dir = Path(__file__).resolve().parents[1] / "evidence" / "word_boundary_q7"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "wer_synthetic_validation.json"
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"tests": results, "has_errors": has_errors}, f, indent=2, ensure_ascii=False)
        
    print(f"Validation complete. Errors: {has_errors}")
    return 1 if has_errors else 0

if __name__ == "__main__":
    sys.exit(test())
