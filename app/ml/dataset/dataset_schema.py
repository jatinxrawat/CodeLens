"""Data schemas for trainable ranking and maintainability datasets."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RankingSample(BaseModel):
    """A single (query, code_chunk) pair with binary or graded relevance label."""
    query: str = Field(..., description="Developer inquiry or natural language question")
    code_chunk_id: str = Field(..., description="Unique ID of candidate code chunk")
    repository_id: str = Field(..., description="Repository where the chunk resides")
    file_path: str = Field(..., description="Source file relative path")
    symbol_name: Optional[str] = Field(default=None, description="Function, class, or method identifier")
    language: str = Field(..., description="Programming language")
    code_text: str = Field(..., description="Raw code text of candidate chunk")
    label: int = Field(..., description="Relevance label: binary (0, 1) or graded (0=irrelevant, 1=weak, 2=relevant, 3=highly relevant)")
    expected_source: bool = Field(default=False, description="Whether this chunk is a ground-truth expected source")


class RankingDataset(BaseModel):
    """Complete dataset for code ranking."""
    version: str = "1.0.0"
    created_at: str
    total_samples: int
    train_repositories: List[str]
    val_repositories: List[str]
    test_repositories: List[str]
    samples: List[RankingSample]
    statistics: Dict[str, Any] = Field(default_factory=dict)


class MaintainabilitySample(BaseModel):
    """A single code chunk feature vector with maintainability risk label."""
    chunk_id: str
    repository_id: str
    file_path: str
    symbol_name: Optional[str]
    language: str
    features: Dict[str, float] = Field(..., description="Extracted numerical code complexity features")
    risk_label: str = Field(..., description="Risk label: 'LOW', 'MEDIUM', or 'HIGH'")
    numeric_label: int = Field(..., description="Numeric label: 0=LOW, 1=MEDIUM, 2=HIGH")


class MaintainabilityDataset(BaseModel):
    """Complete dataset for code maintainability risk prediction."""
    version: str = "1.0.0"
    created_at: str
    total_samples: int
    train_repositories: List[str]
    val_repositories: List[str]
    test_repositories: List[str]
    samples: List[MaintainabilitySample]
    statistics: Dict[str, Any] = Field(default_factory=dict)
