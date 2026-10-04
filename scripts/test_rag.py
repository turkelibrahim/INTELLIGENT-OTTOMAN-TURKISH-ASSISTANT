import sys
from pathlib import Path
import json

# Add backend directory to sys path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.rag_service import RAGEngine

def main():
    # Initialize in-memory RAGEngine
    engine = RAGEngine()
    
    # Mock data from Q11
    doc_id = "doc_mock_001"
    modern_text = "Kardeşinin oğlu Ak Timur'u görevlendirdi; emrinde çok cesur askerler vardı, ona yetenekli yoldaşlar tahsis etti ve dağ tarafından bir..."
    summary = "Metinde, bir askeri sevkiyat veya görevlendirme anlatılmaktadır. Ak Timur komutasındaki cesur ve yetenekli askerlerin dağlık bir bölgeye doğru harekete geçirildiği belirtilmektedir."
    entities = {
        "PERSON": ["Ak Timur"],
        "LOCATION": [],
        "DATE": [],
        "ORGANIZATION": []
    }
    
    print("--- 1. Indexing Document ---")
    engine.index_document(doc_id, modern_text, summary, entities)
    print("Document successfully indexed to ChromaDB!\n")
    
    # Semantic Search Test
    print("--- 2. Semantic Search ---")
    query = "Dağlık bölgeye gönderilen komutan kimdi?"
    print(f"Query: '{query}'\n")
    
    results = engine.semantic_search(query, top_k=1)
    
    out_dir = Path(__file__).resolve().parents[1] / "evidence" / "rag_integration_q12"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "rag_test_results.json"
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "query": query,
            "results": results
        }, f, ensure_ascii=False, indent=2)
        
    for idx, res in enumerate(results, 1):
        print(f"Result {idx}:")
        print(f"  ID: {res['id']}")
        print(f"  Text: {res['text']}")
        print(f"  Metadata: {json.dumps(res['metadata'], ensure_ascii=False)}")
        print(f"  Distance (Cosine): {res['distance']}")
        
    print(f"\nResults saved to {out_file}")

if __name__ == "__main__":
    # Disable chromadb telemetry output for cleaner logs
    import os
    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    main()
