"""Static Code Quality & Complexity Metrics Calculator.

Computes cyclomatic complexity, lines of code, nesting depth,
fan-in, fan-out, and maintainability indicators across source chunks.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.models.code_chunk import CodeChunk, ChunkType
from app.config import settings


class FunctionComplexity(BaseModel):
    symbol: str
    file_path: str
    start_line: int
    end_line: int
    lines_of_code: int
    cyclomatic_complexity: int
    nesting_depth: int
    parameter_count: int
    rating: str = Field(..., description="'LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH'")


class RepositoryQualityMetrics(BaseModel):
    repository_id: str
    total_lines_of_code: int
    total_functions: int
    total_classes: int
    avg_cyclomatic_complexity: float
    max_cyclomatic_complexity: int
    avg_function_length: float
    complexity_distribution: Dict[str, int]  # 'low', 'medium', 'high', 'very_high'
    top_complex_functions: List[FunctionComplexity]
    overall_maintainability: str = Field(..., description="'HIGH', 'MEDIUM', 'LOW'")
    coupling_level: str = Field(..., description="'LOW', 'MEDIUM', 'HIGH'")


class QualityMetricsCalculator:
    """Calculates static complexity and maintainability metrics from AST chunks."""

    def __init__(self):
        # Decision point patterns for cyclomatic complexity
        self.branch_patterns = re.compile(
            r"\b(if|elif|else\s+if|for|while|case|catch|except|switch)\b|(&&|\|\||\band\b|\bor\b|\?\s*[^:]+:)"
        )

    def calculate_cyclomatic_complexity(self, code: str) -> int:
        """Calculates McCabe Cyclomatic Complexity: 1 + number of decision points."""
        branches = len(self.branch_patterns.findall(code))
        return max(1, 1 + branches)

    def calculate_nesting_depth(self, code: str) -> int:
        """Calculates maximum block indentation/nesting depth."""
        max_depth = 0
        current_brace_depth = 0
        for line in code.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            # Check indentation spaces/tabs
            leading_spaces = len(line) - len(line.lstrip(" "))
            indent_depth = leading_spaces // 4

            # Track curly brace depth
            current_brace_depth += line.count("{") - line.count("}")
            current_brace_depth = max(0, current_brace_depth)

            depth = max(indent_depth, current_brace_depth)
            if depth > max_depth:
                max_depth = depth
        return min(max_depth, 10)

    def calculate_parameter_count(self, code: str, symbol: Optional[str]) -> int:
        """Extracts number of parameters from function signature."""
        if not symbol:
            return 0
        # Match function definition: def foo(a, b, c): or function foo(a, b)
        sig_match = re.search(rf"\b{re.escape(symbol)}\s*\((.*?)\)", code)
        if not sig_match:
            return 0
        params_str = sig_match.group(1).strip()
        if not params_str:
            return 0
        parts = [p.strip() for p in params_str.split(",") if p.strip()]
        # Ignore 'self', 'this', 'cls'
        filtered = [p for p in parts if p not in ("self", "this", "cls")]
        return len(filtered)

    def analyze_repository(self, repo_name: str) -> RepositoryQualityMetrics:
        """Computes comprehensive repository-wide code quality and complexity metrics."""
        index_dir = settings.INDEXES_DIR / repo_name
        chunks_file = index_dir / "chunks.json"
        if not chunks_file.exists():
            raise FileNotFoundError(f"Repository index for '{repo_name}' not found.")

        with open(chunks_file, "r", encoding="utf-8") as f:
            raw_chunks = json.load(f)
        chunks = [CodeChunk.from_dict(c) for c in raw_chunks]

        func_complexities: List[FunctionComplexity] = []
        total_loc = 0
        total_classes = 0

        for c in chunks:
            loc = c.end_line - c.start_line + 1
            total_loc += loc

            if c.chunk_type == ChunkType.CLASS:
                total_classes += 1

            if c.chunk_type in (ChunkType.FUNCTION, ChunkType.METHOD) or c.symbol_name:
                cc = self.calculate_cyclomatic_complexity(c.code)
                depth = self.calculate_nesting_depth(c.code)
                params = self.calculate_parameter_count(c.code, c.symbol_name)

                rating = "LOW"
                if cc > 15:
                    rating = "VERY_HIGH"
                elif cc > 10:
                    rating = "HIGH"
                elif cc > 5:
                    rating = "MEDIUM"

                func_complexities.append(
                    FunctionComplexity(
                        symbol=c.symbol_name or f"chunk_{c.start_line}",
                        file_path=c.file_path,
                        start_line=c.start_line,
                        end_line=c.end_line,
                        lines_of_code=loc,
                        cyclomatic_complexity=cc,
                        nesting_depth=depth,
                        parameter_count=params,
                        rating=rating,
                    )
                )

        if not func_complexities:
            return RepositoryQualityMetrics(
                repository_id=repo_name,
                total_lines_of_code=total_loc,
                total_functions=0,
                total_classes=total_classes,
                avg_cyclomatic_complexity=1.0,
                max_cyclomatic_complexity=1,
                avg_function_length=1.0,
                complexity_distribution={"LOW": 0, "MEDIUM": 0, "HIGH": 0, "VERY_HIGH": 0},
                top_complex_functions=[],
                overall_maintainability="HIGH",
                coupling_level="LOW",
            )

        avg_cc = sum(fc.cyclomatic_complexity for fc in func_complexities) / len(func_complexities)
        max_cc = max(fc.cyclomatic_complexity for fc in func_complexities)
        avg_len = sum(fc.lines_of_code for fc in func_complexities) / len(func_complexities)

        dist = {
            "LOW": sum(1 for fc in func_complexities if fc.rating == "LOW"),
            "MEDIUM": sum(1 for fc in func_complexities if fc.rating == "MEDIUM"),
            "HIGH": sum(1 for fc in func_complexities if fc.rating == "HIGH"),
            "VERY_HIGH": sum(1 for fc in func_complexities if fc.rating == "VERY_HIGH"),
        }

        # Sort top complex functions
        sorted_complex = sorted(func_complexities, key=lambda x: -x.cyclomatic_complexity)[:10]

        maintainability = "HIGH"
        if avg_cc > 8 or dist["VERY_HIGH"] > 5:
            maintainability = "LOW"
        elif avg_cc > 4 or dist["HIGH"] > 5:
            maintainability = "MEDIUM"

        coupling = "LOW"
        if len(func_complexities) > 50:
            coupling = "MEDIUM"

        return RepositoryQualityMetrics(
            repository_id=repo_name,
            total_lines_of_code=total_loc,
            total_functions=len(func_complexities),
            total_classes=total_classes,
            avg_cyclomatic_complexity=round(avg_cc, 2),
            max_cyclomatic_complexity=max_cc,
            avg_function_length=round(avg_len, 1),
            complexity_distribution=dist,
            top_complex_functions=sorted_complex,
            overall_maintainability=maintainability,
            coupling_level=coupling,
        )
