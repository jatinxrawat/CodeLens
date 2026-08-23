"""Abstract base class for local embedding generators."""

from abc import ABC, abstractmethod
from typing import List
import numpy as np


class BaseEmbeddingModel(ABC):
    """Abstract interface for local dense vector embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the dimensionality of the generated embedding vectors."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the model identifier string."""
        pass

    @abstractmethod
    def encode(self, texts: List[str], batch_size: int = 32, show_progress_bar: bool = False) -> np.ndarray:
        """Generates dense vector embeddings for a list of texts. Returns shape (N, D)."""
        pass

    @abstractmethod
    def encode_single(self, text: str) -> np.ndarray:
        """Generates dense vector embedding for a single text. Returns shape (D,)."""
        pass
