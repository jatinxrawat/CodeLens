"""Repos API router for instant analysis and progress polling."""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field
from typing import Optional
from app.services.repository_service import repository_service
from app.ingestion.repository import RepositoryManager
from app.schemas.repository import RepositoryStatusResponse

router = APIRouter(prefix="/repos", tags=["Repos"])


class AnalyzeRepoRequest(BaseModel):
    url: Optional[str] = Field(None, description="GitHub repository URL or owner/repo (e.g. 'pallets/click' or 'https://github.com/pallets/click')")
    git_url: Optional[str] = Field(None, description="Alternative git URL field")
    force: bool = Field(False, description="Force re-clone and re-index")


class AnalyzeRepoResponse(BaseModel):
    repo_id: str
    job_id: str
    status: str
    stage: str = "Queued"
    current_step: str = "queued"
    message: str
    progress_pct: int = 5


@router.post("/analyze", response_model=AnalyzeRepoResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_repo(request: AnalyzeRepoRequest, background_tasks: BackgroundTasks):
    """Takes a GitHub URL or owner/repo shorthand, normalizes it, and starts background ingestion."""
    target_url = request.url or request.git_url
    if not target_url or not target_url.strip():
        raise HTTPException(status_code=400, detail="Repository URL must be provided.")

    target_url = target_url.strip()
    try:
        normalized_url = RepositoryManager.normalize_clone_url(target_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        job = repository_service.start_remote_ingestion_job(
            normalized_url, force=request.force, background_tasks=background_tasks
        )
        return AnalyzeRepoResponse(
            repo_id=job.repository_id,
            job_id=job.job_id,
            status=job.status,
            stage=job.stage,
            current_step=job.current_step,
            message=job.message or f"Indexing queued for {normalized_url}",
            progress_pct=job.progress_pct,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate repo analysis: {e}")


@router.get("/{repo_id}/status", response_model=RepositoryStatusResponse)
async def get_repo_status(repo_id: str):
    """Polls real-time ingestion progress for a repository."""
    return repository_service.get_repository_status(repo_id)


@router.get("/{repo_id}", response_model=RepositoryStatusResponse)
async def get_repo_details(repo_id: str):
    """Retrieves repository metadata and ready index stats."""
    status_resp = repository_service.get_repository_status(repo_id)
    if status_resp.status == "not_found":
        raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found.")
    return status_resp
