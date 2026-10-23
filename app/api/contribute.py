"""Contribute API router for open source beginner issues and friendly repos."""

from fastapi import APIRouter, Query, Depends, Request
from typing import Optional, Dict, Any, List
from app.services.github_service import github_service
from app.services.cache_service import cache_service
from app.utils.rate_limiter import check_rate_limit

router = APIRouter(prefix="/contribute", tags=["Contribute"])


@router.get("/issues", dependencies=[Depends(check_rate_limit)])
async def get_contribute_issues(
    request: Request,
    language: Optional[str] = Query(None, description="Programming language filter"),
    domain: Optional[str] = Query(None, description="Domain filter: 'AI/ML', 'web', 'devops', 'mobile'"),
    difficulty: Optional[str] = Query(None, description="Difficulty filter: 'easy', 'medium', 'hard'"),
    q: Optional[str] = Query(None, description="Search keywords"),
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=50),
    refresh: bool = Query(False, description="Force refresh cache"),
):
    """Retrieves open beginner issues with Gemini-generated summaries, skills, and likely files."""
    # Check if logged in user has top languages
    user_id = request.headers.get("X-User-ID", "guest")
    user_top_langs: Optional[List[str]] = None
    if user_id and user_id != "guest":
        profile = cache_service.get_user_profile(user_id)
        if profile and profile.get("top_languages"):
            user_top_langs = profile["top_languages"]

    return await github_service.get_contribute_issues(
        language=language,
        domain=domain,
        difficulty=difficulty,
        search_query=q,
        user_top_languages=user_top_langs,
        page=page,
        per_page=per_page,
        force_refresh=refresh,
    )


@router.get("/repos", dependencies=[Depends(check_rate_limit)])
async def get_contribute_repos(
    language: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=50),
):
    """Retrieves contribution-friendly open source repositories."""
    return await github_service.get_contribute_repos(
        language=language,
        domain=domain,
        page=page,
        per_page=per_page,
    )
