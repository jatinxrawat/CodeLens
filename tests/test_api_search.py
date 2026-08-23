"""API test cases for search endpoint with Hybrid, Vector, and Keyword modes."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_search_hybrid():
    payload = {
        "repository_id": "sample_repo",
        "query": "Where is user login and password authentication handled?",
        "top_k": 3,
        "mode": "hybrid",
        "alpha": 0.6,
    }
    response = client.post("/api/search", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == payload["query"]
    assert data["mode"] == "hybrid"
    assert data["total_results"] >= 1
    assert data["latency_ms"] > 0
    top = data["results"][0]
    assert "file_path" in top
    assert "code" in top
    assert top["similarity"] >= 0.0


def test_api_search_vector_and_keyword():
    # Vector mode
    resp_v = client.post(
        "/api/search",
        json={"repository_id": "sample_repo", "query": "memory pool allocate buffer", "top_k": 2, "mode": "vector"},
    )
    assert resp_v.status_code == 200
    assert len(resp_v.json()["results"]) >= 1

    # Keyword mode
    resp_k = client.post(
        "/api/search",
        json={"repository_id": "sample_repo", "query": "LRUCache capacity items_list", "top_k": 2, "mode": "keyword"},
    )
    assert resp_k.status_code == 200
    assert len(resp_k.json()["results"]) >= 1


def test_api_search_empty_query():
    response = client.post("/api/search", json={"repository_id": "sample_repo", "query": "  "})
    assert response.status_code == 400


def test_api_search_missing_repo():
    response = client.post("/api/search", json={"repository_id": "nonexistent_repo", "query": "login"})
    assert response.status_code == 404
