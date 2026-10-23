"""End-to-end API tests for Explore, Contribute, Provider, and User endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app

client = TestClient(app)


def test_api_explore_repos():
    response = client.get("/api/explore/repos?min_stars=50&page=1&per_page=5")
    assert response.status_code == 200
    data = response.json()
    assert "repos" in data
    assert isinstance(data["repos"], list)
    if len(data["repos"]) > 0:
        repo = data["repos"][0]
        assert "name" in repo
        assert "readiness" in repo
        assert "score" in repo["readiness"]


def test_api_contribute_issues():
    response = client.get("/api/contribute/issues?language=All&domain=All&difficulty=All&page=1&per_page=5")
    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
    assert isinstance(data["issues"], list)
    if len(data["issues"]) > 0:
        issue = data["issues"][0]
        assert "title" in issue
        assert "difficulty" in issue
        assert "skills" in issue


def test_api_contribute_repos():
    response = client.get("/api/contribute/repos?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "repos" in data
    assert isinstance(data["repos"], list)


def test_api_provider_get_and_post():
    # 1. GET current provider
    get_res = client.get("/api/reasoning/provider")
    assert get_res.status_code == 200
    p_info = get_res.json()
    assert "active_provider" in p_info

    # 2. POST to switch provider to 'local'
    post_res = client.post("/api/reasoning/provider", json={"provider": "local"})
    assert post_res.status_code == 200
    updated_info = post_res.json()
    assert updated_info["active_provider"] == "local"

    # 3. Invalid provider returns 400
    bad_res = client.post("/api/reasoning/provider", json={"provider": "invalid_mode"})
    assert bad_res.status_code == 400


def test_api_repos_analyze_and_status():
    from unittest.mock import MagicMock

    mock_job = MagicMock()
    mock_job.job_id = "test_job_123"
    mock_job.repository_id = "test_owner_repo"
    mock_job.status = "running"
    mock_job.progress_pct = 25

    with patch("app.services.repository_service.repository_service.start_remote_ingestion_job", return_value=mock_job):
        res = client.post(
            "/api/repos/analyze",
            json={"url": "https://github.com/test_owner/repo.git"},
        )
        assert res.status_code == 202
        data = res.json()
        assert data["repo_id"] == "test_owner_repo"
        assert data["job_id"] == "test_job_123"

        # Check status endpoint
        with patch("app.services.repository_service.repository_service.get_repository_status") as mock_status:
            mock_status.return_value = {
                "repository_id": "test_owner_repo",
                "status": "ready",
                "progress_pct": 100,
            }
            st_res = client.get("/api/repos/test_owner_repo/status")
            assert st_res.status_code == 200
            st_data = st_res.json()
            assert st_data["repository_id"] == "test_owner_repo"
            assert st_data["status"] == "ready"


def test_api_user_bookmarks_and_working():
    import time
    headers = {"X-User-ID": "student_tester_42"}
    test_issue_id = f"issue_{int(time.time() * 1000)}"

    # 1. Toggle bookmark
    bm_res = client.post(
        "/api/user/bookmarks",
        headers=headers,
        json={
            "issue_id": test_issue_id,
            "repo_name": "tiangolo/fastapi",
            "title": "Fix docstring typos",
            "url": f"https://github.com/tiangolo/fastapi/issues/{test_issue_id}",
        },
    )
    assert bm_res.status_code == 200
    assert bm_res.json()["is_bookmarked"] is True

    # 2. Toggle working status
    work_res = client.post(
        "/api/user/working",
        headers=headers,
        json={
            "issue_id": test_issue_id,
            "repo_name": "tiangolo/fastapi",
            "title": "Fix docstring typos",
            "url": f"https://github.com/tiangolo/fastapi/issues/{test_issue_id}",
            "status": "in_progress",
        },
    )
    assert work_res.status_code == 200
    assert work_res.json()["is_working"] is True

    # 3. Get profile
    prof_res = client.get("/api/user/profile", headers=headers)
    assert prof_res.status_code == 200
    prof = prof_res.json()
    assert prof["user_id"] == "student_tester_42"
    assert any(b["issue_id"] == test_issue_id for b in prof["bookmarks"])
    assert any(w["issue_id"] == test_issue_id for w in prof["working"])
