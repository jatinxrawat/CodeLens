"""Repository Comparison Service.

Enables empirical side-by-side comparison of two codebases across
metrics, languages, complexity, smells, security, and retrieval performance.
"""

from typing import Dict, Any
from pydantic import BaseModel
from app.services.repository_service import repository_service
from app.analysis.quality_metrics import QualityMetricsCalculator
from app.analysis.code_smells import CodeSmellDetector
from app.analysis.security_scanner import SecurityScanner


class RepoComparisonResult(BaseModel):
    repo_a_id: str
    repo_b_id: str
    repo_a: Dict[str, Any]
    repo_b: Dict[str, Any]


class ComparisonService:
    """Compares two indexed repositories side by side."""

    def __init__(self):
        self.quality_calc = QualityMetricsCalculator()
        self.smell_detector = CodeSmellDetector()
        self.security_scanner = SecurityScanner()

    def compare_repositories(self, repo_a: str, repo_b: str) -> RepoComparisonResult:
        """Collects metrics for both repositories and formats comparative report."""
        stats_a = repository_service.get_repository_stats(repo_a)
        stats_b = repository_service.get_repository_stats(repo_b)

        quality_a = self.quality_calc.analyze_repository(repo_a)
        quality_b = self.quality_calc.analyze_repository(repo_b)

        smells_a = self.smell_detector.detect_smells(repo_a)
        smells_b = self.smell_detector.detect_smells(repo_b)

        sec_a = self.security_scanner.scan_repository(repo_a)
        sec_b = self.security_scanner.scan_repository(repo_b)

        a_data = {
            "name": repo_a,
            "total_files": stats_a.total_files,
            "total_chunks": stats_a.total_chunks,
            "total_loc": stats_a.total_lines_of_code,
            "languages": stats_a.languages,
            "avg_complexity": quality_a.avg_cyclomatic_complexity,
            "max_complexity": quality_a.max_cyclomatic_complexity,
            "maintainability": quality_a.overall_maintainability,
            "smells_count": smells_a.total_findings,
            "security_findings": sec_a.total_findings,
            "build_time_sec": stats_a.total_pipeline_time_sec,
        }

        b_data = {
            "name": repo_b,
            "total_files": stats_b.total_files,
            "total_chunks": stats_b.total_chunks,
            "total_loc": stats_b.total_lines_of_code,
            "languages": stats_b.languages,
            "avg_complexity": quality_b.avg_cyclomatic_complexity,
            "max_complexity": quality_b.max_cyclomatic_complexity,
            "maintainability": quality_b.overall_maintainability,
            "smells_count": smells_b.total_findings,
            "security_findings": sec_b.total_findings,
            "build_time_sec": stats_b.total_pipeline_time_sec,
        }

        return RepoComparisonResult(
            repo_a_id=repo_a,
            repo_b_id=repo_b,
            repo_a=a_data,
            repo_b=b_data,
        )


comparison_service = ComparisonService()
