"""Pydantic schemas for static analysis, flow tracing, and impact evaluation."""

from typing import List, Optional
from pydantic import BaseModel, Field


class FlowTraceRequest(BaseModel):
    symbol: str = Field(..., description="Function or method symbol name to trace")
    file_path: Optional[str] = Field(default=None, description="Optional target file path")


class ImpactRequest(BaseModel):
    target: str = Field(..., description="Target file path (e.g. 'src/auth.py') or symbol name")
