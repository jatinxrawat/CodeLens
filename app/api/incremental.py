"""Incremental Repository Update API router."""

from fastapi import APIRouter, HTTPException
from app.ingestion.incremental_updater import IncrementalUpdater, IncrementalUpdateSummary

router = APIRouter()
updater = IncrementalUpdater()


@router.post("/{repository_id}/incremental-update", response_model=IncrementalUpdateSummary)
async def trigger_incremental_update(repository_id: str):
    """Detects modified/added/deleted files and updates FAISS and BM25 indexes incrementally."""
    try:
        return updater.update_repository(repository_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incremental update failed: {e}")
