"""API tests for stats, file tree, graph, and evaluation endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_stats():
    response = client.get("/api/repositories/sample_repo/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["repository_id"] == "sample_repo"
    assert data["total_files"] >= 6
    assert data["total_chunks"] >= 6
    assert "python" in data["languages"]


def test_api_files_and_content():
    # File tree
    resp_tree = client.get("/api/repositories/sample_repo/files")
    assert resp_tree.status_code == 200
    files = resp_tree.json()
    assert isinstance(files, list)
    assert len(files) >= 6

    # File content
    resp_content = client.get("/api/repositories/sample_repo/file-content?path=python/auth.py")
    assert resp_content.status_code == 200
    content_data = resp_content.json()
    assert "def login_user" in content_data["code"]
    assert content_data["language"] == "python"


def test_api_dependency_graph():
    response = client.get("/api/repositories/sample_repo/graph")
    assert response.status_code == 200
    data = response.json()
    assert data["repository_id"] == "sample_repo"
    assert data["total_nodes"] >= 6
    assert len(data["nodes"]) >= 6
    assert isinstance(data["edges"], list)


def test_api_evaluation():
    response = client.post("/api/repositories/sample_repo/evaluate", json={"top_k": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["repository_id"] == "sample_repo"
    assert data["total_queries"] >= 7
    assert len(data["comparisons"]) >= 3
    # Check that Recall@5 and MRR are present
    for comp in data["comparisons"]:
        assert 0.0 <= comp["recall_at_5"] <= 1.0
        assert 0.0 <= comp["mean_reciprocal_rank"] <= 1.0
