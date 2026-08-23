"""API tests for all Phase 4 endpoints."""

from fastapi.testclient import TestClient
from pathlib import Path
from app.main import app
from app.pipeline import IngestionPipeline

client = TestClient(app)


def setup_module():
    """Ensure sample_repo is ingested and indexed for API tests."""
    sample_path = Path(__file__).parent / "fixtures" / "sample_repo"
    if sample_path.exists():
        pipeline = IngestionPipeline()
        pipeline.run_local(sample_path)


def test_api_reasoning_ask():
    resp = client.post(
        "/api/reasoning/ask",
        json={
            "repository_id": "sample_repo",
            "query": "How is user authentication implemented?",
            "top_k": 3,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["repository_id"] == "sample_repo"
    assert data["is_sufficient_evidence"] is True
    assert len(data["sources"]) >= 1
    assert "answer" in data


def test_api_analysis_endpoints():
    # 1. Architecture
    resp_arch = client.get("/api/analysis/sample_repo/architecture")
    assert resp_arch.status_code == 200
    assert len(resp_arch.json()["layers"]) >= 1

    # 2. Quality
    resp_qual = client.get("/api/analysis/sample_repo/quality")
    assert resp_qual.status_code == 200
    assert resp_qual.json()["total_lines_of_code"] > 0

    # 3. Smells
    resp_smells = client.get("/api/analysis/sample_repo/smells")
    assert resp_smells.status_code == 200
    assert "total_findings" in resp_smells.json()

    # 4. Security
    resp_sec = client.get("/api/analysis/sample_repo/security")
    assert resp_sec.status_code == 200
    assert "total_findings" in resp_sec.json()

    # 5. Flow
    resp_flow = client.get("/api/analysis/sample_repo/flow?symbol=login_user")
    assert resp_flow.status_code == 200
    assert resp_flow.json()["target_symbol"] == "login_user"

    # 6. Impact
    resp_impact = client.post("/api/analysis/sample_repo/impact", json={"target": "python/auth.py"})
    assert resp_impact.status_code == 200
    assert resp_impact.json()["target"] == "python/auth.py"


def test_api_reports_and_compare():
    # Report JSON
    resp_rep = client.get("/api/repositories/sample_repo/report")
    assert resp_rep.status_code == 200
    assert "stats" in resp_rep.json()

    # Report Markdown
    resp_md = client.get("/api/repositories/sample_repo/report/markdown")
    assert resp_md.status_code == 200
    assert "# Code Intelligence Report: sample_repo" in resp_md.text

    # Compare
    resp_comp = client.post("/api/repositories/compare", json={"repo_a": "sample_repo", "repo_b": "sample_repo"})
    assert resp_comp.status_code == 200
    assert resp_comp.json()["repo_a_id"] == "sample_repo"

    # Incremental update
    resp_inc = client.post("/api/repositories/sample_repo/incremental-update")
    assert resp_inc.status_code == 200
    assert resp_inc.json()["status"] == "completed"
