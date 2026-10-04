import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.historical_rag import HistoricalQdrantStore
from app.services.historical_analysis import HistoricalAnalyzer


SMOKE_ID = 20001


def main():

    store = HistoricalQdrantStore()

    try:
        store.upsert(
            SMOKE_ID,
            (
                "Dâhiliye Nezâreti Osmanlı Devleti'nin "
                "iç idare ve içişleriyle ilgili merkezî "
                "kurumlarından biridir."
            ),
            {
                "title": "Dâhiliye Nezâreti",
                "type": "institution",
                "verified": True,

                # Bu kayıt yalnız smoke test içindir.
                "source_type": "SMOKE_TEST",
                "source_id": "SMOKE-20001"
            }
        )

        analyzer = HistoricalAnalyzer(
            store=store
        )

        document_text = (
            "Dâhiliye Nezâreti tarafından İstanbul'da "
            "hazırlanan bu yazıda idarî meseleler ele alınmıştır."
        )

        entities = {
            "PERSON": [],
            "LOCATION": ["İstanbul"],
            "DATE": [],
            "ORGANIZATION": [
                "Dâhiliye Nezâreti"
            ]
        }

        result = analyzer.analyze(
            document_text=document_text,
            entities=entities,
        )

        print(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

        if (
            result["_retrieval"]
            ["verified_sources_found"] < 1
        ):
            raise RuntimeError(
                "Verified RAG source was not retrieved."
            )

        institutions = " ".join(
            result.get(
                "institutions",
                []
            )
        ).lower()

        author = (
            result
            .get("author_or_institution", {})
            .get("value", "")
            .lower()
        )

        if (
            "dâhiliye" not in institutions
            and "dahiliye" not in institutions
            and "dâhiliye" not in author
            and "dahiliye" not in author
        ):
            raise RuntimeError(
                "Historical analyzer failed institution grounding."
            )

        print()
        print(
            "HISTORICAL_ANALYZER_GATE: PASS"
        )

    finally:

        try:
            store.delete([SMOKE_ID])
            print(
                "SMOKE_SOURCE_CLEANUP: PASS"
            )
        finally:
            store.close()


if __name__ == "__main__":
    main()
