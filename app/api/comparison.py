"""Repository Comparison API router."""

from fastapi import APIRouter, HTTPException
from app.schemas.comparison import CompareRequest, RepoComparisonResult
from app.services.comparison_service import comparison_service

router = APIRouter()


@router.post("/compare", response_model=RepoComparisonResult)
async def compare_repositories(request: CompareRequest):
    """Compares two indexed repositories across metrics, complexity, and security."""
    try:
        return comparison_service.compare_repositories(request.repo_a, request.repo_b)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")
