"""Optional GitHub OAuth authentication router."""

import httpx
from collections import Counter
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.config import settings
from app.services.cache_service import cache_service
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])


class OAuthCallbackRequest(BaseModel):
    code: str = Field(..., description="GitHub OAuth authorization code")


@router.get("/config")
async def get_auth_config():
    """Returns whether GitHub OAuth is configured on the server."""
    return {
        "oauth_enabled": bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET),
        "client_id": settings.GITHUB_CLIENT_ID or "",
    }


@router.get("/github/url")
async def get_github_oauth_url(redirect_uri: Optional[str] = None):
    """Generates the GitHub OAuth authorization URL."""
    client_id = settings.GITHUB_CLIENT_ID
    if not client_id:
        return {
            "error": "GitHub OAuth is not configured on this server.",
            "url": None,
        }
    scope = "read:user,repo"
    url = f"https://github.com/login/oauth/authorize?client_id={client_id}&scope={scope}"
    if redirect_uri:
        url += f"&redirect_uri={redirect_uri}"
    return {"url": url}


@router.post("/github/callback")
async def github_oauth_callback(req: OAuthCallbackRequest):
    """Exchanges authorization code for GitHub access token, calculates top languages, and creates user profile."""
    client_id = settings.GITHUB_CLIENT_ID
    client_secret = settings.GITHUB_CLIENT_SECRET

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400,
            detail="GitHub OAuth client credentials are not configured on this server.",
        )

    # 1. Exchange code for access token
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                json={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": req.code,
                },
            )
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise HTTPException(
                    status_code=400,
                    detail=f"GitHub OAuth failed: {token_data.get('error_description', 'No access token received')}",
                )

            # 2. Fetch authenticated user profile
            user_headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "CodeLens-OAuth",
            }
            user_resp = await client.get("https://api.github.com/user", headers=user_headers)
            user_data = user_resp.json()
            user_id = str(user_data.get("id"))
            username = user_data.get("login", "")
            avatar_url = user_data.get("avatar_url", "")

            # 3. Fetch user's repositories to extract top programming languages
            repos_resp = await client.get(
                "https://api.github.com/user/repos?sort=updated&per_page=30",
                headers=user_headers,
            )
            top_languages: List[str] = []
            if repos_resp.status_code == 200:
                user_repos = repos_resp.json()
                lang_counts = Counter(
                    r.get("language") for r in user_repos if r.get("language")
                )
                top_languages = [lang for lang, _ in lang_counts.most_common(5)]

            if not top_languages:
                top_languages = ["Python", "TypeScript", "JavaScript"]

            # 4. Save profile in SQLite
            cache_service.save_user_profile(
                user_id=user_id,
                username=username,
                avatar_url=avatar_url,
                top_languages=top_languages,
            )

            return {
                "status": "success",
                "user_id": user_id,
                "username": username,
                "avatar_url": avatar_url,
                "top_languages": top_languages,
                "access_token": access_token,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub OAuth error: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth authentication error: {e}")
