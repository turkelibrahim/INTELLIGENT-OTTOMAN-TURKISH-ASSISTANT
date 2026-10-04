import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.historical_rag import (
    HistoricalCorpusIngestor,
)


def main():

    ingestor = HistoricalCorpusIngestor()

    try:

        path = (
            ROOT.parent
            / "datasets"
            / "historical_knowledge"
            / "02_structured"
            / "ingestion_smoke.jsonl"
        )

        result = ingestor.ingest_jsonl(path)

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        if result["accepted"] != 1:
            raise RuntimeError(
                "Expected exactly one accepted record."
            )

        if result["rejected"] != 1:
            raise RuntimeError(
                "Expected exactly one rejected record."
            )

        print()
        print("CORPUS_INGESTION_GATE: PASS")

    finally:
        ingestor.close()


if __name__ == "__main__":
    main()
