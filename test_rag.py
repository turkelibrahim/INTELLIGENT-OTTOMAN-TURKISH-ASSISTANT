import sys
from pathlib import Path

# Add backend to path so we can import
sys.path.append(str(Path("backend").absolute()))

from app.services.historical_rag.qdrant_store import HistoricalQdrantStore

def test_rag():
    print("Initialize RAG Store (Qdrant Local + Ollama Embeddings)...")
    try:
        store = HistoricalQdrantStore()
        print("[PASS] Qdrant Store initialized successfully.")
    except Exception as e:
        print(f"[FAIL] Initialization failed: {e}")
        return

    print("Testing Vector Search with query: 'Osmanlı'...")
    try:
        results = store.dense_search("Osmanlı", limit=2)
        print(f"[PASS] RAG Search successful. Found {len(results)} context items.")
        for r in results:
            text = r.get("text", "")[:50].replace("\n", " ")
            print(f" - {text}... (Score: {r.get('score', 0)})")
    except Exception as e:
        print(f"[FAIL] RAG Search failed: {e}")

if __name__ == "__main__":
    test_rag()
