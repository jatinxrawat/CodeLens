"""Pydantic schemas for static dependency and import graph."""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    type: Literal["file", "external_package", "module"]
    language: Optional[str] = None
    path: str
    size_bytes: Optional[int] = None
    in_degree: int = 0
    out_degree: int = 0


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship_type: Literal["import_relationship", "external_import", "containment", "inferred_relationship"]
    is_static: bool = True
    raw_import: Optional[str] = None


class GraphResponse(BaseModel):
    repository_id: str
    total_nodes: int
    total_edges: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]
