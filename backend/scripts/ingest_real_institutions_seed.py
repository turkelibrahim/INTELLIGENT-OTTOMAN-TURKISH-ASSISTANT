import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.historical_rag import HistoricalCorpusIngestor


def main():
    path = (
        ROOT.parent
        / "datasets"
        / "historical_knowledge"
        / "02_structured"
        / "institutions_seed_v1.jsonl"
    )

    ingestor = HistoricalCorpusIngestor()

    try:
        result = ingestor.ingest_jsonl(path)

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        if result["accepted"] != 7:
            raise RuntimeError(
                f"Expected 7 accepted records, got {result['accepted']}"
            )

        if result["rejected"] != 0:
            raise RuntimeError(
                f"Unexpected rejected records: {result['errors']}"
            )

        count = ingestor.store.count()

        print()
        print("PRODUCTION_HISTORICAL_POINTS:", count)
        print("REAL_CORPUS_SEED_GATE: PASS")

    finally:
        ingestor.close()


if __name__ == "__main__":
    main()
