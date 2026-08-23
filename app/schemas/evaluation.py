"""Pydantic schemas for retrieval evaluation and benchmark comparison."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    dataset_path: Optional[str] = Field(default=None, description="Optional custom benchmark JSON path")
    top_k: int = Field(default=5, ge=1, le=20)


class ModelComparisonResult(BaseModel):
    mode: str
    alpha: float
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    mean_reciprocal_rank: float
    avg_latency_ms: float


class EvaluationResponse(BaseModel):
    repository_id: str
    total_queries: int
    comparisons: List[ModelComparisonResult]
    query_breakdown: List[Dict[str, Any]]
