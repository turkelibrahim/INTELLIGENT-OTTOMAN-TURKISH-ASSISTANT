import os
from typing import List

import requests


class OllamaEmbeddingProvider:
    def __init__(
        self,
        model: str = "qwen3-embedding:0.6b",
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: int = 120,
    ):
        self.model = os.getenv(
            "OLLAMA_EMBEDDING_MODEL",
            model
        )

        self.base_url = os.getenv(
            "OLLAMA_BASE_URL",
            base_url
        ).rstrip("/")

        self.timeout_seconds = timeout_seconds

    def embed(self, text: str) -> List[float]:
        response = requests.post(
            f"{self.base_url}/api/embed",
            json={
                "model": self.model,
                "input": text,
            },
            timeout=self.timeout_seconds,
        )

        response.raise_for_status()

        payload = response.json()

        embeddings = payload.get("embeddings")

        if not embeddings:
            raise RuntimeError(
                "Ollama embedding response is empty."
            )

        vector = embeddings[0]

        if len(vector) != 1024:
            raise RuntimeError(
                f"Unexpected embedding dimension: {len(vector)}"
            )

        return vector
