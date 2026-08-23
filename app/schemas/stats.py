"""Pydantic schemas for repository statistics and performance telemetry."""

from typing import Dict, Optional, List
from pydantic import BaseModel


class RepositoryStatsResponse(BaseModel):
    repository_id: str
    repository_name: str
    source: str
    indexed_at: str
    total_files: int
    total_chunks: int
    total_lines_of_code: int
    languages: Dict[str, int]
    chunk_types: Dict[str, int]
    embedding_model: str
    embedding_dimension: int
    ingestion_time_sec: float
    parsing_time_sec: float
    embedding_time_sec: float
    indexing_time_sec: float
    total_pipeline_time_sec: float
    avg_search_latency_ms: Optional[float] = None
    p95_search_latency_ms: Optional[float] = None
