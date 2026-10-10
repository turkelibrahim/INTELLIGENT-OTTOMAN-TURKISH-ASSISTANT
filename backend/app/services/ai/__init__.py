"""AI provider package."""
from .ollama_provider import OllamaProvider

__all__ = ["OllamaProvider"]
from .router import smart_router
