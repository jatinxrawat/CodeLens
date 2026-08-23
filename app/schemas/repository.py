"""Pydantic schemas for repository ingestion and status."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    git_url: str = Field(..., description="GitHub or Git repository URL (e.g. https://github.com/user/repo.git)")
    force: bool = Field(default=False, description="Force re-clone if directory already exists")


class IngestLocalRequest(BaseModel):
    repo_path: str = Field(..., description="Local directory path to ingest")


class IngestJobResponse(BaseModel):
    job_id: str
    repository_id: str
    repository_name: str
    status: str = Field(..., description="Job status: 'queued', 'running', 'completed', 'failed'")
    message: str


class RepositoryStatusResponse(BaseModel):
    repository_id: str
    repository_name: str
    source: str
    status: str = Field(..., description="'ready', 'ingesting', 'failed', 'not_found'")
    current_step: Optional[str] = None  # 'cloning', 'discovering', 'parsing', 'embedding', 'indexing', 'ready'
    progress_pct: Optional[int] = None
    total_files: int = 0
    total_chunks: int = 0
    languages: Dict[str, int] = {}
    ingestion_duration_sec: float = 0.0
    error: Optional[str] = None


class RepositorySummary(BaseModel):
    repository_id: str
    repository_name: str
    source: str
    indexed_at: str
    total_files: int
    total_chunks: int
    languages: Dict[str, int]
