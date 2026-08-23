"""Integration test for full ingestion, indexing, and semantic search."""

from pathlib import Path
from app.pipeline import IngestionPipeline
from app.retrieval.search import SearchEngine
from app.config import settings


def test_full_pipeline_ingest_and_search(sample_repo_path: Path):
    pipeline = IngestionPipeline()
    meta = pipeline.run_local(sample_repo_path)

    assert meta.repo_name == "sample_repo"
    assert meta.total_files >= 6
    assert meta.total_chunks >= 6

    # Verify index directory exists
    index_dir = settings.INDEXES_DIR / "sample_repo"
    assert index_dir.exists()
    assert (index_dir / "index.faiss").exists()
    assert (index_dir / "chunks.json").exists()

    # Create search engine and query
    engine = SearchEngine.from_index_dir(index_dir)

    # 1. Query for authentication
    results, latency = engine.search("Where is user login and password authentication?", top_k=3)
    assert len(results) > 0
    assert latency > 0
    top_chunk = results[0].chunk
    assert "auth.py" in top_chunk.file_path or top_chunk.symbol_name in {"login_user", "UserSessionManager"}

    # 2. Query for caching
    results, _ = engine.search("Least Recently Used LRU cache eviction and key lookup", top_k=3)
    assert len(results) > 0
    assert any("cache.cpp" in r.chunk.file_path or "LRUCache" in (r.chunk.symbol_name or "") for r in results)

    # 3. Query for memory pool allocation
    results, _ = engine.search("C memory pool allocation buffer", top_k=3)
    assert len(results) > 0
    assert any("memory.c" in r.chunk.file_path or "pool_allocate" in (r.chunk.symbol_name or "") for r in results)
