"""Repository ingestion and lifecycle management API router."""

from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from app.schemas.repository import (
    IngestRequest,
    IngestLocalRequest,
    IngestJobResponse,
    RepositoryStatusResponse,
    RepositorySummary,
)
from app.services.repository_service import repository_service

router = APIRouter()


@router.get("", response_model=List[RepositorySummary])
async def list_repositories():
    """Lists all indexed repositories available for search."""
    return repository_service.list_repositories()


@router.post("/ingest", response_model=IngestJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_remote_repository(request: IngestRequest):
    """Spawns an asynchronous background ingestion job for a remote GitHub repository."""
    if not request.git_url or not request.git_url.strip():
        raise HTTPException(status_code=400, detail="Invalid GitHub URL provided.")

    if not request.git_url.startswith(("http://", "https://", "git@", "ssh://")):
        raise HTTPException(status_code=400, detail="URL must start with http://, https://, or git@")

    try:
        job = repository_service.start_remote_ingestion_job(request.git_url, force=request.force)
        return IngestJobResponse(
            job_id=job.job_id,
            repository_id=job.repository_id,
            repository_name=job.repository_name,
            status=job.status,
            message=f"Ingestion job started for {request.git_url}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start ingestion job: {e}")


@router.post("/ingest-local", response_model=IngestJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_local_repository(request: IngestLocalRequest):
    """Spawns an asynchronous background ingestion job for a local directory."""
    if not request.repo_path or not request.repo_path.strip():
        raise HTTPException(status_code=400, detail="Repository path cannot be empty.")

    try:
        job = repository_service.start_local_ingestion_job(request.repo_path)
        return IngestJobResponse(
            job_id=job.job_id,
            repository_id=job.repository_id,
            repository_name=job.repository_name,
            status=job.status,
            message=f"Ingestion job started for {request.repo_path}",
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start ingestion job: {e}")


@router.get("/{repository_id}", response_model=RepositoryStatusResponse)
async def get_repository_details(repository_id: str):
    """Retrieves current status, metrics, and details for a repository."""
    status_resp = repository_service.get_repository_status(repository_id)
    if status_resp.status == "not_found":
        raise HTTPException(status_code=404, detail=f"Repository '{repository_id}' not found.")
    return status_resp


@router.get("/{repository_id}/status", response_model=RepositoryStatusResponse)
async def get_repository_status(repository_id: str):
    """Polls real-time ingestion progress for a repository."""
    return repository_service.get_repository_status(repository_id)
