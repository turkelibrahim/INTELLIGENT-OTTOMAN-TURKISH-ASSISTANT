import chromadb
from chromadb.config import Settings
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Retrieval-Augmented Generation (RAG) Service
    Handles indexing of modern Turkish texts with metadata (NER entities) 
    and semantic searching.
    """
    
    def __init__(self, persist_directory: str = None):
        """
        Initializes ChromaDB collection.
        Uses in-memory if persist_directory is None.
        """
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            # Fallback for testing
            self.client = chromadb.Client()
            
        # Create or get collection
        self.collection_name = "ottoman_docs_collection"
        # We rely on ChromaDB's default embedding function (all-MiniLM-L6-v2)
        # for quick prototyping. In production, a multilingual/Turkish model like 
        # sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 would be ideal.
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )
        logger.info(f"Initialized RAGEngine with collection: {self.collection_name}")

    def index_document(self, doc_id: str, modern_text: str, summary: str, entities: Dict[str, Any]):
        """
        Indexes a document into the vector database.
        
        :param doc_id: Unique identifier for the document
        :param modern_text: Translated/Modernized text (used for vector embedding)
        :param summary: Brief summary of the text
        :param entities: Extracted NER entities (PERSON, LOCATION, DATE, ORG)
        """
        # Metadata must be simple key-value pairs (strings, ints, floats, bools)
        # We serialize list of entities into strings for metadata filtering capabilities
        metadata = {
            "summary": summary,
            "person_entities": ", ".join(entities.get("PERSON", [])),
            "location_entities": ", ".join(entities.get("LOCATION", [])),
            "date_entities": ", ".join(entities.get("DATE", [])),
            "organization_entities": ", ".join(entities.get("ORGANIZATION", []))
        }
        
        self.collection.add(
            documents=[modern_text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        logger.info(f"Document {doc_id} indexed successfully.")

    def semantic_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Searches the vector database for semantically similar documents.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else None
                })
                
        return formatted_results
