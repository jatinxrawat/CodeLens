"""API test cases for repository ingestion and status endpoints."""

from fastapi.testclient import TestClient
from pathlib import Path
from app.main import app

client = TestClient(app)


def test_list_and_get_repositories():
    response = client.get("/api/repositories")
    assert response.status_code == 200
    repos = response.json()
    assert isinstance(repos, list)
    assert any(r["repository_name"] == "sample_repo" for r in repos)

    # Get details
    resp_details = client.get("/api/repositories/sample_repo")
    assert resp_details.status_code == 200
    details = resp_details.json()
    assert details["repository_name"] == "sample_repo"
    assert details["status"] == "ready"
    assert details["total_files"] >= 6


def test_get_nonexistent_repository():
    response = client.get("/api/repositories/non_existent_repo_123")
    assert response.status_code == 404


def test_invalid_ingest_request():
    response = client.post("/api/repositories/ingest", json={"git_url": ""})
    assert response.status_code == 400

    response = client.post("/api/repositories/ingest", json={"git_url": "invalid-url"})
    assert response.status_code == 400
