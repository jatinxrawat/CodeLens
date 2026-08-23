"""Unit tests for architectural layer inference engine."""

from pathlib import Path
from app.analysis.architecture_engine import ArchitectureEngine
from app.pipeline import IngestionPipeline


def test_architecture_engine(sample_repo_path: Path):
    pipeline = IngestionPipeline()
    pipeline.run_local(sample_repo_path)

    engine = ArchitectureEngine()
    report = engine.infer_architecture("sample_repo")

    assert report.repository_id == "sample_repo"
    assert len(report.layers) >= 1
    assert any(l.name == "Service / Business Logic" or l.name == "Unclassified / General" for l in report.layers)
    assert report.status == "Detected / Inferred"
