"""Hybrid code search combining BM25 keyword retrieval and FAISS dense vector search."""

import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Literal
import numpy as np

from app.models.code_chunk import SearchResult, CodeChunk
from app.retrieval.vector_store import FaissVectorStore
from app.retrieval.bm25_store import BM25Store
from app.embeddings.base import BaseEmbeddingModel
from app.embeddings.embedding_model import SentenceTransformerEmbeddingModel
from app.config import settings

SearchMode = Literal["hybrid", "vector", "keyword"]


class HybridSearchEngine:
    """Combines dense semantic vector retrieval (FAISS) with sparse lexical retrieval (BM25)."""

    def __init__(
        self,
        vector_store: FaissVectorStore,
        bm25_store: BM25Store,
        embedding_model: Optional[BaseEmbeddingModel] = None,
    ):
        self.vector_store = vector_store
        self.bm25_store = bm25_store
        self.embedding_model = embedding_model or SentenceTransformerEmbeddingModel()

    @classmethod
    def from_index_dir(
        cls,
        index_dir: Path,
        embedding_model: Optional[BaseEmbeddingModel] = None,
    ) -> "HybridSearchEngine":
        """Factory method to load both FAISS and BM25 indices from disk."""
        vector_store = FaissVectorStore.load(index_dir)
        bm25_store = BM25Store.load(index_dir, vector_store.chunks)
        return cls(vector_store=vector_store, bm25_store=bm25_store, embedding_model=embedding_model)

    @classmethod
    def from_repo_name(
        cls,
        repo_name: str,
        embedding_model: Optional[BaseEmbeddingModel] = None,
    ) -> "HybridSearchEngine":
        """Loads a hybrid search engine for an indexed repository by name."""
        index_dir = settings.INDEXES_DIR / repo_name
        return cls.from_index_dir(index_dir, embedding_model=embedding_model)

    def _normalize_scores(self, scored_items: Dict[str, float]) -> Dict[str, float]:
        """Applies min-max normalization to raw scores to map them into [0.0, 1.0]."""
        if not scored_items:
            return {}
        scores = list(scored_items.values())
        min_s, max_s = min(scores), max(scores)
        if abs(max_s - min_s) < 1e-6:
            return {k: 1.0 for k in scored_items}
        return {k: (s - min_s) / (max_s - min_s) for k, s in scored_items.items()}

    def search(
        self,
        query: str,
        top_k: int = 5,
        mode: SearchMode = "hybrid",
        alpha: float = 0.6,
    ) -> Tuple[List[SearchResult], float]:
        """Performs search according to selected retrieval mode.

        Args:
            query: Natural language or keyword search string.
            top_k: Maximum number of ranked results to return.
            mode: 'hybrid', 'vector', or 'keyword'.
            alpha: Weight for dense vector similarity in [0.0, 1.0] (1.0 = pure vector, 0.0 = pure BM25).

        Returns:
            Tuple of (ranked SearchResults, latency in milliseconds).
        """
        start_time = time.perf_counter()

        if mode == "vector" or (mode == "hybrid" and alpha >= 0.999):
            # Dense-only search
            query_vector = self.embedding_model.encode_single(query)
            results = self.vector_store.search(query_vector, top_k=top_k)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return results, latency_ms

        if mode == "keyword" or (mode == "hybrid" and alpha <= 0.001):
            # BM25-only search
            results = self.bm25_store.search(query, top_k=top_k)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return results, latency_ms

        # Hybrid Search: Retrieve larger candidate pool from both systems
        candidate_k = max(top_k * 3, 20)

        # 1. Vector Search
        query_vector = self.embedding_model.encode_single(query)
        vector_results = self.vector_store.search(query_vector, top_k=candidate_k)

        # 2. BM25 Search
        bm25_results = self.bm25_store.search(query, top_k=candidate_k)

        # Map chunk_id to CodeChunk
        chunk_map: Dict[str, CodeChunk] = {}
        dense_raw_scores: Dict[str, float] = {}
        bm25_raw_scores: Dict[str, float] = {}

        for r in vector_results:
            cid = r.chunk.chunk_id
            chunk_map[cid] = r.chunk
            dense_raw_scores[cid] = r.score

        for r in bm25_results:
            cid = r.chunk.chunk_id
            chunk_map[cid] = r.chunk
            bm25_raw_scores[cid] = r.score

        # Normalize score spaces
        dense_norm = self._normalize_scores(dense_raw_scores)
        bm25_norm = self._normalize_scores(bm25_raw_scores)

        # Fuse scores
        all_ids = set(dense_raw_scores.keys()) | set(bm25_raw_scores.keys())
        fused_scores: Dict[str, float] = {}

        for cid in all_ids:
            d_score = dense_norm.get(cid, 0.0)
            b_score = bm25_norm.get(cid, 0.0)
            fused_scores[cid] = (alpha * d_score) + ((1.0 - alpha) * b_score)

        # Rank and build SearchResult objects
        sorted_ids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)[:top_k]

        results: List[SearchResult] = []
        for rank, cid in enumerate(sorted_ids, start=1):
            results.append(
                SearchResult(
                    chunk=chunk_map[cid],
                    score=round(fused_scores[cid], 4),
                    rank=rank,
                )
            )

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return results, latency_ms
