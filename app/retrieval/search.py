"""Semantic code retrieval engine."""

import time
from pathlib import Path
from typing import List, Tuple, Optional
from app.models.code_chunk import SearchResult
from app.retrieval.vector_store import FaissVectorStore
from app.embeddings.base import BaseEmbeddingModel
from app.embeddings.embedding_model import SentenceTransformerEmbeddingModel
from app.config import settings


class SearchEngine:
    """Semantic search engine that queries the FAISS vector store using local dense embeddings."""

    def __init__(
        self,
        vector_store: FaissVectorStore,
        embedding_model: Optional[BaseEmbeddingModel] = None,
    ):
        self.vector_store = vector_store
        self.embedding_model = embedding_model or SentenceTransformerEmbeddingModel()

    @classmethod
    def from_index_dir(
        cls,
        index_dir: Path,
        embedding_model: Optional[BaseEmbeddingModel] = None,
    ) -> "SearchEngine":
        """Factory method to load a search engine directly from a persisted index directory."""
        store = FaissVectorStore.load(index_dir)
        return cls(vector_store=store, embedding_model=embedding_model)

    @classmethod
    def from_repo_name(
        cls,
        repo_name: str,
        embedding_model: Optional[BaseEmbeddingModel] = None,
    ) -> "SearchEngine":
        """Loads a search engine for an indexed repository by name."""
        index_dir = settings.INDEXES_DIR / repo_name
        return cls.from_index_dir(index_dir, embedding_model=embedding_model)

    def search(self, query: str, top_k: int = 5) -> Tuple[List[SearchResult], float]:
        """Performs semantic search against indexed code chunks.

        Returns:
            Tuple of (ranked SearchResults, latency in milliseconds)
        """
        start_time = time.perf_counter()

        # 1. Embed query locally
        query_vector = self.embedding_model.encode_single(query)

        # 2. Vector search in FAISS
        results = self.vector_store.search(query_vector, top_k=top_k)

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return results, latency_ms
