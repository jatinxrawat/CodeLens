"""Unit tests for code quality metrics and code smell detector."""

from pathlib import Path
from app.analysis.quality_metrics import QualityMetricsCalculator
from app.analysis.code_smells import CodeSmellDetector
from app.pipeline import IngestionPipeline


def test_quality_metrics_and_smells(sample_repo_path: Path):
    pipeline = IngestionPipeline()
    pipeline.run_local(sample_repo_path)

    calc = QualityMetricsCalculator()
    metrics = calc.analyze_repository("sample_repo")

    assert metrics.repository_id == "sample_repo"
    assert metrics.total_lines_of_code > 0
    assert metrics.avg_cyclomatic_complexity >= 1.0
    assert metrics.overall_maintainability in ("HIGH", "MEDIUM", "LOW")

    detector = CodeSmellDetector()
    smells = detector.detect_smells("sample_repo")
    assert smells.repository_id == "sample_repo"
    assert isinstance(smells.findings, list)
