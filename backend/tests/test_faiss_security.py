import pytest
import os
import json
import pickle
import faiss
import tempfile
import hashlib
from pathlib import Path
from app.services.chat.embeddings import VectorStoreService, SCHEMA_VERSION

@pytest.fixture
def temp_vector_db():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

def test_faiss_schema_validation(temp_vector_db):
    service = VectorStoreService(persist_directory=temp_vector_db)
    # Write invalid schema version
    meta_path = Path(temp_vector_db) / "document_chunks.json"
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump({"schema_version": "0.1", "records": []}, f)
    
    # Reload
    service._load_index()
    # It should fallback to empty index rather than crashing
    assert service.index.ntotal == 0
    assert len(service.records) == 0

def test_legacy_pickle_rejection(temp_vector_db):
    service = VectorStoreService(persist_directory=temp_vector_db)
    # Create fake pickle
    pkl_path = Path(temp_vector_db) / "document_chunks.pkl"
    with pkl_path.open("wb") as f:
        pickle.dump([{"id": "test"}], f)
        
    service._load_index()
    assert service.index.ntotal == 0
    assert len(service.records) == 0

def test_metadata_size_limit(temp_vector_db):
    service = VectorStoreService(persist_directory=temp_vector_db)
    # create large metadata
    large_string = "a" * (51 * 1024 * 1024)
    service.records = [{"id": "test", "huge": large_string}]
    # Mock index
    service.index = faiss.IndexFlatIP(384)
    with pytest.raises(ValueError, match="Metadata exceeds 50MB size limit"):
        service._persist()

def test_checksum_validation(temp_vector_db):
    service = VectorStoreService(persist_directory=temp_vector_db)
    service.index = faiss.IndexFlatIP(384)
    service.records = [{"id": "test"}]
    service._persist()
    
    # Corrupt the index file
    index_path = Path(temp_vector_db) / "document_chunks.faiss"
    with open(index_path, "ab") as f:
        f.write(b"corruption")
        
    # Reload should fail checksum and fallback
    service2 = VectorStoreService(persist_directory=temp_vector_db)
    assert service2.index.ntotal == 0

def test_user_isolation(temp_vector_db):
    service = VectorStoreService(persist_directory=temp_vector_db)
    service.add_texts(["test doc 1"], [{"user_id": 1, "document_id": 1}], ["doc1"])
    service.add_texts(["test doc 2"], [{"user_id": 2, "document_id": 2}], ["doc2"])
    
    # Search with user 1 filter
    results = service.similarity_search("test", k=10, filter_dict={"user_id": 1})
    assert len(results) == 1
    assert results[0]["user_id"] == 1
    
    # Search with user 2 filter
    results = service.similarity_search("test", k=10, filter_dict={"user_id": 2})
    assert len(results) == 1
    assert results[0]["user_id"] == 2
