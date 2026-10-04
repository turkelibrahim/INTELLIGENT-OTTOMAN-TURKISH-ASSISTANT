import json
import os
from typing import Any, Dict, List, Optional

import requests


class OllamaProvider:
    """
    Local Ollama LLM provider.

    Default production-local model:
        qwen3.5:4b

    Ollama API:
        http://127.0.0.1:11434
    """

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: int = 180,
        keep_alive: Optional[str] = None,
    ):
        self.model = (
            model
            or os.getenv("OLLAMA_MODEL")
            or "qwen3.5:4b"
        )

        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or "http://127.0.0.1:11434"
        ).rstrip("/")

        self.timeout_seconds = int(
            os.getenv("OLLAMA_TIMEOUT_SECONDS", str(timeout_seconds))
        )

        self.keep_alive = (
            keep_alive
            if keep_alive is not None
            else os.getenv("OLLAMA_KEEP_ALIVE", "10m")
        )

    @property
    def chat_url(self) -> str:
        return f"{self.base_url}/api/chat"

    @property
    def tags_url(self) -> str:
        return f"{self.base_url}/api/tags"

    def health_check(self) -> Dict[str, Any]:
        """
        Checks whether Ollama is reachable and whether
        the configured model is installed.
        """
        response = requests.get(
            self.tags_url,
            timeout=10,
        )
        response.raise_for_status()

        payload = response.json()

        installed_models = [
            item.get("name", "")
            for item in payload.get("models", [])
        ]

        model_available = any(
            name == self.model
            or name.startswith(f"{self.model}:")
            for name in installed_models
        )

        return {
            "provider": "ollama",
            "base_url": self.base_url,
            "model": self.model,
            "reachable": True,
            "model_available": model_available,
            "installed_models": installed_models,
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        think: bool = False,
    ) -> str:
        """
        Sends a chat request to the local Ollama model.

        If schema is supplied, Ollama is asked to return
        structured JSON matching that JSON Schema.
        """

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": think,
            "options": {
                "temperature": temperature,
            },
        }

        if self.keep_alive:
            payload["keep_alive"] = self.keep_alive

        if schema is not None:
            payload["format"] = schema

        response = requests.post(
            self.chat_url,
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        data = response.json()

        content = (
            data.get("message", {})
            .get("content", "")
            .strip()
        )

        if not content:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        return content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        schema: Dict[str, Any],
        *,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Requests structured JSON and parses it.
        """

        raw = self.chat(
            messages,
            schema=schema,
            temperature=temperature,
            think=False,
        )

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Ollama returned invalid JSON: {raw}"
            ) from exc

        if not isinstance(parsed, dict):
            raise RuntimeError(
                "Ollama structured response must be a JSON object."
            )

        return parsed
