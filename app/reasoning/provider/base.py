"""Abstract base class interface for CodeLens LLM Providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
import numpy as np


class LLMProvider(ABC):
    """Universal interface for LLM text generation, streaming, embeddings, and structured JSON output."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider ('gemini' or 'local')."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_tier: str = "flash",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs,
    ) -> str:
        """Generates a text completion given a prompt and optional system instructions."""
        pass

    @abstractmethod
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_tier: str = "flash",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs,
    ) -> Iterator[str]:
        """Streams text chunks incrementally."""
        pass

    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """Computes dense vector embeddings for a batch of strings, returning a float32 numpy array."""
        pass

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        schema: Optional[Any] = None,
        system_prompt: Optional[str] = None,
        model_tier: str = "flash",
        **kwargs,
    ) -> Dict[str, Any]:
        """Generates structured JSON output strictly conforming to the requested schema or prompt."""
        pass
