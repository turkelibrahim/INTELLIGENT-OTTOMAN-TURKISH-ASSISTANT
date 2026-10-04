import sys
from pathlib import Path
import json

# Add backend directory to sys path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.document_intelligence_service import DocIntelligenceEngine

def main():
    engine = DocIntelligenceEngine(use_mock=True)
    
    mock_input = "Havale yaptı karındaş oğlu Ak Timur'u üzerinde kodu gayet bahadırlardan idi ana yarar yoldaşlar koştu dağ tarafından bir..."
    
    print("Testing Document Intelligence Engine (Mock Mode)...\n")
    print("INPUT TEXT: [Mock input with special characters]")
    
    # 1. Translate
    translation = engine.translate_to_modern_turkish(mock_input)
    print(f"--- TRANSLATION ---\n{translation}\n")
    
    # 2. Summarize
    summary = engine.summarize_document(mock_input)
    print(f"--- SUMMARY ---\n{summary}\n")
    
    # 3. Extract Entities
    entities = engine.extract_entities(mock_input)
    print(f"--- EXTRACTED ENTITIES (JSON) ---")
    print(json.dumps(entities, ensure_ascii=False, indent=2))
    print()
    
    # Save results
    results = {
        "input": mock_input,
        "translation": translation,
        "summary": summary,
        "entities": entities
    }
    
    out_dir = Path(__file__).resolve().parents[1] / "evidence" / "doc_intelligence_q11"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = out_dir / "doc_intelligence_test_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"Results saved to {out_file}")

if __name__ == "__main__":
    main()
