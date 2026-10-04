import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List
from contextlib import contextmanager

from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models

from .embedding_provider import OllamaEmbeddingProvider


_STORE_CACHE = None

class HistoricalQdrantStore:

    COLLECTION = "ottoman_historical_knowledge_v1"
    DICTIONARY_COLLECTION = "ottoman_dictionary_v1"

    def __new__(cls, *args, **kwargs):
        global _STORE_CACHE
        if _STORE_CACHE is None:
            _STORE_CACHE = super().__new__(cls)
            _STORE_CACHE._initialized = False
        return _STORE_CACHE

    def __init__(self, path: str | None = None):
        if getattr(self, '_initialized', False):
            return
        self.path = Path(
            path
            or os.getenv(
                "HISTORICAL_QDRANT_PATH",
                r"C:\ottoman_ai_data\qdrant"
            )
        )
        self.path.mkdir(parents=True, exist_ok=True)

        self.embedding = OllamaEmbeddingProvider()
        self.bm25 = SparseTextEmbedding(
            model_name="Qdrant/bm25",
            language="turkish",
            disable_stemmer=True,
        )
        self._ensure_collection()
        self._initialized = True

    @contextmanager
    def _get_client(self):
        client = QdrantClient(path=str(self.path))
        try:
            yield client
        finally:
            client.close()

    def _ensure_collection(self):
        with self._get_client() as client:
            if not client.collection_exists(self.COLLECTION):
                client.create_collection(
                    collection_name=self.COLLECTION,
                    vectors_config={"dense": models.VectorParams(size=1024, distance=models.Distance.COSINE)},
                    sparse_vectors_config={"lexical": models.SparseVectorParams(modifier=models.Modifier.IDF)},
                )
            if not client.collection_exists(self.DICTIONARY_COLLECTION):
                client.create_collection(
                    collection_name=self.DICTIONARY_COLLECTION,
                    vectors_config={"dense": models.VectorParams(size=1024, distance=models.Distance.COSINE)},
                    sparse_vectors_config={"lexical": models.SparseVectorParams(modifier=models.Modifier.IDF)},
                )

    def _sparse_vector(self, text: str, query: bool = False):
        if query:
            emb = list(self.bm25.query_embed(text))[0]
        else:
            emb = list(self.bm25.embed(text))[0]

        return models.SparseVector(
            indices=emb.indices.tolist(),
            values=emb.values.tolist(),
        )

    def upsert(self, item_id: int, text: str, payload: Dict[str, Any]):
        dense = self.embedding.embed(text)
        sparse = self._sparse_vector(text)

        point = models.PointStruct(
            id=item_id,
            vector={
                "dense": dense,
                "lexical": sparse,
            },
            payload={
                **payload,
                "text": text,
            },
        )

        with self._get_client() as client:
            client.upsert(
                collection_name=self.COLLECTION,
                points=[point],
                wait=True,
            )

    def lexical_search(
        self, query: str, limit: int = 5, verified_only: bool = True
    ) -> List[Dict[str, Any]]:
        q = self._sparse_vector(query, query=True)
        query_filter = None

        if verified_only:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="verified",
                        match=models.MatchValue(value=True)
                    )
                ]
            )

        with self._get_client() as client:
            results = client.query_points(
                collection_name=self.COLLECTION,
                query=q,
                using="lexical",
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            ).points

        return [
            {
                "id": hit.id,
                "score": float(hit.score),
                **(hit.payload or {}),
            }
            for hit in results
        ]

    def dense_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        q = self.embedding.embed(query)

        with self._get_client() as client:
            results = client.query_points(
                collection_name=self.COLLECTION,
                query=q,
                using="dense",
                limit=limit,
                with_payload=True,
            ).points

        return [
            {
                "id": hit.id,
                "score": float(hit.score),
                **(hit.payload or {}),
            }
            for hit in results
        ]

    @staticmethod
    def _normalize_search_text(value: str) -> str:
        value = str(value or "").casefold()
        value = unicodedata.normalize("NFKD", value)
        value = "".join(char for char in value if not unicodedata.combining(char))

        replacements = {
            "ı": "i",
            "ş": "s",
            "ğ": "g",
            "ç": "c",
            "ö": "o",
            "ü": "u",
        }

        for old, new in replacements.items():
            value = value.replace(old, new)

        value = re.sub(r"[^a-z0-9\s]", " ", value)
        return " ".join(value.split())

    def search(
        self, query: str, limit: int = 5, verified_only: bool = True
    ) -> List[Dict[str, Any]]:
        candidate_limit = max(limit * 4, 12)
        candidates = self.lexical_search(
            query=query, limit=candidate_limit, verified_only=verified_only
        )

        normalized_query = self._normalize_search_text(query)
        reranked = []

        for item in candidates:
            bm25_score = float(item.get("score", 0.0))
            title = self._normalize_search_text(item.get("title", ""))
            aliases = [
                self._normalize_search_text(alias)
                for alias in item.get("aliases", []) if alias
            ]
            keywords = [
                self._normalize_search_text(keyword)
                for keyword in item.get("keywords", []) if keyword
            ]

            title_match = 1 if title and title in normalized_query else 0
            alias_matches = sum(1 for alias in aliases if alias and alias in normalized_query)
            keyword_matches = sum(1 for keyword in keywords if keyword and keyword in normalized_query)

            domain_boost = (title_match * 5.0) + (alias_matches * 4.0) + (keyword_matches * 2.5)
            final_score = bm25_score + domain_boost

            enriched = dict(item)
            enriched["bm25_score"] = bm25_score
            enriched["title_match"] = title_match
            enriched["alias_matches"] = alias_matches
            enriched["keyword_matches"] = keyword_matches
            enriched["domain_boost"] = domain_boost
            enriched["retrieval_score"] = final_score
            reranked.append(enriched)

        reranked.sort(
            key=lambda item: (item["retrieval_score"], item["bm25_score"]),
            reverse=True,
        )
        return reranked[:limit]

    def count(self) -> int:
        with self._get_client() as client:
            return client.count(
                collection_name=self.COLLECTION,
                exact=True,
            ).count

    def delete(self, item_ids: List[int]) -> None:
        if not item_ids:
            return
        with self._get_client() as client:
            client.delete(
                collection_name=self.COLLECTION,
                points_selector=models.PointIdsList(points=item_ids),
                wait=True,
            )
