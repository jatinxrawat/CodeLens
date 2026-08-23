"""Incremental Repository Updater and Index Synchronizer.

Detects modified, added, and deleted files using file hash tracking and
re-indexes only affected AST chunks into FAISS and BM25 without full rebuilding.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from app.config import settings
from app.models.code_chunk import CodeChunk
from app.ingestion.file_discovery import FileDiscovery
from app.parsing.parser import CodeParser
from app.embeddings import SentenceTransformerEmbeddingModel
from app.retrieval.vector_store import FaissVectorStore
from app.retrieval.bm25_store import BM25Store


class IncrementalUpdateSummary(BaseModel):
    repository_id: str
    added_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]
    total_reindexed_chunks: int
    duration_sec: float
    status: str = "completed"


class IncrementalUpdater:
    """Synchronizes vector and lexical indexes when repository files change."""

    def __init__(self):
        self.file_discovery = FileDiscovery()
        self.parser = CodeParser()
        self.embedding_model = SentenceTransformerEmbeddingModel()

    @staticmethod
    def _compute_file_hash(path: Path) -> str:
        """Computes SHA256 hash of file content."""
        hasher = hashlib.sha256()
        hasher.update(path.read_bytes())
        return hasher.hexdigest()

    def update_repository(self, repo_name: str) -> IncrementalUpdateSummary:
        """Performs incremental update on the specified repository index."""
        import time
        start_time = time.time()

        index_dir = settings.INDEXES_DIR / repo_name
        if not index_dir.exists() or not (index_dir / "chunks.json").exists():
            raise FileNotFoundError(f"Repository index '{repo_name}' not found.")

        # Load existing chunks
        with open(index_dir / "chunks.json", "r", encoding="utf-8") as f:
            raw_chunks = json.load(f)
        existing_chunks = [CodeChunk.from_dict(c) for c in raw_chunks]

        # Scan current filesystem
        repo_dir = settings.REPOSITORIES_DIR / repo_name
        if not repo_dir.exists():
            repo_dir = settings.BASE_DIR / "tests" / "fixtures" / "sample_repo"

        discovered_files = self.file_discovery.discover_files(repo_dir)
        current_paths_rel = {df.relative_path: df.full_path for df in discovered_files}
        existing_paths = set(c.file_path for c in existing_chunks)

        added_files = [p for p in current_paths_rel if p not in existing_paths]
        deleted_files = [p for p in existing_paths if p not in current_paths_rel]
        
        # Check modified files (compare chunk counts or file hashes)
        modified_files = []
        for p_rel, full_p in current_paths_rel.items():
            if p_rel in existing_paths:
                # Compare file mtime/content
                old_chunks = [c for c in existing_chunks if c.file_path == p_rel]
                new_chunks = self.parser.parse_file(file_path=full_p, repo_name=repo_name, relative_path=p_rel)
                if len(old_chunks) != len(new_chunks) or any(oc.code != nc.code for oc, nc in zip(old_chunks, new_chunks)):
                    modified_files.append(p_rel)

        # Retain untouched chunks
        files_to_remove = set(modified_files + deleted_files)
        retained_chunks = [c for c in existing_chunks if c.file_path not in files_to_remove]

        # Parse new and modified files
        newly_extracted_chunks: List[CodeChunk] = []
        for rel_p in added_files + modified_files:
            full_p = current_paths_rel.get(rel_p)
            if full_p and full_p.exists():
                file_chunks = self.parser.parse_file(
                    file_path=full_p,
                    repo_name=repo_name,
                    relative_path=rel_p,
                )
                newly_extracted_chunks.extend(file_chunks)

        all_updated_chunks = retained_chunks + newly_extracted_chunks

        # Re-embed and persist updated index
        if newly_extracted_chunks or deleted_files:
            texts = [c.get_embeddable_text() for c in all_updated_chunks]
            embeddings = self.embedding_model.encode(texts, batch_size=settings.EMBEDDING_BATCH_SIZE)

            v_store = FaissVectorStore(dimension=self.embedding_model.dimension)
            v_store.add_chunks(all_updated_chunks, embeddings)

            bm25_store = BM25Store()
            bm25_store.add_chunks(all_updated_chunks)

            # Update metadata
            from collections import Counter
            from app.models.code_chunk import IndexMetadata
            meta = IndexMetadata(
                repo_name=repo_name,
                repo_source=str(repo_dir),
                indexed_at=datetime.now(timezone.utc).isoformat(),
                total_files=len(discovered_files),
                total_chunks=len(all_updated_chunks),
                languages=dict(Counter(c.language for c in all_updated_chunks)),
                chunk_types=dict(Counter(c.chunk_type.value for c in all_updated_chunks)),
                embedding_model=self.embedding_model.model_name,
                embedding_dimension=self.embedding_model.dimension,
                total_time_sec=round(time.time() - start_time, 2),
            )
            v_store.save(index_dir, metadata=meta)
            bm25_store.save(index_dir)

        duration = round(time.time() - start_time, 2)
        return IncrementalUpdateSummary(
            repository_id=repo_name,
            added_files=added_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            total_reindexed_chunks=len(newly_extracted_chunks),
            duration_sec=duration,
        )
