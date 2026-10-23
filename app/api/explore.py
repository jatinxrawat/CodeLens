"""Explore API router for GitHub repositories and trending codebases."""

from fastapi import APIRouter, Query, Depends
from typing import Optional, Dict, Any
from app.services.github_service import github_service
from app.utils.rate_limiter import check_rate_limit

router = APIRouter(prefix="/explore", tags=["Explore"])


@router.get("/repos", dependencies=[Depends(check_rate_limit)])
async def get_explore_repos(
    language: Optional[str] = Query(None, description="Programming language filter (e.g. 'python', 'typescript')"),
    topic: Optional[str] = Query(None, description="GitHub topic/domain filter (e.g. 'machine-learning', 'web')"),
    min_stars: int = Query(50, ge=0, description="Minimum star count"),
    recently_active: bool = Query(True, description="Filter for repositories pushed in the last 60 days"),
    q: Optional[str] = Query(None, description="Optional text search query"),
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=50),
    refresh: bool = Query(False, description="Force refresh cache from GitHub"),
):
    """Retrieves top repositories from GitHub Search API, enriched with contribution readiness scores."""
    return await github_service.get_explore_repos(
        language=language,
        topic=topic,
        min_stars=min_stars,
        recently_active=recently_active,
        search_query=q,
        page=page,
        per_page=per_page,
        force_refresh=refresh,
    )
