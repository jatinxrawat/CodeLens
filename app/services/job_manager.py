"""Thread-safe background ingestion job manager and lifecycle tracker."""

import time
import uuid
import threading
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
from app.services.cache_service import cache_service

# Standard stages and default metadata
STAGE_METADATA: Dict[str, Dict[str, Any]] = {
    "queued": {
        "stage": "Queued",
        "progress_pct": 5,
        "message": "Job queued for analysis...",
    },
    "cloning": {
        "stage": "Cloning",
        "progress_pct": 15,
        "message": "Cloning repository from GitHub (depth=1)...",
    },
    "parsing": {
        "stage": "Parsing AST",
        "progress_pct": 40,
        "message": "Scanning code files and extracting AST symbols...",
    },
    "embedding": {
        "stage": "Generating Embeddings",
        "progress_pct": 65,
        "message": "Generating vector embeddings (downloading embedding model on first run, this may take a moment)...",
    },
    "indexing": {
        "stage": "Building Indices",
        "progress_pct": 85,
        "message": "Building FAISS vector index and BM25 search stores...",
    },
    "done": {
        "stage": "Ready",
        "progress_pct": 100,
        "message": "Repository analysis complete! Ready for exploration.",
    },
    "ready": {
        "stage": "Ready",
        "progress_pct": 100,
        "message": "Repository analysis complete! Ready for exploration.",
    },
    "completed": {
        "stage": "Ready",
        "progress_pct": 100,
        "message": "Repository analysis complete! Ready for exploration.",
    },
    "failed": {
        "stage": "Failed",
        "progress_pct": 0,
        "message": "Analysis failed.",
    },
}


class IngestionJob(BaseModel):
    job_id: str
    repository_id: str
    repository_name: str
    source: str
    status: str  # 'queued', 'cloning', 'parsing', 'embedding', 'indexing', 'done', 'failed', 'running', 'completed'
    current_step: str  # 'queued', 'cloning', 'parsing', 'embedding', 'indexing', 'done', 'failed'
    stage: str = "Queued"
    progress_pct: int = 5
    message: Optional[str] = "Job queued for analysis..."
    error: Optional[str] = None
    created_at: float
    updated_at: float
    duration_sec: float = 0.0


class IngestionJobManager:
    """Manages asynchronous background ingestion jobs with in-memory tracking and SQLite persistence."""

    def __init__(self):
        self._jobs: Dict[str, IngestionJob] = {}
        self._lock = threading.Lock()

    def create_job(self, repo_name: str, source: str) -> IngestionJob:
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        now = time.time()
        job = IngestionJob(
            job_id=job_id,
            repository_id=repo_name,
            repository_name=repo_name,
            source=source,
            status="queued",
            current_step="queued",
            stage=STAGE_METADATA["queued"]["stage"],
            progress_pct=STAGE_METADATA["queued"]["progress_pct"],
            message=STAGE_METADATA["queued"]["message"],
            error=None,
            created_at=now,
            updated_at=now,
            duration_sec=0.0,
        )
        with self._lock:
            self._jobs[job_id] = job
        cache_service.save_job(job.model_dump())
        return job

    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        current_step: Optional[str] = None,
        stage: Optional[str] = None,
        progress_pct: Optional[int] = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[IngestionJob]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                cached = cache_service.get_job(job_id)
                if cached:
                    job = IngestionJob(**cached)
                    self._jobs[job_id] = job
                else:
                    return None

            now = time.time()
            if status:
                job.status = status
            if current_step:
                job.current_step = current_step

            # Infer defaults from STAGE_METADATA if not provided
            meta_key = current_step or status
            stage_defaults = STAGE_METADATA.get(meta_key, {})

            if stage is not None:
                job.stage = stage
            elif "stage" in stage_defaults and not job.stage:
                job.stage = stage_defaults["stage"]
            elif current_step and current_step in STAGE_METADATA:
                job.stage = STAGE_METADATA[current_step]["stage"]

            if progress_pct is not None:
                job.progress_pct = max(0, min(100, progress_pct))
            elif current_step and current_step in STAGE_METADATA:
                job.progress_pct = STAGE_METADATA[current_step]["progress_pct"]

            if message is not None:
                job.message = message
            elif current_step and current_step in STAGE_METADATA:
                job.message = STAGE_METADATA[current_step]["message"]

            if error:
                job.error = error
                job.status = "failed"
                job.current_step = "failed"
                job.stage = "Failed"
                if progress_pct is None:
                    job.progress_pct = 0
                if not message:
                    job.message = error

            job.updated_at = now
            job.duration_sec = round(now - job.created_at, 2)
            updated_dict = job.model_dump()

        cache_service.save_job(updated_dict)
        return job

    def get_job(self, job_id: str) -> Optional[IngestionJob]:
        with self._lock:
            if job_id in self._jobs:
                return self._jobs[job_id]

        cached = cache_service.get_job(job_id)
        if cached:
            try:
                job = IngestionJob(**cached)
                with self._lock:
                    self._jobs[job_id] = job
                return job
            except Exception:
                return None
        return None

    def get_latest_job_for_repo(self, repo_name: str) -> Optional[IngestionJob]:
        with self._lock:
            matching = [
                j for j in self._jobs.values()
                if j.repository_name == repo_name or j.repository_id == repo_name
            ]
            if matching:
                return sorted(matching, key=lambda j: j.created_at, reverse=True)[0]

        cached = cache_service.get_latest_job_for_repo(repo_name)
        if cached:
            try:
                job = IngestionJob(**cached)
                with self._lock:
                    self._jobs[job.job_id] = job
                return job
            except Exception:
                return None
        return None


job_manager = IngestionJobManager()
