import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.document_intelligence_service import DocIntelligenceEngine


def main():
    engine = DocIntelligenceEngine(use_mock=False)

    health = engine.health_check()

    print("=== DOCUMENT INTELLIGENCE HEALTH ===")
    print(json.dumps(health, ensure_ascii=False, indent=2))

    sample = (
        "Ak Timur, 1299 tarihinde Söğüt'te "
        "Osmanlı Beyliği adına görevlendirildi."
    )

    modern = engine.translate_to_modern_turkish(sample)
    summary = engine.summarize_document(sample)
    entities = engine.extract_entities(sample)

    print()
    print("=== MODERN TURKISH ===")
    print(modern)

    print()
    print("=== SUMMARY ===")
    print(summary)

    print()
    print("=== ENTITIES ===")
    print(json.dumps(entities, ensure_ascii=False, indent=2))

    if not modern.strip():
        raise RuntimeError("Modern Turkish output is empty.")

    if not summary.strip():
        raise RuntimeError("Summary output is empty.")

    if not isinstance(entities, dict):
        raise RuntimeError("NER output is invalid.")

    print()
    print("DOCUMENT_INTELLIGENCE_LOCAL_LLM_GATE: PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print()
        print("DOCUMENT_INTELLIGENCE_LOCAL_LLM_GATE: FAIL")
        print(type(exc).__name__ + ":", exc)
        sys.exit(1)
