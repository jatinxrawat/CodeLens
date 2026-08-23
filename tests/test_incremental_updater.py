"""Unit tests for incremental repository updates."""

from pathlib import Path
from app.ingestion.incremental_updater import IncrementalUpdater
from app.pipeline import IngestionPipeline


def test_incremental_updater_sample_repo(sample_repo_path: Path):
    pipeline = IngestionPipeline()
    pipeline.run_local(sample_repo_path)

    updater = IncrementalUpdater()
    res = updater.update_repository("sample_repo")

    assert res.repository_id == "sample_repo"
    assert res.status == "completed"
    assert res.duration_sec >= 0
