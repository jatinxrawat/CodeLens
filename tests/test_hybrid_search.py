"""Unit tests for hybrid search retrieval modes (Vector, BM25, and Hybrid with alpha)."""

from pathlib import Path
from app.models.code_chunk import CodeChunk, ChunkType
from app.retrieval.vector_store import FaissVectorStore
from app.retrieval.bm25_store import BM25Store
from app.retrieval.hybrid_search import HybridSearchEngine


def test_hybrid_search_modes(sample_repo_path: Path):
    from app.pipeline import IngestionPipeline
    from app.config import settings

    pipeline = IngestionPipeline()
    pipeline.run_local(sample_repo_path)

    index_dir = settings.INDEXES_DIR / "sample_repo"
    engine = HybridSearchEngine.from_index_dir(index_dir)

    query = "Where is user login and session authentication?"

    # 1. Hybrid Search (alpha = 0.6)
    results_hybrid, lat_h = engine.search(query, top_k=3, mode="hybrid", alpha=0.6)
    assert len(results_hybrid) > 0
    assert lat_h > 0

    # 2. Vector Search (mode = 'vector')
    results_vec, lat_v = engine.search(query, top_k=3, mode="vector")
    assert len(results_vec) > 0

    # 3. Keyword Search (mode = 'keyword')
    results_bm25, lat_b = engine.search("login_user verify_token", top_k=3, mode="keyword")
    assert len(results_bm25) > 0
    assert any("auth.py" in r.chunk.file_path for r in results_bm25)
