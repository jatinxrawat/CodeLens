"""Maintainability Risk Explainability Layer.

Clearly distinguishes measured static metrics from ML model predictions.
"""

from typing import Dict, Any
from app.models.code_chunk import CodeChunk
from app.ml.maintainability.risk_model import MaintainabilityRiskModel
from app.ml.maintainability.feature_extractor import MaintainabilityFeatureExtractor


class MaintainabilityExplainer:
    """Provides transparent, factual diagnostic factors for maintainability risk predictions."""

    def __init__(self, model: MaintainabilityRiskModel):
        self.model = model
        self.extractor = MaintainabilityFeatureExtractor()

    def explain_chunk(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Produces a breakdown with measured facts vs ML model risk assessment."""
        prediction = self.model.predict_chunk_risk(chunk)
        feats = prediction["measured_features"]

        # 1. Measured Facts (empirical ground truth)
        measured_facts = [
            f"Measured Cyclomatic Complexity: {int(feats['cyclomatic_complexity'])} decision points",
            f"Measured Lines of Code: {int(feats['loc'])} LOC (raw {len(chunk.code.splitlines())} lines)",
            f"Measured Max Nesting Depth: {int(feats['nesting_depth'])} levels",
            f"Measured Parameter Count: {int(feats['param_count'])} parameters",
            f"Measured Branch Count: {int(feats['branch_count'])} conditional branches",
            f"Measured Comment Ratio: {feats['comment_ratio'] * 100:.1f}%",
        ]

        # 2. Risk Factors Driving Model Output
        contributing_factors = []
        if feats["cyclomatic_complexity"] >= 10:
            contributing_factors.append({
                "factor": "High Cyclomatic Complexity",
                "severity": "CRITICAL",
                "detail": f"CC is {int(feats['cyclomatic_complexity'])}, well above the clean code threshold of 10.",
            })
        elif feats["cyclomatic_complexity"] >= 5:
            contributing_factors.append({
                "factor": "Moderate Cyclomatic Complexity",
                "severity": "WARNING",
                "detail": f"CC is {int(feats['cyclomatic_complexity'])}, indicating non-trivial branching logic.",
            })

        if feats["loc"] >= 60:
            contributing_factors.append({
                "factor": "Excessive Function Length",
                "severity": "WARNING",
                "detail": f"Length is {int(feats['loc'])} lines, reducing readability and test isolation.",
            })

        if feats["nesting_depth"] >= 4:
            contributing_factors.append({
                "factor": "Deep Control-Flow Nesting",
                "severity": "CRITICAL",
                "detail": f"Nesting is {int(feats['nesting_depth'])} levels deep, elevating cognitive complexity.",
            })

        if feats["param_count"] >= 5:
            contributing_factors.append({
                "factor": "High Parameter Count",
                "severity": "WARNING",
                "detail": f"Accepts {int(feats['param_count'])} parameters; consider passing a configuration object.",
            })

        return {
            "symbol_name": chunk.symbol_name,
            "file_path": chunk.file_path,
            "predicted_risk": prediction["predicted_risk"],
            "model_confidence": prediction["confidence"],
            "probabilities": prediction["probabilities"],
            "measured_facts": measured_facts,
            "contributing_factors": contributing_factors,
            "recommendation": (
                "Refactor into smaller, focused single-responsibility subroutines."
                if prediction["predicted_risk"] == "HIGH"
                else "Acceptable complexity, but monitor future conditional growth."
                if prediction["predicted_risk"] == "MEDIUM"
                else "Code exhibits clean maintainability characteristics."
            ),
        }
