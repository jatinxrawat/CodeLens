"""Rule-Based Code Smell Detection Module.

Identifies maintainability risks such as very long functions, deeply nested logic,
excessive parameters, overly large classes, and high coupling.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.models.code_chunk import CodeChunk, ChunkType
from app.config import settings
from app.analysis.quality_metrics import QualityMetricsCalculator


class CodeSmellFinding(BaseModel):
    id: str
    file_path: str
    symbol_name: Optional[str] = None
    start_line: int
    end_line: int
    rule_name: str
    issue_title: str
    metric_value: str
    threshold: str
    severity: str = Field(..., description="'CRITICAL', 'WARNING', 'INFO'")
    recommendation: str


class CodeSmellReport(BaseModel):
    repository_id: str
    total_findings: int
    critical_count: int
    warning_count: int
    info_count: int
    findings: List[CodeSmellFinding]


class CodeSmellDetector:
    """Detects rule-based code smells across parsed repository chunks."""

    def __init__(self):
        self.metrics_calc = QualityMetricsCalculator()

    def detect_smells(self, repo_name: str) -> CodeSmellReport:
        """Runs rule-based detection across all indexed chunks in the repository."""
        index_dir = settings.INDEXES_DIR / repo_name
        chunks_file = index_dir / "chunks.json"
        if not chunks_file.exists():
            raise FileNotFoundError(f"Repository index for '{repo_name}' not found.")

        with open(chunks_file, "r", encoding="utf-8") as f:
            raw_chunks = json.load(f)
        chunks = [CodeChunk.from_dict(c) for c in raw_chunks]

        findings: List[CodeSmellFinding] = []
        finding_id_seq = 1

        for c in chunks:
            loc = c.end_line - c.start_line + 1

            # 1. Very Long Function (> 50 lines)
            if c.chunk_type in (ChunkType.FUNCTION, ChunkType.METHOD) and loc > 50:
                findings.append(
                    CodeSmellFinding(
                        id=f"smell_{finding_id_seq}",
                        file_path=c.file_path,
                        symbol_name=c.symbol_name,
                        start_line=c.start_line,
                        end_line=c.end_line,
                        rule_name="LONG_FUNCTION",
                        issue_title="Long Function Body",
                        metric_value=f"{loc} lines",
                        threshold="> 50 lines",
                        severity="WARNING" if loc < 100 else "CRITICAL",
                        recommendation="Decompose large function into smaller, single-responsibility helper functions.",
                    )
                )
                finding_id_seq += 1

            # 2. Overly Large Class (> 250 lines)
            if c.chunk_type == ChunkType.CLASS and loc > 250:
                findings.append(
                    CodeSmellFinding(
                        id=f"smell_{finding_id_seq}",
                        file_path=c.file_path,
                        symbol_name=c.symbol_name,
                        start_line=c.start_line,
                        end_line=c.end_line,
                        rule_name="LARGE_CLASS",
                        issue_title="Large Class (God Object)",
                        metric_value=f"{loc} lines",
                        threshold="> 250 lines",
                        severity="WARNING",
                        recommendation="Split class responsibilities using the Single Responsibility Principle or composition.",
                    )
                )
                finding_id_seq += 1

            # 3. High Cyclomatic Complexity (> 10)
            cc = self.metrics_calc.calculate_cyclomatic_complexity(c.code)
            if cc > 10:
                findings.append(
                    CodeSmellFinding(
                        id=f"smell_{finding_id_seq}",
                        file_path=c.file_path,
                        symbol_name=c.symbol_name,
                        start_line=c.start_line,
                        end_line=c.end_line,
                        rule_name="HIGH_CYCLOMATIC_COMPLEXITY",
                        issue_title="High Cyclomatic Complexity",
                        metric_value=f"Score: {cc}",
                        threshold="> 10",
                        severity="CRITICAL" if cc > 20 else "WARNING",
                        recommendation="Simplify nested conditionals and extract branch handlers into dedicated strategy methods.",
                    )
                )
                finding_id_seq += 1

            # 4. Deeply Nested Logic (> 3 levels)
            depth = self.metrics_calc.calculate_nesting_depth(c.code)
            if depth > 3:
                findings.append(
                    CodeSmellFinding(
                        id=f"smell_{finding_id_seq}",
                        file_path=c.file_path,
                        symbol_name=c.symbol_name,
                        start_line=c.start_line,
                        end_line=c.end_line,
                        rule_name="DEEP_NESTING",
                        issue_title="Deeply Nested Indentation",
                        metric_value=f"{depth} levels",
                        threshold="> 3 levels",
                        severity="WARNING",
                        recommendation="Apply guard clauses (early returns) to flatten nested conditional logic.",
                    )
                )
                finding_id_seq += 1

            # 5. Excessive Parameters (> 5 parameters)
            if c.symbol_name:
                params = self.metrics_calc.calculate_parameter_count(c.code, c.symbol_name)
                if params > 5:
                    findings.append(
                        CodeSmellFinding(
                            id=f"smell_{finding_id_seq}",
                            file_path=c.file_path,
                            symbol_name=c.symbol_name,
                            start_line=c.start_line,
                            end_line=c.end_line,
                            rule_name="EXCESSIVE_PARAMETERS",
                            issue_title="Excessive Parameter Count",
                            metric_value=f"{params} parameters",
                            threshold="> 5 parameters",
                            severity="INFO" if params <= 7 else "WARNING",
                            recommendation="Introduce a Parameter Object or Config dataclass to encapsulate arguments.",
                        )
                    )
                    finding_id_seq += 1

        crit = sum(1 for f in findings if f.severity == "CRITICAL")
        warn = sum(1 for f in findings if f.severity == "WARNING")
        info = sum(1 for f in findings if f.severity == "INFO")

        return CodeSmellReport(
            repository_id=repo_name,
            total_findings=len(findings),
            critical_count=crit,
            warning_count=warn,
            info_count=info,
            findings=sorted(findings, key=lambda x: (0 if x.severity == "CRITICAL" else (1 if x.severity == "WARNING" else 2))),
        )
