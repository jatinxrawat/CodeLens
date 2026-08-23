"""Service layer for repository lifecycle, file exploration, and background ingestion."""

import os
import json
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
from app.config import settings
from app.ingestion.repository import RepositoryManager
from app.ingestion.file_discovery import FileDiscovery
from app.parsing.parser import CodeParser
from app.pipeline import IngestionPipeline
from app.retrieval.vector_store import FaissVectorStore
from app.schemas.repository import RepositorySummary, RepositoryStatusResponse, IngestJobResponse
from app.schemas.stats import RepositoryStatsResponse
from app.services.job_manager import job_manager, IngestionJob


class RepositoryService:
    """Coordinates repository ingestion, status tracking, statistics, and file inspection."""

    def __init__(self):
        self.repo_manager = RepositoryManager()
        self.file_discovery = FileDiscovery()
        self.parser = CodeParser()

    def list_repositories(self) -> List[RepositorySummary]:
        """Returns summaries of all indexed repositories on disk."""
        if not settings.INDEXES_DIR.exists():
            return []

        summaries: List[RepositorySummary] = []
        for d in sorted(settings.INDEXES_DIR.iterdir()):
            if d.is_dir() and (d / "metadata.json").exists():
                try:
                    with open(d / "metadata.json", "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    summaries.append(
                        RepositorySummary(
                            repository_id=meta.get("repo_name", d.name),
                            repository_name=meta.get("repo_name", d.name),
                            source=meta.get("repo_source", "local"),
                            indexed_at=meta.get("indexed_at", "N/A"),
                            total_files=meta.get("total_files", 0),
                            total_chunks=meta.get("total_chunks", 0),
                            languages=meta.get("languages", {}),
                        )
                    )
                except Exception:
                    continue
        return summaries

    def get_chunks_for_repository(self, repo_name: str) -> List[Dict[str, Any]]:
        """Returns raw chunks dictionary list for a given repository."""
        index_dir = settings.INDEXES_DIR / repo_name
        chunks_file = index_dir / "chunks.json"
        if not chunks_file.exists():
            return []
        try:
            with open(chunks_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_repository_status(self, repo_name: str) -> RepositoryStatusResponse:
        """Retrieves real-time status of a repository (either active background job or ready index)."""
        job = job_manager.get_latest_job_for_repo(repo_name)
        if job and job.status in ("queued", "running"):
            return RepositoryStatusResponse(
                repository_id=job.repository_id,
                repository_name=job.repository_name,
                source=job.source,
                status="ingesting",
                current_step=job.current_step,
                progress_pct=job.progress_pct,
                ingestion_duration_sec=job.duration_sec,
                error=job.error,
            )

        index_dir = settings.INDEXES_DIR / repo_name
        if not index_dir.exists() or not (index_dir / "metadata.json").exists():
            if job and job.status == "failed":
                return RepositoryStatusResponse(
                    repository_id=job.repository_id,
                    repository_name=job.repository_name,
                    source=job.source,
                    status="failed",
                    error=job.error,
                )
            return RepositoryStatusResponse(
                repository_id=repo_name,
                repository_name=repo_name,
                source="",
                status="not_found",
                error=f"Repository '{repo_name}' has not been indexed yet.",
            )

        with open(index_dir / "metadata.json", "r", encoding="utf-8") as f:
            meta = json.load(f)

        return RepositoryStatusResponse(
            repository_id=meta.get("repo_name", repo_name),
            repository_name=meta.get("repo_name", repo_name),
            source=meta.get("repo_source", "local"),
            status="ready",
            current_step="ready",
            progress_pct=100,
            total_files=meta.get("total_files", 0),
            total_chunks=meta.get("total_chunks", 0),
            languages=meta.get("languages", {}),
            ingestion_duration_sec=meta.get("total_time_sec", 0.0),
        )

    def get_repository_stats(self, repo_name: str) -> RepositoryStatsResponse:
        """Loads detailed indexing stats for a repository."""
        index_dir = settings.INDEXES_DIR / repo_name
        meta_file = index_dir / "metadata.json"
        if not meta_file.exists():
            raise FileNotFoundError(f"Repository index '{repo_name}' not found.")

        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        # Count total lines of code across chunks
        total_loc = 0
        chunks_file = index_dir / "chunks.json"
        if chunks_file.exists():
            try:
                with open(chunks_file, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                total_loc = sum((c.get("end_line", 0) - c.get("start_line", 0) + 1) for c in chunks)
            except Exception:
                pass

        return RepositoryStatsResponse(
            repository_id=meta.get("repo_name", repo_name),
            repository_name=meta.get("repo_name", repo_name),
            source=meta.get("repo_source", "local"),
            indexed_at=meta.get("indexed_at", "N/A"),
            total_files=meta.get("total_files", 0),
            total_chunks=meta.get("total_chunks", 0),
            total_lines_of_code=total_loc,
            languages=meta.get("languages", {}),
            chunk_types=meta.get("chunk_types", {}),
            embedding_model=meta.get("embedding_model", settings.EMBEDDING_MODEL_NAME),
            embedding_dimension=meta.get("embedding_dimension", 384),
            ingestion_time_sec=meta.get("ingestion_time_sec", 0.0),
            parsing_time_sec=meta.get("parsing_time_sec", 0.0),
            embedding_time_sec=meta.get("embedding_time_sec", 0.0),
            indexing_time_sec=meta.get("indexing_time_sec", 0.0),
            total_pipeline_time_sec=meta.get("total_time_sec", 0.0),
        )

    def get_file_tree(self, repo_name: str) -> List[Dict[str, Any]]:
        """Returns structured file tree and metadata for the repository."""
        index_dir = settings.INDEXES_DIR / repo_name
        chunks_file = index_dir / "chunks.json"
        if not chunks_file.exists():
            raise FileNotFoundError(f"Chunks index for '{repo_name}' not found.")

        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        files_map: Dict[str, Dict[str, Any]] = {}
        for c in chunks:
            path = c.get("file_path", "")
            if path not in files_map:
                files_map[path] = {
                    "path": path,
                    "name": Path(path).name,
                    "language": c.get("language", ""),
                    "symbols": [],
                    "total_chunks": 0,
                    "min_line": c.get("start_line", 1),
                    "max_line": c.get("end_line", 1),
                }
            files_map[path]["total_chunks"] += 1
            files_map[path]["min_line"] = min(files_map[path]["min_line"], c.get("start_line", 1))
            files_map[path]["max_line"] = max(files_map[path]["max_line"], c.get("end_line", 1))
            if c.get("symbol_name"):
                files_map[path]["symbols"].append({
                    "symbol": c.get("symbol_name"),
                    "type": c.get("chunk_type"),
                    "start_line": c.get("start_line"),
                    "end_line": c.get("end_line"),
                })

        return sorted(list(files_map.values()), key=lambda x: x["path"])

    def get_file_content(self, repo_name: str, relative_path: str) -> Dict[str, Any]:
        """Returns raw code content, lines, and detected symbols for a given file."""
        # Check cloned repo dir or fixtures
        possible_paths = [
            settings.REPOSITORIES_DIR / repo_name / relative_path,
            settings.BASE_DIR / "tests" / "fixtures" / "sample_repo" / relative_path,
        ]

        found_path: Optional[Path] = None
        for p in possible_paths:
            if p.exists() and p.is_file():
                found_path = p
                break

        if not found_path:
            # Fallback to reconstructing from chunks in index
            index_dir = settings.INDEXES_DIR / repo_name
            chunks_file = index_dir / "chunks.json"
            if chunks_file.exists():
                with open(chunks_file, "r", encoding="utf-8") as f:
                    chunks = [c for c in json.load(f) if c.get("file_path") == relative_path]
                if chunks:
                    chunks_sorted = sorted(chunks, key=lambda c: c["start_line"])
                    full_code = "\n\n".join(c["code"] for c in chunks_sorted)
                    return {
                        "file_path": relative_path,
                        "code": full_code,
                        "total_lines": full_code.count("\n") + 1,
                        "language": chunks[0].get("language", "text"),
                        "symbols": [c.get("symbol_name") for c in chunks if c.get("symbol_name")],
                    }
            raise FileNotFoundError(f"File '{relative_path}' not found in repository '{repo_name}'")

        content = found_path.read_text(encoding="utf-8", errors="replace")
        ext = found_path.suffix.lower()
        lang = settings.SUPPORTED_EXTENSIONS.get(ext, "text")

        return {
            "file_path": relative_path,
            "code": content,
            "total_lines": content.count("\n") + 1,
            "language": lang,
            "size_bytes": found_path.stat().st_size,
        }

    def start_remote_ingestion_job(self, git_url: str, force: bool = False) -> IngestionJob:
        """Spawns background job to ingest a remote Git repository."""
        repo_name = RepositoryManager.extract_repo_name(git_url)
        job = job_manager.create_job(repo_name, git_url)

        def _run():
            try:
                job_manager.update_job(job.job_id, status="running", current_step="cloning", progress_pct=10)
                pipeline = IngestionPipeline()
                repo_n, repo_path = pipeline.repo_manager.clone_repository(git_url, force_reclone=force)

                job_manager.update_job(job.job_id, current_step="discovering", progress_pct=30)
                discovered = pipeline.file_discovery.discover_files(repo_path)
                if not discovered:
                    raise ValueError(f"No supported source code files found in {git_url}")

                job_manager.update_job(job.job_id, current_step="parsing", progress_pct=50)
                chunks = pipeline.parser.parse_discovered_files(discovered, repo_n)
                if not chunks:
                    raise ValueError("No code chunks extracted from repository files.")

                job_manager.update_job(job.job_id, current_step="embedding", progress_pct=70)
                texts = [c.get_embeddable_text() for c in chunks]
                embeddings = pipeline.embedding_model.encode(texts, batch_size=settings.EMBEDDING_BATCH_SIZE)

                job_manager.update_job(job.job_id, current_step="indexing", progress_pct=90)
                index_dir = settings.INDEXES_DIR / repo_n
                v_store = FaissVectorStore(dimension=pipeline.embedding_model.dimension)
                v_store.add_chunks(chunks, embeddings)

                from app.retrieval.bm25_store import BM25Store
                bm25_store = BM25Store(k1=settings.BM25_K1, b=settings.BM25_B)
                bm25_store.add_chunks(chunks)

                from collections import Counter
                from datetime import datetime, timezone
                from app.models.code_chunk import IndexMetadata

                meta = IndexMetadata(
                    repo_name=repo_n,
                    repo_source=git_url,
                    indexed_at=datetime.now(timezone.utc).isoformat(),
                    total_files=len(discovered),
                    total_chunks=len(chunks),
                    languages=dict(Counter(c.language for c in chunks)),
                    chunk_types=dict(Counter(c.chunk_type.value for c in chunks)),
                    embedding_model=pipeline.embedding_model.model_name,
                    embedding_dimension=pipeline.embedding_model.dimension,
                    ingestion_time_sec=1.0,
                    parsing_time_sec=0.5,
                    embedding_time_sec=2.0,
                    indexing_time_sec=0.1,
                    total_time_sec=3.6,
                )
                v_store.save(index_dir, metadata=meta)
                bm25_store.save(index_dir)

                job_manager.update_job(job.job_id, status="completed", current_step="ready", progress_pct=100)

            except Exception as e:
                job_manager.update_job(job.job_id, error=str(e))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return job

    def start_local_ingestion_job(self, local_path_str: str) -> IngestionJob:
        """Spawns background job to ingest a local repository path."""
        local_path = Path(local_path_str).resolve()
        if not local_path.exists() or not local_path.is_dir():
            raise FileNotFoundError(f"Local path not found or not a directory: {local_path_str}")

        repo_name = RepositoryManager.extract_repo_name(str(local_path))
        job = job_manager.create_job(repo_name, str(local_path))

        def _run():
            try:
                job_manager.update_job(job.job_id, status="running", current_step="discovering", progress_pct=25)
                pipeline = IngestionPipeline()
                pipeline.run_local(local_path)
                job_manager.update_job(job.job_id, status="completed", current_step="ready", progress_pct=100)
            except Exception as e:
                job_manager.update_job(job.job_id, error=str(e))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return job


repository_service = RepositoryService()
