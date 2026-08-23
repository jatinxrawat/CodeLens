"""Hallucination Protection & Evidence Confidence Guard.

Enforces strict confidence thresholds on retrieved evidence to prevent
hallucination or ungrounded synthesis when repository context is insufficient.
"""

from typing import List, Tuple, Optional
from pydantic import BaseModel, Field
from app.models.code_chunk import SearchResult


class EvidenceAssessment(BaseModel):
    is_sufficient: bool
    confidence_level: str = Field(..., description="'HIGH', 'MEDIUM', 'LOW', 'INSUFFICIENT'")
    confidence_score: float
    top_similarity: float
    evidence_count: int
    rejection_reason: Optional[str] = None


class HallucinationGuard:
    """Evaluates whether retrieved search chunks provide adequate evidence for grounded answering."""

    def __init__(
        self,
        min_similarity_threshold: float = 0.25,
        high_confidence_threshold: float = 0.60,
        medium_confidence_threshold: float = 0.40,
    ):
        self.min_similarity_threshold = min_similarity_threshold
        self.high_confidence_threshold = high_confidence_threshold
        self.medium_confidence_threshold = medium_confidence_threshold

    def evaluate_evidence(self, results: List[SearchResult]) -> EvidenceAssessment:
        """Assesses retrieval quality against calibrated confidence thresholds."""
        if not results:
            return EvidenceAssessment(
                is_sufficient=False,
                confidence_level="INSUFFICIENT",
                confidence_score=0.0,
                top_similarity=0.0,
                evidence_count=0,
                rejection_reason="I don't have enough evidence in the repository to answer this confidently.",
            )

        top_score = max(r.score for r in results)
        count = len(results)

        if top_score < self.min_similarity_threshold:
            return EvidenceAssessment(
                is_sufficient=False,
                confidence_level="INSUFFICIENT",
                confidence_score=round(top_score, 3),
                top_similarity=round(top_score, 3),
                evidence_count=count,
                rejection_reason="I don't have enough evidence in the repository to answer this confidently.",
            )

        if top_score >= self.high_confidence_threshold and count >= 2:
            level = "HIGH"
            conf = min(0.95, top_score + 0.1)
        elif top_score >= self.medium_confidence_threshold:
            level = "MEDIUM"
            conf = top_score
        else:
            level = "LOW"
            conf = max(0.35, top_score)

        return EvidenceAssessment(
            is_sufficient=True,
            confidence_level=level,
            confidence_score=round(conf, 3),
            top_similarity=round(top_score, 3),
            evidence_count=count,
            rejection_reason=None,
        )
