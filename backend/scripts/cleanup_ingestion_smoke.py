import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.historical_rag import (
    HistoricalCorpusIngestor,
    HistoricalQdrantStore,
)

SOURCE_ID = "TEST-A"
CHUNK_ID = "001"

store = HistoricalQdrantStore()

try:
    point_id = HistoricalCorpusIngestor._stable_point_id(
        SOURCE_ID,
        CHUNK_ID
    )

    store.delete([point_id])

    count = store.count()

    print("TEST_RECORD_REMOVED")
    print("PRODUCTION_HISTORICAL_POINTS:", count)

    if count != 7:
        raise RuntimeError(
            f"Expected exactly 7 real corpus points, got {count}"
        )

    print("PRODUCTION_CORPUS_CLEAN_GATE: PASS")

finally:
    store.close()
