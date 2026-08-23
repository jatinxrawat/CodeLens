"""Pydantic schemas for repository comparison."""

from typing import Dict, Any
from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    repo_a: str = Field(..., description="First repository ID")
    repo_b: str = Field(..., description="Second repository ID to compare against")


class RepoComparisonResult(BaseModel):
    repo_a_id: str
    repo_b_id: str
    repo_a: Dict[str, Any]
    repo_b: Dict[str, Any]
