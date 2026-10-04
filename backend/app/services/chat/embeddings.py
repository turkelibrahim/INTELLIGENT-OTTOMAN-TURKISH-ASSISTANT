import logging
import os
import json
import hashlib
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0"

class VectorStoreService:
    """
    Local persistent vector search using FAISS and sentence-transformers.
    Uses versioned, checksum-validated JSON for metadata security.
    """

    def __init__(
        self,
        persist_directory: str = "./vector_db",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.persist_directory = Path(persist_directory)
        self.model_name = model_name
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.index_path = self.persist_directory / "document_chunks.faiss"
        self.meta_path = self.persist_directory / "document_chunks.json"

        self.index: Optional[faiss.Index] = None
        self.records: List[Dict[str, Any]] = []
        self.collection: Optional[bool] = None

        self._verify_and_load_model()
        self._load_index()
        self.collection = True

    def _calculate_file_hash(self, filepath: Path) -> str:
        if not filepath.exists():
            return ""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _verify_and_load_model(self):
        manifest_path = Path(__file__).parent / "model_manifest.json"
        if not manifest_path.exists():
            raise RuntimeError("Model manifest not found. Provenance verification failed.")
        
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        model_id = manifest.get("model_id")
        revision = manifest.get("revision")
        expected_files = manifest.get("files", {})
        
        from huggingface_hub import snapshot_download
        
        try:
            snapshot_path = snapshot_download(
                repo_id=model_id,
                revision=revision,
                local_files_only=False,
            )
        except Exception as exc:
            logger.error("Failed to download or locate model %s at %s: %s", model_id, revision, exc)
            self.embedding_model = None
            return

        for filename, expected_hash in expected_files.items():
            filepath = Path(snapshot_path) / filename
            if not filepath.exists():
                raise RuntimeError(f"Missing model file: {filename}")
            actual_hash = self._calculate_file_hash(filepath)
            if actual_hash != expected_hash:
                raise RuntimeError(f"Checksum mismatch for {filename}")
                
        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.embedding_model = SentenceTransformer(snapshot_path, trust_remote_code=False, device=device)
            self.model_revision = revision
            logger.info("Loaded and verified embedding model: %s", self.model_name)
        except Exception as exc:
            logger.error("Failed to load embedding model %s: %s", self.model_name, exc)
            self.embedding_model = None

    def _load_index(self) -> None:
        legacy_pkl = self.persist_directory / "document_chunks.pkl"
        if legacy_pkl.exists():
            logger.warning("Legacy .pkl metadata found. It will not be loaded.")

        if self.index_path.exists() and self.meta_path.exists():
            try:
                with self.meta_path.open("r", encoding="utf-8") as handle:
                    metadata = json.load(handle)

                if metadata.get("schema_version") != SCHEMA_VERSION:
                    raise ValueError(f"Invalid schema version: {metadata.get('schema_version')}")

                expected_hash = metadata.get("faiss_index_sha256")
                actual_hash = self._calculate_file_hash(self.index_path)
                if expected_hash and actual_hash != expected_hash:
                    raise ValueError("FAISS index checksum mismatch")

                # Use relative path for FAISS C++ compatibility with non-ASCII paths on Windows
                rel_index_path = os.path.relpath(self.index_path, os.getcwd())
                self.index = faiss.read_index(rel_index_path)
                self.records = metadata.get("records", [])

                if self.index.ntotal == len(self.records):
                    return
                logger.warning("FAISS index and metadata count mismatch; rebuilding empty index")
            except Exception as exc:
                logger.error("Failed to load FAISS vector index or metadata: %s", exc)

        dimension = self._embedding_dimension()
        self.index = faiss.IndexFlatIP(dimension)
        self.records = []

    def _embedding_dimension(self) -> int:
        if self.embedding_model is None:
            raise RuntimeError("Embedding model is not available")
        if hasattr(self.embedding_model, "get_embedding_dimension"):
            return int(self.embedding_model.get_embedding_dimension())
        return int(self.embedding_model.get_sentence_embedding_dimension())

    def _embed(self, texts: List[str]) -> np.ndarray:
        if self.embedding_model is None:
            raise RuntimeError("Embedding model is not available")
        embeddings = self.embedding_model.encode(texts, normalize_embeddings=True)
        return np.asarray(embeddings, dtype="float32")

    def _persist(self) -> None:
        if self.index is None:
            return
            
        tmp_index_fd, tmp_index_path = tempfile.mkstemp(dir=self.persist_directory, suffix=".faiss")
        os.close(tmp_index_fd)
        tmp_index = Path(tmp_index_path)
        
        try:
            rel_tmp_index = os.path.relpath(tmp_index, os.getcwd())
            faiss.write_index(self.index, rel_tmp_index)
            index_hash = self._calculate_file_hash(tmp_index)
            
            metadata = {
                "schema_version": SCHEMA_VERSION,
                "index_id": "document_chunks",
                "embedding_model_id": self.model_name,
                "embedding_model_revision": getattr(self, "model_revision", "unknown"),
                "embedding_dimension": self._embedding_dimension(),
                "faiss_index_sha256": index_hash,
                "records": self.records,
            }
            
            metadata_json = json.dumps(metadata, ensure_ascii=False)
            if len(metadata_json.encode('utf-8')) > 50 * 1024 * 1024:
                raise ValueError("Metadata exceeds 50MB size limit")

            tmp_meta_fd, tmp_meta_path = tempfile.mkstemp(dir=self.persist_directory, suffix=".json")
            with os.fdopen(tmp_meta_fd, "w", encoding="utf-8") as handle:
                handle.write(metadata_json)
            tmp_meta = Path(tmp_meta_path)
            
            tmp_index.replace(self.index_path)
            tmp_meta.replace(self.meta_path)
        except Exception as exc:
            tmp_index.unlink(missing_ok=True)
            if 'tmp_meta' in locals():
                tmp_meta.unlink(missing_ok=True)
            logger.error("Failed to persist FAISS index: %s", exc)
            raise

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]], ids: List[str]) -> None:
        if self.index is None or self.embedding_model is None:
            logger.error("VectorStore not properly initialized. Cannot add texts.")
            return
        if not (len(texts) == len(metadatas) == len(ids)):
            raise ValueError("texts, metadatas and ids must have the same length")
        if not texts:
            return

        try:
            existing_ids = {record["id"] for record in self.records}
            new_texts: List[str] = []
            new_records: List[Dict[str, Any]] = []
            for text, metadata, item_id in zip(texts, metadatas, ids):
                record = {"id": item_id, "text": text, **metadata}
                if item_id in existing_ids:
                    self.records = [r for r in self.records if r["id"] != item_id]
                    self._rebuild_index()
                new_texts.append(text)
                new_records.append(record)

            embeddings = self._embed(new_texts)
            self.index.add(embeddings)
            self.records.extend(new_records)
            self._persist()
        except Exception as exc:
            logger.error("Error adding texts to FAISS vector index: %s", exc)

    def _rebuild_index(self) -> None:
        dimension = self._embedding_dimension()
        self.index = faiss.IndexFlatIP(dimension)
        if self.records:
            embeddings = self._embed([record["text"] for record in self.records])
            self.index.add(embeddings)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if self.index is None or self.embedding_model is None or self.index.ntotal == 0:
            logger.info("VectorStore empty or unavailable. Cannot search.")
            return []

        try:
            query_embedding = self._embed([query])
            search_k = min(max(k * 4, k), self.index.ntotal)
            scores, indexes = self.index.search(query_embedding, search_k)
            formatted_results: List[Dict[str, Any]] = []

            for score, index in zip(scores[0], indexes[0]):
                if index < 0:
                    continue
                record = dict(self.records[int(index)])
                if filter_dict and any(record.get(key) != value for key, value in filter_dict.items()):
                    continue
                record["distance"] = float(1 - score)
                formatted_results.append(record)
                if len(formatted_results) >= k:
                    break

            return formatted_results
        except Exception as exc:
            logger.error("Error searching FAISS vector index: %s", exc)
            return []
