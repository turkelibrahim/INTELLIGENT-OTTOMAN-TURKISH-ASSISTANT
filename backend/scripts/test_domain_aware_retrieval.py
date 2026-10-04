import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.historical_rag import HistoricalQdrantStore


TESTS = [
    (
        "Osmanlı Devleti'nde dışişleri ve diplomatik ilişkilerden sorumlu nezaret hangisidir?",
        "Hariciye Nezâreti",
    ),
    (
        "Osmanlı Devleti'nde içişleri ve iç idareyle ilgili merkezî kurum hangisidir?",
        "Dâhiliye Nezâreti",
    ),
    (
        "Osmanlı merkez yönetimindeki önemli karar organlarından biri hangisidir?",
        "Dîvân-ı Hümâyun",
    ),
    (
        "1870 yılında adliye teşkilatıyla ilişkili olarak kurulan nezaret hangisidir?",
        "Adliye Nezâreti",
    ),
]


def main():

    store = HistoricalQdrantStore()

    passed = 0

    try:

        print(
            "=== DOMAIN-AWARE REAL CORPUS TEST ==="
        )

        for index, (
            query,
            expected
        ) in enumerate(
            TESTS,
            start=1
        ):

            results = store.search(
                query=query,
                limit=3,
                verified_only=True,
            )

            actual = (
                results[0].get("title")
                if results
                else None
            )

            ok = actual == expected

            if ok:
                passed += 1

            print()
            print("TEST", index)
            print("QUERY:", query)
            print("EXPECTED:", expected)
            print("ACTUAL:", actual)
            print(
                "STATUS:",
                "PASS" if ok else "FAIL"
            )

            print("TOP RESULTS:")

            for rank, item in enumerate(
                results,
                start=1
            ):
                print(
                    rank,
                    "|",
                    item.get("title"),
                    "| FINAL:",
                    round(
                        item.get(
                            "retrieval_score",
                            0
                        ),
                        6
                    ),
                    "| BM25:",
                    round(
                        item.get(
                            "bm25_score",
                            0
                        ),
                        6
                    ),
                    "| KEYWORDS:",
                    item.get(
                        "keyword_matches"
                    ),
                    "| ALIASES:",
                    item.get(
                        "alias_matches"
                    ),
                )

        print()
        print(
            f"RESULT: {passed}/{len(TESTS)}"
        )

        if passed != len(TESTS):
            raise RuntimeError(
                "Domain-aware retrieval gate failed."
            )

        print(
            "DOMAIN_AWARE_RETRIEVAL_GATE: PASS"
        )

    finally:
        store.close()


if __name__ == "__main__":
    main()
