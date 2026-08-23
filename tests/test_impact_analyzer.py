"""Unit tests for potential impact analysis and blast radius calculation."""

from pathlib import Path
from app.analysis.impact_analyzer import ImpactAnalyzer
from app.pipeline import IngestionPipeline


def test_impact_analyzer_sample_repo(sample_repo_path: Path):
    pipeline = IngestionPipeline()
    pipeline.run_local(sample_repo_path)

    analyzer = ImpactAnalyzer()
    res = analyzer.analyze_impact("sample_repo", "python/auth.py")

    assert res.target == "python/auth.py"
    assert res.target_type == "file"
    assert isinstance(res.impacted_files, list)
    assert res.total_affected_files >= 0
