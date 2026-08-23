"""FAISS vector store and persistence management."""

import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import faiss
from app.models.code_chunk import CodeChunk, SearchResult, IndexMetadata
from app.config import settings


class FaissVectorStore:
    """Vector store leveraging FAISS IndexFlatIP (Inner Product on normalized vectors = Cosine Similarity)."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.chunks: List[CodeChunk] = []
        self.metadata: Optional[IndexMetadata] = None

    def add_chunks(self, chunks: List[CodeChunk], embeddings: np.ndarray):
        """Adds code chunks and their corresponding embedding vectors to the FAISS index."""
        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch between number of chunks ({len(chunks)}) and embeddings ({len(embeddings)})")

        if len(chunks) == 0:
            return

        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension {embeddings.shape[1]} does not match index dimension {self.dimension}")

        # Ensure float32 contiguous array
        vectors = np.ascontiguousarray(embeddings, dtype=np.float32)
        self.index.add(vectors)
        self.chunks.extend(chunks)

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[SearchResult]:
        """Searches the vector store for the top-k most similar code chunks."""
        if self.index.ntotal == 0:
            return []

        # Ensure query is 2D float32 array
        if query_vector.ndim == 1:
            query_vector = np.expand_dims(query_vector, axis=0)
        query_vector = np.ascontiguousarray(query_vector, dtype=np.float32)

        actual_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, actual_k)

        results: List[SearchResult] = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), start=1):
            if idx == -1 or idx >= len(self.chunks):
                continue
            results.append(
                SearchResult(
                    chunk=self.chunks[idx],
                    score=float(score),
                    rank=rank,
                )
            )

        return results

    def save(self, index_dir: Path, metadata: Optional[IndexMetadata] = None):
        """Persists the FAISS index and chunk metadata to disk."""
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)

        # 1. Save binary FAISS index
        faiss_file = index_dir / "index.faiss"
        faiss.write_index(self.index, str(faiss_file))

        # 2. Save code chunks data
        chunks_file = index_dir / "chunks.json"
        chunks_data = [chunk.model_dump() for chunk in self.chunks]
        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2)

        # 3. Save index metadata stats
        if metadata:
            self.metadata = metadata
            meta_file = index_dir / "metadata.json"
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata.model_dump(), f, indent=2)

    @classmethod
    def load(cls, index_dir: Path) -> "FaissVectorStore":
        """Loads a persisted FAISS index, chunk metadata, and statistics from disk."""
        index_dir = Path(index_dir)
        faiss_file = index_dir / "index.faiss"
        chunks_file = index_dir / "chunks.json"
        meta_file = index_dir / "metadata.json"

        if not faiss_file.exists():
            raise FileNotFoundError(f"FAISS index file not found at {faiss_file}")
        if not chunks_file.exists():
            raise FileNotFoundError(f"Chunks metadata file not found at {chunks_file}")

        # 1. Load FAISS index
        index = faiss.read_index(str(faiss_file))
        store = cls(dimension=index.d)
        store.index = index

        # 2. Load Chunks
        with open(chunks_file, "r", encoding="utf-8") as f:
            raw_chunks = json.load(f)
            store.chunks = [CodeChunk(**item) for item in raw_chunks]

        # 3. Load Metadata if present
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                store.metadata = IndexMetadata(**json.load(f))

        return store
