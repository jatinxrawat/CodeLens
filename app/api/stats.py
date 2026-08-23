"""Repository statistics and performance telemetry API router."""

from fastapi import APIRouter, HTTPException
from app.schemas.stats import RepositoryStatsResponse
from app.services.repository_service import repository_service
from app.services.search_service import search_service

router = APIRouter()


@router.get("/{repository_id}/stats", response_model=RepositoryStatsResponse)
async def get_repository_stats(repository_id: str):
    """Returns detailed parsing, indexing, and search telemetry statistics."""
    try:
        stats = repository_service.get_repository_stats(repository_id)
        avg_lat, p95_lat = search_service.get_latency_stats()
        stats.avg_search_latency_ms = avg_lat
        stats.p95_search_latency_ms = p95_lat
        return stats
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve repository stats: {e}")
