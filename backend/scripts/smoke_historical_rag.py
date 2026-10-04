import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.historical_rag import (
    HistoricalQdrantStore,
)


def main():

    store = HistoricalQdrantStore()

    try:

        store.upsert(
            10001,
            (
                "Dâhiliye Nezâreti. Dahiliye Nezareti. "
                "Osmanlı Devleti'nin içişlerinden ve "
                "iç idaresinden sorumlu kurumdur."
            ),
            {
                "title": "Dâhiliye Nezâreti",
                "type": "institution",
                "verified": False,
                "source_type": "SMOKE_TEST",
            },
        )

        store.upsert(
            10002,
            (
                "Hariciye Nezâreti. Hariciye Nezareti. "
                "Osmanlı Devleti'nin dışişleri ve "
                "diplomatik ilişkilerinden sorumludur."
            ),
            {
                "title": "Hariciye Nezâreti",
                "type": "institution",
                "verified": False,
                "source_type": "SMOKE_TEST",
            },
        )

        query = (
            "Osmanlı Devleti'nde içişlerinden "
            "sorumlu kurum hangisidir?"
        )

        results = store.lexical_search(
            query,
            limit=2,
        )

        print("=== HISTORICAL RAG ===")

        for i, result in enumerate(
            results,
            start=1
        ):
            print(
                i,
                result.get("title"),
                result.get("score")
            )

        if not results:
            raise RuntimeError(
                "Historical RAG returned no result."
            )

        if (
            results[0]
            .get("title")
            != "Dâhiliye Nezâreti"
        ):
            raise RuntimeError(
                "Wrong top historical result."
            )

        print(
            "HISTORICAL_RAG_BACKEND_GATE: PASS"
        )

    finally:
        store.close()


if __name__ == "__main__":
    main()
