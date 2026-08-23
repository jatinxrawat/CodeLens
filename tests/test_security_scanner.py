"""Unit tests for static security pattern scanner."""

from pathlib import Path
from app.analysis.security_scanner import SecurityScanner
from app.pipeline import IngestionPipeline


def test_security_scanner_sample_repo(sample_repo_path: Path):
    pipeline = IngestionPipeline()
    pipeline.run_local(sample_repo_path)

    scanner = SecurityScanner()
    report = scanner.scan_repository("sample_repo")

    assert report.repository_id == "sample_repo"
    assert isinstance(report.findings, list)
    assert report.total_findings >= 0
