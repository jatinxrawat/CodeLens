"""Unit tests for FAISS vector store indexing and persistence."""

import tempfile
import numpy as np
from pathlib import Path
from app.models.code_chunk import CodeChunk, ChunkType, IndexMetadata
from app.retrieval.vector_store import FaissVectorStore


def test_vector_store_add_and_search():
    dimension = 4
    store = FaissVectorStore(dimension=dimension)

    chunks = [
        CodeChunk(
            chunk_id="chunk_1",
            repo_name="test_repo",
            file_path="auth.py",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            symbol_name="login",
            start_line=1,
            end_line=10,
            code="def login(): pass",
        ),
        CodeChunk(
            chunk_id="chunk_2",
            repo_name="test_repo",
            file_path="cache.cpp",
            language="cpp",
            chunk_type=ChunkType.CLASS,
            symbol_name="LRUCache",
            start_line=1,
            end_line=20,
            code="class LRUCache {};",
        ),
    ]

    # Normalized vectors
    v1 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    embeddings = np.stack([v1, v2])

    store.add_chunks(chunks, embeddings)
    assert store.index.ntotal == 2

    # Query matching v1
    query_vec = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    results = store.search(query_vec, top_k=2)

    assert len(results) == 2
    assert results[0].chunk.symbol_name == "login"
    assert results[0].rank == 1
    assert abs(results[0].score - 1.0) < 1e-4


def test_vector_store_persistence(tmp_path: Path):
    dimension = 4
    store = FaissVectorStore(dimension=dimension)

    chunks = [
        CodeChunk(
            chunk_id="c1",
            repo_name="demo",
            file_path="service.ts",
            language="typescript",
            chunk_type=ChunkType.CLASS,
            symbol_name="PaymentService",
            start_line=5,
            end_line=25,
            code="class PaymentService {}",
        )
    ]
    emb = np.array([[0.5, 0.5, 0.5, 0.5]], dtype=np.float32)
    emb /= np.linalg.norm(emb)

    store.add_chunks(chunks, emb)

    metadata = IndexMetadata(
        repo_name="demo",
        repo_source="local",
        indexed_at="2026-08-23T00:00:00Z",
        total_files=1,
        total_chunks=1,
        languages={"typescript": 1},
        chunk_types={"class": 1},
        embedding_model="test-model",
        embedding_dimension=4,
        ingestion_time_sec=0.1,
        parsing_time_sec=0.1,
        embedding_time_sec=0.1,
        indexing_time_sec=0.1,
        total_time_sec=0.4,
    )

    save_dir = tmp_path / "test_index"
    store.save(save_dir, metadata=metadata)

    assert (save_dir / "index.faiss").exists()
    assert (save_dir / "chunks.json").exists()
    assert (save_dir / "metadata.json").exists()

    # Load back
    loaded_store = FaissVectorStore.load(save_dir)
    assert loaded_store.index.ntotal == 1
    assert len(loaded_store.chunks) == 1
    assert loaded_store.chunks[0].symbol_name == "PaymentService"
    assert loaded_store.metadata is not None
    assert loaded_store.metadata.repo_name == "demo"
