"""Unit tests for GitHub REST API Integration Service with mocked HTTP."""

import pytest
import httpx
import time
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.github_service import GitHubService, github_service
from app.services.cache_service import cache_service


@pytest.fixture
def mock_repo_item():
    return {
        "id": 123456,
        "name": "fastapi",
        "full_name": "tiangolo/fastapi",
        "html_url": "https://github.com/tiangolo/fastapi",
        "description": "FastAPI framework, high performance, easy to learn",
        "stargazers_count": 75000,
        "forks_count": 6000,
        "open_issues_count": 250,
        "language": "Python",
        "topics": ["python", "api", "rest", "async"],
        "pushed_at": "2026-10-20T12:00:00Z",
        "created_at": "2018-12-08T10:00:00Z",
        "owner": {
            "login": "tiangolo",
            "avatar_url": "https://avatars.githubusercontent.com/u/1326112",
        },
    }


@pytest.fixture
def mock_issue_item():
    return {
        "id": 998877,
        "number": 105,
        "title": "Fix docstring typos in router.py",
        "html_url": "https://github.com/tiangolo/fastapi/issues/105",
        "body": "There are minor spelling mistakes in app/router.py docstrings.",
        "state": "open",
        "created_at": "2026-10-18T08:00:00Z",
        "updated_at": "2026-10-22T09:00:00Z",
        "comments": 2,
        "labels": [{"name": "good first issue", "color": "7057ff"}],
        "repository_url": "https://api.github.com/repos/tiangolo/fastapi",
        "user": {"login": "student_contributor", "avatar_url": "https://example.com/avatar.png"},
    }


@pytest.mark.anyio
async def test_get_explore_repos_with_mocked_http(mock_repo_item):
    service = GitHubService(token="mock_gh_token_123")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "total_count": 1,
        "items": [mock_repo_item],
    }
    mock_resp.headers = {
        "x-ratelimit-remaining": "48",
        "x-ratelimit-reset": str(time.time() + 1800),
    }

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        res = await service.get_explore_repos(
            language="Python",
            min_stars=100,
            page=1,
            per_page=5,
            force_refresh=True,
        )

        assert "repos" in res
        assert len(res["repos"]) == 1
        repo = res["repos"][0]
        assert repo["name"] == "fastapi"
        assert repo["full_name"] == "tiangolo/fastapi"
        assert repo["stars"] == 75000
        assert "readiness" in repo
        assert 0 <= repo["readiness"]["score"] <= 100
        assert service._rate_limit_remaining == 48


@pytest.mark.anyio
async def test_get_contribute_issues_with_mocked_http(mock_issue_item):
    service = GitHubService(token="mock_gh_token_123")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "total_count": 1,
        "items": [mock_issue_item],
    }
    mock_resp.headers = {
        "x-ratelimit-remaining": "45",
        "x-ratelimit-reset": str(time.time() + 1800),
    }

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        res = await service.get_contribute_issues(
            language="Python",
            domain="Web",
            difficulty="easy",
            page=1,
            per_page=5,
            force_refresh=True,
        )

        assert "issues" in res
        assert len(res["issues"]) >= 1
        issue = res["issues"][0]
        assert issue["title"] == "Fix docstring typos in router.py"
        assert "difficulty" in issue
        assert "skills" in issue
        assert "readiness" in issue


@pytest.mark.anyio
async def test_rate_limit_exhaustion_returns_fallback():
    service = GitHubService()
    # Force remaining rate limit to 0
    service._rate_limit_remaining = 0
    service._rate_limit_reset = time.time() + 600

    # Calling contribute issues when exhausted should return cached/curated fallback without calling HTTP
    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        res = await service.get_contribute_issues(force_refresh=True)
        assert mock_get.call_count == 0
        assert "issues" in res
        assert len(res["issues"]) > 0


@pytest.mark.anyio
async def test_caching_behavior(mock_repo_item):
    service = GitHubService()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "total_count": 1,
        "items": [mock_repo_item],
    }
    mock_resp.headers = {"x-ratelimit-remaining": "50"}

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        # First call: hits HTTP
        res1 = await service.get_explore_repos(language="Go", force_refresh=True)
        assert mock_get.call_count == 1

        # Second call with force_refresh=False: hits SQLite cache
        res2 = await service.get_explore_repos(language="Go", force_refresh=False)
        assert mock_get.call_count == 1  # No additional network call
        assert res1["repos"][0]["name"] == res2["repos"][0]["name"]
