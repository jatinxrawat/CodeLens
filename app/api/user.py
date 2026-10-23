"""User bookmarks, working status, and preference profile API router."""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.cache_service import cache_service

router = APIRouter(prefix="/user", tags=["User & Contributions"])


class BookmarkToggleRequest(BaseModel):
    issue_id: str
    repo_name: str
    title: str
    url: str


class WorkingToggleRequest(BaseModel):
    issue_id: str
    repo_name: str
    title: str
    url: str
    status: Optional[str] = "in_progress"


class TopLanguagesRequest(BaseModel):
    top_languages: List[str]


def _resolve_user_id(request: Request) -> str:
    return request.headers.get("X-User-ID", "guest_student")


@router.get("/profile")
async def get_profile(request: Request):
    user_id = _resolve_user_id(request)
    profile = cache_service.get_user_profile(user_id)
    if not profile:
        profile = {
            "user_id": user_id,
            "username": "Guest Student" if user_id == "guest_student" else user_id,
            "avatar_url": "",
            "top_languages": ["Python", "TypeScript", "JavaScript"],
        }
    profile["bookmarks"] = cache_service.get_bookmarks(user_id)
    profile["working"] = cache_service.get_working(user_id)
    return profile


@router.get("/bookmarks")
async def get_bookmarks(request: Request):
    user_id = _resolve_user_id(request)
    return cache_service.get_bookmarks(user_id)


@router.post("/bookmarks")
async def toggle_bookmark(req: BookmarkToggleRequest, request: Request):
    user_id = _resolve_user_id(request)
    is_bookmarked = cache_service.toggle_bookmark(
        user_id=user_id,
        issue_id=req.issue_id,
        repo_name=req.repo_name,
        title=req.title,
        url=req.url,
    )
    return {
        "issue_id": req.issue_id,
        "is_bookmarked": is_bookmarked,
        "message": "Bookmark added" if is_bookmarked else "Bookmark removed",
    }


@router.get("/working")
async def get_working(request: Request):
    user_id = _resolve_user_id(request)
    return cache_service.get_working(user_id)


@router.post("/working")
async def toggle_working(req: WorkingToggleRequest, request: Request):
    user_id = _resolve_user_id(request)
    is_working = cache_service.toggle_working(
        user_id=user_id,
        issue_id=req.issue_id,
        repo_name=req.repo_name,
        title=req.title,
        url=req.url,
        status=req.status or "in_progress",
    )
    return {
        "issue_id": req.issue_id,
        "is_working": is_working,
        "message": "Marked as working on this" if is_working else "Removed from working list",
    }


@router.post("/top-languages")
async def set_top_languages(req: TopLanguagesRequest, request: Request):
    user_id = _resolve_user_id(request)
    profile = cache_service.get_user_profile(user_id) or {
        "user_id": user_id,
        "username": user_id,
        "avatar_url": "",
    }
    cache_service.save_user_profile(
        user_id=user_id,
        username=profile.get("username", user_id),
        avatar_url=profile.get("avatar_url", ""),
        top_languages=req.top_languages,
    )
    return {"status": "success", "top_languages": req.top_languages}
