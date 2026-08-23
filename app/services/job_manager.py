"""Thread-safe background ingestion job manager and lifecycle tracker."""

import time
import uuid
import threading
from typing import Dict, Optional, Any
from pydantic import BaseModel


class IngestionJob(BaseModel):
    job_id: str
    repository_id: str
    repository_name: str
    source: str
    status: str  # 'queued', 'running', 'completed', 'failed'
    current_step: str  # 'initializing', 'cloning', 'discovering', 'parsing', 'embedding', 'indexing', 'ready'
    progress_pct: int
    error: Optional[str] = None
    created_at: float
    updated_at: float
    duration_sec: float = 0.0


class IngestionJobManager:
    """Manages asynchronous background ingestion jobs."""

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
            current_step="initializing",
            progress_pct=0,
            error=None,
            created_at=now,
            updated_at=now,
            duration_sec=0.0,
        )
        with self._lock:
            self._jobs[job_id] = job
        return job

    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        current_step: Optional[str] = None,
        progress_pct: Optional[int] = None,
        error: Optional[str] = None,
    ):
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            now = time.time()
            if status:
                job.status = status
            if current_step:
                job.current_step = current_step
            if progress_pct is not None:
                job.progress_pct = progress_pct
            if error:
                job.error = error
                job.status = "failed"
            job.updated_at = now
            job.duration_sec = round(now - job.created_at, 2)

    def get_job(self, job_id: str) -> Optional[IngestionJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def get_latest_job_for_repo(self, repo_name: str) -> Optional[IngestionJob]:
        with self._lock:
            matching = [j for j in self._jobs.values() if j.repository_name == repo_name]
            if not matching:
                return None
            return sorted(matching, key=lambda j: j.created_at, reverse=True)[0]


job_manager = IngestionJobManager()
