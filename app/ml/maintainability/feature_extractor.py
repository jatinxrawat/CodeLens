"""Maintainability Risk Feature Extractor.

Extracts multidimensional complexity and structural metrics from source code.
"""

from typing import Dict, Any, List
import numpy as np
from app.models.code_chunk import CodeChunk
from app.analysis.quality_metrics import QualityMetricsCalculator


class MaintainabilityFeatureExtractor:
    """Extracts numerical complexity features for the Maintainability Risk Model."""

    FEATURE_NAMES = [
        "loc",
        "cyclomatic_complexity",
        "nesting_depth",
        "param_count",
        "branch_count",
        "loop_count",
        "comment_ratio",
        "return_count",
        "error_blocks",
        "has_docstring",
        "avg_line_length",
    ]

    def __init__(self):
        self.quality_calc = QualityMetricsCalculator()

    def extract_features(self, chunk: CodeChunk) -> Dict[str, float]:
        """Extracts numerical features from a CodeChunk."""
        code = chunk.code
        lines = code.splitlines()
        loc = len([l for l in lines if l.strip()])
        raw_loc = len(lines)

        cc = self.quality_calc.calculate_cyclomatic_complexity(code)
        nesting = self.quality_calc.calculate_nesting_depth(code)

        param_count = 0
        if "(" in code and ")" in code:
            signature = code.split("{")[0].split(":")[0]
            if "(" in signature and ")" in signature:
                param_str = signature[signature.find("(") + 1 : signature.rfind(")")]
                param_count = len([p for p in param_str.split(",") if p.strip()])

        branch_count = float(code.count("if ") + code.count("elif ") + code.count("else:") + code.count("case ") + code.count("switch"))
        loop_count = float(code.count("for ") + code.count("while ") + code.count("do {"))
        comment_lines = len([l for l in lines if l.strip().startswith(("#", "//", "/*", "*", '"""', "'''"))])
        comment_ratio = float(comment_lines) / float(max(1, raw_loc))
        return_count = float(code.count("return ") + code.count("yield "))
        error_blocks = float(code.count("try:") + code.count("try {") + code.count("catch") + code.count("except"))

        return {
            "loc": float(loc),
            "cyclomatic_complexity": float(cc),
            "nesting_depth": float(nesting),
            "param_count": float(min(15, param_count)),
            "branch_count": branch_count,
            "loop_count": loop_count,
            "comment_ratio": round(comment_ratio, 3),
            "return_count": return_count,
            "error_blocks": error_blocks,
            "has_docstring": 1.0 if chunk.docstring else 0.0,
            "avg_line_length": float(sum(len(l) for l in lines) / max(1, len(lines))),
        }

    def extract_vector(self, chunk: CodeChunk) -> np.ndarray:
        """Returns 1D float array in canonical feature order."""
        feats = self.extract_features(chunk)
        return np.array([feats[name] for name in self.FEATURE_NAMES], dtype=np.float32)
