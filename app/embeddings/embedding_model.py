"""Local SentenceTransformer embedding model implementation."""

from typing import List, Optional
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.embeddings.base import BaseEmbeddingModel


class SentenceTransformerEmbeddingModel(BaseEmbeddingModel):
    """Local embedding generator powered by open-source SentenceTransformers."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
    ):
        self._model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.device = self._resolve_device(device or settings.EMBEDDING_DEVICE)
        self._model = SentenceTransformer(self._model_name, device=self.device)
        self._dimension = self._model.get_sentence_embedding_dimension()

    def _resolve_device(self, preferred_device: str) -> str:
        """Auto-detects the optimal compute accelerator (MPS on Mac, CUDA on GPU, or CPU)."""
        if preferred_device != "auto":
            return preferred_device

        if torch.backends.mps.is_available() and torch.backends.mps.is_built():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        return "cpu"

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """Encodes texts into L2-normalized float32 numpy vectors."""
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=True,  # Crucial for exact Cosine Similarity with FAISS IndexFlatIP
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        """Encodes a single string into an L2-normalized 1D vector."""
        vec = self.encode([text], batch_size=1, show_progress_bar=False)
        return vec[0]
