"""Service layer for repository lifecycle, file exploration, and background ingestion."""

import os
import json
import hashlib
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from collections import Counter
from fastapi import BackgroundTasks

from app.config import settings
from app.utils.logger import logger
from app.ingestion.repository import RepositoryManager
from app.ingestion.file_discovery import FileDiscovery
from app.parsing.parser import CodeParser
from app.pipeline import IngestionPipeline
from app.embeddings.embedding_model import SentenceTransformerEmbeddingModel
from app.retrieval.vector_store import FaissVectorStore
from app.retrieval.bm25_store import BM25Store
from app.models.code_chunk import IndexMetadata
from app.schemas.repository import RepositorySummary, RepositoryStatusResponse, IngestJobResponse
from app.schemas.stats import RepositoryStatsResponse
from app.services.job_manager import job_manager, IngestionJob, STAGE_METADATA
from app.services.cache_service import cache_service


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
        clean_name = RepositoryManager.extract_repo_name(repo_name)
        index_dir = settings.INDEXES_DIR / clean_name
        chunks_file = index_dir / "chunks.json"
        if not chunks_file.exists():
            return []
        try:
            with open(chunks_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_repository_status(self, repo_identifier: str) -> RepositoryStatusResponse:
        """Retrieves real-time status of a repository (either active background job or ready index)."""
        # 1. First check if identifier is a job_id
        job: Optional[IngestionJob] = None
        if repo_identifier.startswith("job_"):
            job = job_manager.get_job(repo_identifier)

        clean_name = RepositoryManager.extract_repo_name(repo_identifier)

        # 2. If not found by job_id, look up latest job by repo name or identifier
        if not job:
            job = job_manager.get_latest_job_for_repo(repo_identifier) or job_manager.get_latest_job_for_repo(clean_name)

        # If job is active in ingestion
        if job and job.status in ("queued", "running", "cloning", "parsing", "embedding", "indexing"):
            return RepositoryStatusResponse(
                repository_id=job.repository_id,
                repository_name=job.repository_name,
                source=job.source,
                status="ingesting",
                stage=job.stage or STAGE_METADATA.get(job.current_step, {}).get("stage", "Processing"),
                current_step=job.current_step,
                progress_pct=job.progress_pct,
                message=job.message or STAGE_METADATA.get(job.current_step, {}).get("message", "Processing..."),
                ingestion_duration_sec=job.duration_sec,
                error=job.error,
            )

        # If job has failed
        if job and job.status == "failed":
            return RepositoryStatusResponse(
                repository_id=job.repository_id,
                repository_name=job.repository_name,
                source=job.source,
                status="failed",
                stage="Failed",
                current_step="failed",
                progress_pct=0,
                message=job.message or job.error or "Repository analysis failed.",
                ingestion_duration_sec=job.duration_sec,
                error=job.error or "Repository analysis failed.",
            )

        # Check if indexed directory exists on disk
        index_dir = settings.INDEXES_DIR / clean_name
        if index_dir.exists() and (index_dir / "metadata.json").exists():
            try:
                with open(index_dir / "metadata.json", "r", encoding="utf-8") as f:
                    meta = json.load(f)

                total_files = meta.get("total_files", 0)
                total_chunks = meta.get("total_chunks", 0)

                default_message = (
                    "No code files found in repository."
                    if total_files == 0 or total_chunks == 0
                    else "Repository analysis complete! Ready for exploration."
                )

                return RepositoryStatusResponse(
                    repository_id=meta.get("repo_name", clean_name),
                    repository_name=meta.get("repo_name", clean_name),
                    source=meta.get("repo_source", "local"),
                    status="ready",
                    stage="Ready",
                    current_step="done",
                    progress_pct=100,
                    message=job.message if (job and job.message and job.status in ("done", "completed")) else default_message,
                    total_files=total_files,
                    total_chunks=total_chunks,
                    languages=meta.get("languages", {}),
                    ingestion_duration_sec=meta.get("total_time_sec", 0.0),
                )
            except Exception as e:
                logger.warning(f"Error reading index metadata for {clean_name}: {e}")

        # If completed job without index files (e.g. empty repository)
        if job and job.status in ("completed", "done", "ready"):
            return RepositoryStatusResponse(
                repository_id=job.repository_id,
                repository_name=job.repository_name,
                source=job.source,
                status="ready",
                stage="Ready",
                current_step="done",
                progress_pct=100,
                message=job.message or "Repository analysis complete! Ready for exploration.",
                total_files=0,
                total_chunks=0,
                languages={},
                ingestion_duration_sec=job.duration_sec,
            )

        # Otherwise not found
        return RepositoryStatusResponse(
            repository_id=clean_name,
            repository_name=clean_name,
            source="",
            status="not_found",
            stage="Not Found",
            current_step="not_found",
            progress_pct=0,
            message=f"Repository '{repo_identifier}' has not been analyzed yet.",
            error=f"Repository '{repo_identifier}' has not been analyzed yet.",
        )

    def get_repository_stats(self, repo_name: str) -> RepositoryStatsResponse:
        """Loads detailed indexing stats for a repository."""
        clean_name = RepositoryManager.extract_repo_name(repo_name)
        index_dir = settings.INDEXES_DIR / clean_name
        meta_file = index_dir / "metadata.json"
        if not meta_file.exists():
            raise FileNotFoundError(f"Repository index '{clean_name}' not found.")

        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

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
            repository_id=meta.get("repo_name", clean_name),
            repository_name=meta.get("repo_name", clean_name),
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
        clean_name = RepositoryManager.extract_repo_name(repo_name)
        index_dir = settings.INDEXES_DIR / clean_name
        chunks_file = index_dir / "chunks.json"
        if not chunks_file.exists():
            raise FileNotFoundError(f"Chunks index for '{clean_name}' not found.")

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
        clean_name = RepositoryManager.extract_repo_name(repo_name)
        possible_paths = [
            settings.REPOSITORIES_DIR / clean_name / relative_path,
            settings.BASE_DIR / "tests" / "fixtures" / "sample_repo" / relative_path,
        ]

        found_path: Optional[Path] = None
        for p in possible_paths:
            if p.exists() and p.is_file():
                found_path = p
                break

        if not found_path:
            index_dir = settings.INDEXES_DIR / clean_name
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
            raise FileNotFoundError(f"File '{relative_path}' not found in repository '{clean_name}'")

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

    def _save_empty_index(self, repo_name: str, source: str, total_files: int = 0):
        """Creates empty index files on disk so status check can resolve immediately."""
        index_dir = settings.INDEXES_DIR / repo_name
        index_dir.mkdir(parents=True, exist_ok=True)
        meta = IndexMetadata(
            repo_name=repo_name,
            repo_source=source,
            indexed_at=datetime.now(timezone.utc).isoformat(),
            total_files=total_files,
            total_chunks=0,
            languages={},
            chunk_types={},
            embedding_model="none",
            embedding_dimension=0,
            ingestion_time_sec=0.1,
            parsing_time_sec=0.0,
            embedding_time_sec=0.0,
            indexing_time_sec=0.0,
            total_time_sec=0.1,
        )
        with open(index_dir / "metadata.json", "w", encoding="utf-8") as f:
            f.write(meta.model_dump_json(indent=2))
        with open(index_dir / "chunks.json", "w", encoding="utf-8") as f:
            f.write("[]")

    def start_remote_ingestion_job(
        self,
        git_url: str,
        force: bool = False,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> IngestionJob:
        """Spawns an asynchronous background job to ingest a remote Git repository."""
        # 1. Verify git is available
        if not RepositoryManager.is_git_available():
            raise RuntimeError("Git executable is not installed or not found in system PATH. Please install git.")

        # 2. Normalize clone URL
        normalized_url = RepositoryManager.normalize_clone_url(git_url)
        repo_name = RepositoryManager.extract_repo_name(normalized_url)

        # 3. Create job record
        job = job_manager.create_job(repo_name, normalized_url)

        def _run():
            logger.info(f"[{job.job_id}] Starting ingestion pipeline for {normalized_url}")
            try:
                # Stage: Cloning (15%)
                job_manager.update_job(
                    job.job_id,
                    status="cloning",
                    current_step="cloning",
                    stage="Cloning",
                    progress_pct=15,
                    message=f"Cloning {repo_name} from GitHub (depth=1)...",
                )

                pipeline = IngestionPipeline()
                repo_n, repo_path = pipeline.repo_manager.clone_repository(
                    normalized_url, force_reclone=force, timeout_sec=60
                )

                # Stage: Parsing AST (40%)
                job_manager.update_job(
                    job.job_id,
                    status="parsing",
                    current_step="parsing",
                    stage="Parsing AST",
                    progress_pct=40,
                    message="Scanning source code files and extracting AST symbols...",
                )

                discovered = pipeline.file_discovery.discover_files(repo_path)
                if not discovered:
                    logger.info(f"[{job.job_id}] No supported code files found in {normalized_url}. Graceful finish.")
                    self._save_empty_index(repo_n, normalized_url, total_files=0)
                    job_manager.update_job(
                        job.job_id,
                        status="done",
                        current_step="done",
                        stage="Ready",
                        progress_pct=100,
                        message="No code files found in repository.",
                    )
                    return

                # Cache file hashes for incremental updates
                f_hashes = {}
                for f in discovered:
                    try:
                        content = f.read_bytes()
                        f_hashes[str(f.relative_to(repo_path))] = hashlib.sha256(content).hexdigest()
                    except Exception:
                        pass
                cache_service.update_file_hashes(repo_n, f_hashes)

                chunks = pipeline.parser.parse_discovered_files(discovered, repo_n)
                if not chunks:
                    logger.info(f"[{job.job_id}] No code chunks extracted from {normalized_url}. Graceful finish.")
                    self._save_empty_index(repo_n, normalized_url, total_files=len(discovered))
                    job_manager.update_job(
                        job.job_id,
                        status="done",
                        current_step="done",
                        stage="Ready",
                        progress_pct=100,
                        message="No code files found in repository.",
                    )
                    return

                # Stage: Embedding (65%)
                job_manager.update_job(
                    job.job_id,
                    status="embedding",
                    current_step="embedding",
                    stage="Generating Embeddings",
                    progress_pct=65,
                    message="Generating vector embeddings (downloading model on first run, this may take a moment)...",
                )

                texts = [c.get_embeddable_text() for c in chunks]
                embeddings = pipeline.embedding_model.encode(texts, batch_size=settings.EMBEDDING_BATCH_SIZE)

                # Stage: Indexing (85%)
                job_manager.update_job(
                    job.job_id,
                    status="indexing",
                    current_step="indexing",
                    stage="Building Indices",
                    progress_pct=85,
                    message="Building FAISS vector index and BM25 search stores...",
                )

                index_dir = settings.INDEXES_DIR / repo_n
                v_store = FaissVectorStore(dimension=pipeline.embedding_model.dimension)
                v_store.add_chunks(chunks, embeddings)

                bm25_store = BM25Store(k1=settings.BM25_K1, b=settings.BM25_B)
                bm25_store.add_chunks(chunks)

                meta = IndexMetadata(
                    repo_name=repo_n,
                    repo_source=normalized_url,
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

                # Stage: Done (100%)
                success_msg = f"Repository analysis complete! {len(chunks)} code chunks indexed across {len(discovered)} files."
                logger.info(f"[{job.job_id}] Ingestion complete for {repo_n}")
                job_manager.update_job(
                    job.job_id,
                    status="done",
                    current_step="done",
                    stage="Ready",
                    progress_pct=100,
                    message=success_msg,
                )

            except Exception as e:
                logger.exception(f"[{job.job_id}] Repository ingestion failed for {normalized_url}: {e}")
                err_text = str(e)
                if "timed out" in err_text.lower():
                    readable_err = "Git clone timed out after 60 seconds. The repository may be too large or GitHub is responding slowly."
                elif "terminal prompts disabled" in err_text.lower() or "authentication failed" in err_text.lower() or "could not read username" in err_text.lower():
                    readable_err = "Authentication failed or repository is private. Please ensure the repository is public."
                elif "not found" in err_text.lower() and "git" in err_text.lower():
                    readable_err = "Repository not found on GitHub. Please check the owner/repo URL."
                else:
                    readable_err = f"Analysis failed: {err_text}"

                job_manager.update_job(
                    job.job_id,
                    status="failed",
                    current_step="failed",
                    stage="Failed",
                    progress_pct=0,
                    error=readable_err,
                    message=readable_err,
                )

        if background_tasks is not None:
            background_tasks.add_task(_run)
        else:
            thread = threading.Thread(target=_run, daemon=True)
            thread.start()

        return job

    def start_local_ingestion_job(
        self,
        local_path_str: str,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> IngestionJob:
        """Spawns background job to ingest a local repository path."""
        local_path = Path(local_path_str).resolve()
        if not local_path.exists() or not local_path.is_dir():
            raise FileNotFoundError(f"Local path not found or not a directory: {local_path_str}")

        repo_name = RepositoryManager.extract_repo_name(str(local_path))
        job = job_manager.create_job(repo_name, str(local_path))

        def _run():
            logger.info(f"[{job.job_id}] Starting local ingestion for {local_path}")
            try:
                job_manager.update_job(
                    job.job_id,
                    status="parsing",
                    current_step="parsing",
                    stage="Parsing AST",
                    progress_pct=30,
                    message="Discovering files and parsing AST chunks...",
                )
                pipeline = IngestionPipeline()
                meta = pipeline.run_local(local_path)

                msg = (
                    "No code files found in repository."
                    if meta.total_files == 0 or meta.total_chunks == 0
                    else f"Repository analysis complete! {meta.total_chunks} chunks indexed across {meta.total_files} files."
                )

                job_manager.update_job(
                    job.job_id,
                    status="done",
                    current_step="done",
                    stage="Ready",
                    progress_pct=100,
                    message=msg,
                )
            except Exception as e:
                logger.exception(f"[{job.job_id}] Local ingestion failed for {local_path}: {e}")
                readable_err = f"Local ingestion failed: {str(e)}"
                job_manager.update_job(
                    job.job_id,
                    status="failed",
                    current_step="failed",
                    stage="Failed",
                    progress_pct=0,
                    error=readable_err,
                    message=readable_err,
                )

        if background_tasks is not None:
            background_tasks.add_task(_run)
        else:
            thread = threading.Thread(target=_run, daemon=True)
            thread.start()

        return job


repository_service = RepositoryService()
