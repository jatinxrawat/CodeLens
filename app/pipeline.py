"""End-to-end ingestion and indexing pipeline."""

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict
from collections import Counter
from rich.console import Console
from app.config import settings
from app.ingestion.repository import RepositoryManager
from app.ingestion.file_discovery import FileDiscovery
from app.ingestion.filters import FileFilter
from app.parsing.parser import CodeParser
from app.embeddings.embedding_model import SentenceTransformerEmbeddingModel
from app.retrieval.vector_store import FaissVectorStore
from app.retrieval.bm25_store import BM25Store
from app.models.code_chunk import IndexMetadata

console = Console()


class IngestionPipeline:
    """Coordinates the full repository ingestion, parsing, embedding, and indexing lifecycle."""

    def __init__(
        self,
        repo_manager: Optional[RepositoryManager] = None,
        file_discovery: Optional[FileDiscovery] = None,
        parser: Optional[CodeParser] = None,
        embedding_model: Optional[SentenceTransformerEmbeddingModel] = None,
    ):
        self.repo_manager = repo_manager or RepositoryManager()
        self.file_discovery = file_discovery or FileDiscovery()
        self.parser = parser or CodeParser()
        self.embedding_model = embedding_model or SentenceTransformerEmbeddingModel()

    def run_remote(self, git_url: str, force_reclone: bool = False) -> IndexMetadata:
        """Runs the pipeline for a remote git repository."""
        t0 = time.perf_counter()
        console.print(f"[bold cyan]Cloning repository:[/bold cyan] {git_url}")
        repo_name, repo_path = self.repo_manager.clone_repository(git_url, force_reclone=force_reclone)
        ingestion_time = time.perf_counter() - t0

        return self._process_repository(
            repo_name=repo_name,
            repo_path=repo_path,
            source_descriptor=git_url,
            ingestion_time_sec=ingestion_time,
        )

    def run_local(self, local_path: Path) -> IndexMetadata:
        """Runs the pipeline for a local repository directory."""
        t0 = time.perf_counter()
        console.print(f"[bold cyan]Ingesting local directory:[/bold cyan] {local_path}")
        repo_name, repo_path = self.repo_manager.prepare_local_repository(local_path)
        ingestion_time = time.perf_counter() - t0

        return self._process_repository(
            repo_name=repo_name,
            repo_path=repo_path,
            source_descriptor=str(local_path),
            ingestion_time_sec=ingestion_time,
        )

    def _process_repository(
        self,
        repo_name: str,
        repo_path: Path,
        source_descriptor: str,
        ingestion_time_sec: float,
    ) -> IndexMetadata:
        total_start = time.perf_counter()

        # 1. Discover files
        console.print("[dim]Discovering source files...[/dim]")
        discovered_files = self.file_discovery.discover_files(repo_path)
        console.print(f"Found [bold green]{len(discovered_files)}[/bold green] source files matching supported languages.")

        if not discovered_files:
            console.print(f"[yellow]No supported code files found in repository: {repo_path}. Initializing empty index.[/yellow]")
            empty_metadata = IndexMetadata(
                repo_name=repo_name,
                repo_source=source_descriptor,
                indexed_at=datetime.now(timezone.utc).isoformat(),
                total_files=0,
                total_chunks=0,
                languages={},
                chunk_types={},
                embedding_model="none",
                embedding_dimension=0,
                ingestion_time_sec=round(ingestion_time_sec, 3),
                parsing_time_sec=0.0,
                embedding_time_sec=0.0,
                indexing_time_sec=0.0,
                total_time_sec=round(time.perf_counter() - total_start + ingestion_time_sec, 3),
            )
            index_dir = settings.INDEXES_DIR / repo_name
            index_dir.mkdir(parents=True, exist_ok=True)
            with open(index_dir / "metadata.json", "w", encoding="utf-8") as f:
                f.write(empty_metadata.model_dump_json(indent=2))
            with open(index_dir / "chunks.json", "w", encoding="utf-8") as f:
                f.write("[]")
            return empty_metadata

        # Compute and cache file hashes for incremental indexing
        import hashlib
        from app.services.cache_service import cache_service
        file_hashes = {}
        for f in discovered_files:
            try:
                content = f.read_bytes()
                rel_path = str(f.relative_to(repo_path))
                file_hashes[rel_path] = hashlib.sha256(content).hexdigest()
            except Exception:
                pass
        cache_service.update_file_hashes(repo_name, file_hashes)

        # 2. Parse files into AST Code Chunks
        t_parse_start = time.perf_counter()
        console.print("[dim]Parsing source files into AST chunks...[/dim]")
        chunks = self.parser.parse_discovered_files(discovered_files, repo_name)
        parsing_time_sec = time.perf_counter() - t_parse_start
        console.print(f"Extracted [bold green]{len(chunks)}[/bold green] code chunks in {parsing_time_sec:.2f}s.")

        if not chunks:
            console.print(f"[yellow]No parseable code chunks extracted from {repo_path}. Initializing empty index.[/yellow]")
            empty_metadata = IndexMetadata(
                repo_name=repo_name,
                repo_source=source_descriptor,
                indexed_at=datetime.now(timezone.utc).isoformat(),
                total_files=len(discovered_files),
                total_chunks=0,
                languages={},
                chunk_types={},
                embedding_model="none",
                embedding_dimension=0,
                ingestion_time_sec=round(ingestion_time_sec, 3),
                parsing_time_sec=round(parsing_time_sec, 3),
                embedding_time_sec=0.0,
                indexing_time_sec=0.0,
                total_time_sec=round(time.perf_counter() - total_start + ingestion_time_sec, 3),
            )
            index_dir = settings.INDEXES_DIR / repo_name
            index_dir.mkdir(parents=True, exist_ok=True)
            with open(index_dir / "metadata.json", "w", encoding="utf-8") as f:
                f.write(empty_metadata.model_dump_json(indent=2))
            with open(index_dir / "chunks.json", "w", encoding="utf-8") as f:
                f.write("[]")
            return empty_metadata

        # Compute stats
        lang_counts = Counter(chunk.language for chunk in chunks)
        type_counts = Counter(chunk.chunk_type.value for chunk in chunks)

        # 3. Generate Local Embeddings
        t_emb_start = time.perf_counter()
        console.print(f"[dim]Generating embeddings using {self.embedding_model.model_name}...[/dim]")
        texts_to_embed = [chunk.get_embeddable_text() for chunk in chunks]
        embeddings = self.embedding_model.encode(
            texts_to_embed,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            show_progress_bar=True,
        )
        embedding_time_sec = time.perf_counter() - t_emb_start
        console.print(f"Generated {embeddings.shape[0]} embeddings ({embeddings.shape[1]} dims) in {embedding_time_sec:.2f}s.")

        # 4. Build and Save FAISS & BM25 Indexes
        t_index_start = time.perf_counter()
        console.print("[dim]Building FAISS & BM25 search indexes...[/dim]")
        vector_store = FaissVectorStore(dimension=self.embedding_model.dimension)
        vector_store.add_chunks(chunks, embeddings)

        bm25_store = BM25Store(k1=settings.BM25_K1, b=settings.BM25_B)
        bm25_store.add_chunks(chunks)

        total_time_sec = time.perf_counter() - total_start + ingestion_time_sec
        indexing_time_sec = time.perf_counter() - t_index_start

        index_metadata = IndexMetadata(
            repo_name=repo_name,
            repo_source=source_descriptor,
            indexed_at=datetime.now(timezone.utc).isoformat(),
            total_files=len(discovered_files),
            total_chunks=len(chunks),
            languages=dict(lang_counts),
            chunk_types=dict(type_counts),
            embedding_model=self.embedding_model.model_name,
            embedding_dimension=self.embedding_model.dimension,
            ingestion_time_sec=round(ingestion_time_sec, 3),
            parsing_time_sec=round(parsing_time_sec, 3),
            embedding_time_sec=round(embedding_time_sec, 3),
            indexing_time_sec=round(indexing_time_sec, 3),
            total_time_sec=round(total_time_sec, 3),
        )

        # Persist indexes to disk
        index_dir = settings.INDEXES_DIR / repo_name
        vector_store.save(index_dir, metadata=index_metadata)
        bm25_store.save(index_dir)
        console.print(f"[bold green]✓ Successfully persisted index and metadata to:[/bold green] {index_dir}")

        return index_metadata
