"""Pydantic schemas for local evidence-based reasoning and RAG Q&A."""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.reasoning.rag_pipeline import CitationSource, DecisionFactor


class AskRequest(BaseModel):
    repository_id: str = Field(..., description="Target repository ID")
    query: str = Field(..., description="User question (e.g. 'How is authentication handled?')")
    top_k: int = Field(default=5, ge=1, le=20)
    alpha: float = Field(default=0.6, ge=0.0, le=1.0)


class AskResponse(BaseModel):
    query: str
    repository_id: str
    category: str
    confidence_level: str
    confidence_score: float
    answer: str
    sources: List[CitationSource]
    reasoning_evidence: List[DecisionFactor]
    latency_ms: float
    is_sufficient_evidence: bool
