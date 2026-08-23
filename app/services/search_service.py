"""Service layer for semantic and hybrid code retrieval."""

import time
from typing import Dict, Optional, Tuple, List
from app.config import settings
from app.retrieval.hybrid_search import HybridSearchEngine
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem


class SearchService:
    """Manages search engine caching and query execution."""

    def __init__(self):
        self._engines: Dict[str, HybridSearchEngine] = {}
        self._latencies: List[float] = []

    def get_search_engine(self, repo_name: str) -> HybridSearchEngine:
        """Retrieves or creates a cached HybridSearchEngine instance."""
        if repo_name in self._engines:
            return self._engines[repo_name]

        index_dir = settings.INDEXES_DIR / repo_name
        if not index_dir.exists() or not (index_dir / "index.faiss").exists():
            raise FileNotFoundError(f"Repository index '{repo_name}' not found. Please ingest the repository first.")

        engine = HybridSearchEngine.from_index_dir(index_dir)
        self._engines[repo_name] = engine
        return engine

    def search(self, request: SearchRequest) -> SearchResponse:
        """Executes hybrid, vector, or keyword search against the specified repository."""
        engine = self.get_search_engine(request.repository_id)
        results, latency_ms = engine.search(
            query=request.query,
            top_k=request.top_k,
            mode=request.mode,
            alpha=request.alpha,
        )

        self._latencies.append(latency_ms)
        # Keep last 1000 measurements
        if len(self._latencies) > 1000:
            self._latencies.pop(0)

        items = [
            SearchResultItem(
                file_path=r.chunk.file_path,
                symbol=r.chunk.symbol_name,
                language=r.chunk.language,
                chunk_type=r.chunk.chunk_type.value,
                start_line=r.chunk.start_line,
                end_line=r.chunk.end_line,
                similarity=round(r.score, 4),
                code=r.chunk.code,
                docstring=r.chunk.docstring,
                context_prefix=r.chunk.context_prefix,
                rank=r.rank,
            )
            for r in results
        ]

        return SearchResponse(
            query=request.query,
            repository_id=request.repository_id,
            mode=request.mode,
            alpha=request.alpha,
            latency_ms=round(latency_ms, 2),
            total_results=len(items),
            results=items,
        )

    def get_latency_stats(self) -> Tuple[Optional[float], Optional[float]]:
        """Returns (avg_latency_ms, p95_latency_ms) from recent searches."""
        if not self._latencies:
            return None, None
        sorted_lat = sorted(self._latencies)
        avg_l = sum(sorted_lat) / len(sorted_lat)
        p95_idx = int(len(sorted_lat) * 0.95)
        p95_l = sorted_lat[min(p95_idx, len(sorted_lat) - 1)]
        return round(avg_l, 2), round(p95_l, 2)


search_service = SearchService()
