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
    stage: str = Field(default="Queued", description="Current pipeline stage name")
    current_step: str = Field(default="queued", description="Technical current step key")
    progress_pct: int = Field(default=5, description="Progress percentage (0-100)")
    message: str


class RepositoryStatusResponse(BaseModel):
    repository_id: str
    repository_name: str
    source: str
    status: str = Field(..., description="'ready', 'ingesting', 'failed', 'not_found'")
    stage: str = Field(default="Ready", description="Human-readable pipeline stage name")
    current_step: Optional[str] = "ready"  # 'queued', 'cloning', 'parsing', 'embedding', 'indexing', 'ready', 'failed'
    progress_pct: int = Field(default=100, description="Progress percentage 0-100")
    message: Optional[str] = Field(default=None, description="Detailed explanatory message")
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
