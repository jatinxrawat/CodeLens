"""Tests for the CodeLens ingestion job pipeline, state machine, and edge cases."""

import pytest
import shutil
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.ingestion.repository import RepositoryManager
from app.services.job_manager import job_manager, STAGE_METADATA
from app.services.repository_service import repository_service
from app.pipeline import IngestionPipeline
from app.config import settings

client = TestClient(app)


def test_git_availability():
    """Verifies git detection."""
    assert RepositoryManager.is_git_available() is True


def test_clone_url_normalization():
    """Verifies that owner/repo and various URL formats are correctly normalized."""
    # owner/repo shorthand
    assert RepositoryManager.normalize_clone_url("pallets/click") == "https://github.com/pallets/click.git"
    assert RepositoryManager.normalize_clone_url("facebook/react") == "https://github.com/facebook/react.git"

    # github.com/ without protocol
    assert RepositoryManager.normalize_clone_url("github.com/tiangolo/fastapi") == "https://github.com/tiangolo/fastapi.git"

    # Full https URL without .git
    assert RepositoryManager.normalize_clone_url("https://github.com/pallets/click") == "https://github.com/pallets/click.git"

    # Full https URL with .git
    assert RepositoryManager.normalize_clone_url("https://github.com/pallets/click.git") == "https://github.com/pallets/click.git"

    # SSH / git@ URL
    assert RepositoryManager.normalize_clone_url("git@github.com:pallets/click.git") == "git@github.com:pallets/click.git"

    # Invalid URLs
    with pytest.raises(ValueError):
        RepositoryManager.normalize_clone_url("")

    with pytest.raises(ValueError):
        RepositoryManager.normalize_clone_url("justaname")


def test_job_state_machine_transitions():
    """Tests the job lifecycle state machine from queued to ready and persistence."""
    repo_name = "test_lifecycle_repo"
    job = job_manager.create_job(repo_name, "https://github.com/test/repo.git")

    assert job.status == "queued"
    assert job.current_step == "queued"
    assert job.stage == "Queued"
    assert job.progress_pct == 5
    assert "queued" in job.message.lower()

    # Transition to cloning
    job_manager.update_job(job.job_id, current_step="cloning")
    updated = job_manager.get_job(job.job_id)
    assert updated.current_step == "cloning"
    assert updated.stage == "Cloning"
    assert updated.progress_pct == 15

    # Transition to parsing
    job_manager.update_job(job.job_id, current_step="parsing")
    updated = job_manager.get_job(job.job_id)
    assert updated.stage == "Parsing AST"
    assert updated.progress_pct == 40

    # Transition to embedding
    job_manager.update_job(job.job_id, current_step="embedding")
    updated = job_manager.get_job(job.job_id)
    assert updated.stage == "Generating Embeddings"
    assert updated.progress_pct == 65
    assert "downloading" in updated.message.lower()

    # Transition to indexing
    job_manager.update_job(job.job_id, current_step="indexing")
    updated = job_manager.get_job(job.job_id)
    assert updated.stage == "Building Indices"
    assert updated.progress_pct == 85

    # Transition to done
    job_manager.update_job(job.job_id, status="done", current_step="done")
    updated = job_manager.get_job(job.job_id)
    assert updated.stage == "Ready"
    assert updated.progress_pct == 100

    # Verify retrieval by repo name
    latest = job_manager.get_latest_job_for_repo(repo_name)
    assert latest is not None
    assert latest.job_id == job.job_id


def test_job_failure_state():
    """Verifies that failure updates status to failed with 0 progress and informative error."""
    repo_name = "test_failure_repo"
    job = job_manager.create_job(repo_name, "https://github.com/test/fail.git")

    job_manager.update_job(
        job.job_id,
        current_step="cloning",
        error="Git clone timed out after 60 seconds. The repository may be too large or GitHub is responding slowly.",
    )

    failed_job = job_manager.get_job(job.job_id)
    assert failed_job.status == "failed"
    assert failed_job.stage == "Failed"
    assert failed_job.progress_pct == 0
    assert "timed out" in failed_job.error

    # Verify repository status service reflects failed state with non-null fields
    status_resp = repository_service.get_repository_status(failed_job.job_id)
    assert status_resp.status == "failed"
    assert status_resp.stage == "Failed"
    assert status_resp.progress_pct == 0
    assert status_resp.error is not None
    assert "timed out" in status_resp.error


def test_empty_repository_handling():
    """Verifies that a repository with no code files (e.g. README-only) finishes gracefully without crashing."""
    temp_dir = Path(tempfile.mkdtemp(prefix="codelens_empty_repo_"))
    try:
        # Create only non-code files (README.md and LICENSE)
        (temp_dir / "README.md").write_text("# Documentation Only\nNo code here.")
        (temp_dir / "LICENSE").write_text("MIT License")

        empty_repo_name = f"test_empty_{temp_dir.name}"
        pipeline = IngestionPipeline()
        meta = pipeline._process_repository(
            repo_name=empty_repo_name,
            repo_path=temp_dir,
            source_descriptor=str(temp_dir),
            ingestion_time_sec=0.1,
        )

        assert meta.total_files == 0
        assert meta.total_chunks == 0

        # Verify repository service reports status as ready with 100% and clear message
        status_resp = repository_service.get_repository_status(empty_repo_name)
        assert status_resp.status == "ready"
        assert status_resp.progress_pct == 100
        assert status_resp.total_files == 0
        assert status_resp.total_chunks == 0
        assert "No code files found" in status_resp.message
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        # Clean up created index
        index_dir = settings.INDEXES_DIR / empty_repo_name
        if index_dir.exists():
            shutil.rmtree(index_dir, ignore_errors=True)


def test_repos_analyze_api_flow():
    """Tests the /api/repos/analyze and status polling endpoint contracts."""
    response = client.post("/api/repos/analyze", json={"url": "pallets/click"})
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert "repo_id" in data
    assert data["stage"] == "Queued"
    assert data["progress_pct"] == 5
    assert data["current_step"] == "queued"

    # Poll status using job_id
    poll_resp = client.get(f"/api/repos/{data['job_id']}/status")
    assert poll_resp.status_code == 200
    status_data = poll_resp.json()
    assert status_data["stage"] in ("Queued", "Cloning", "Parsing AST", "Generating Embeddings", "Building Indices", "Ready", "Failed")
    assert isinstance(status_data["progress_pct"], int)
    assert status_data["message"] is not None
