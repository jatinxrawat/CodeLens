"""Pydantic schemas for semantic and hybrid code search."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    repository_id: str = Field(..., description="Target repository name or ID")
    query: str = Field(..., description="Natural language question or code keyword query")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of ranked chunks to retrieve")
    mode: Literal["hybrid", "vector", "keyword"] = Field(
        default="hybrid",
        description="Retrieval engine mode: 'hybrid' (BM25 + FAISS), 'vector' (Dense only), 'keyword' (BM25 only)",
    )
    alpha: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Hybrid fusion weight (1.0 = pure vector, 0.0 = pure BM25)",
    )


class SearchResultItem(BaseModel):
    file_path: str
    symbol: Optional[str] = None
    language: str
    chunk_type: str
    start_line: int
    end_line: int
    similarity: float
    code: str
    docstring: Optional[str] = None
    context_prefix: Optional[str] = None
    rank: int


class SearchResponse(BaseModel):
    query: str
    repository_id: str
    mode: str
    alpha: float
    latency_ms: float
    total_results: int
    results: List[SearchResultItem]
