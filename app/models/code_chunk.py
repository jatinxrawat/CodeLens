"""Data models for structural code representation, search, and evaluation."""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import hashlib


class ChunkType(str, Enum):
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    MODULE = "module"
    BLOCK = "block"


class CodeChunk(BaseModel):
    """Represents a structural code chunk extracted via AST parsing."""
    chunk_id: str = Field(..., description="Unique identifier computed from repo, file path, and line range")
    repo_name: str = Field(..., description="Name of the repository")
    file_path: str = Field(..., description="Relative path of file within repository")
    language: str = Field(..., description="Programming language (e.g. python, javascript)")
    chunk_type: ChunkType = Field(default=ChunkType.FUNCTION, description="Type of AST element")
    symbol_name: Optional[str] = Field(default=None, description="Identifier name (e.g. function or class name)")
    start_line: int = Field(..., description="1-indexed starting line number")
    end_line: int = Field(..., description="1-indexed ending line number")
    code: str = Field(..., description="Raw source code content")
    docstring: Optional[str] = Field(default=None, description="Extracted docstring or block comment")
    context_prefix: Optional[str] = Field(default=None, description="Surrounding parent context (e.g. class or module)")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeChunk":
        """Constructs a CodeChunk from dictionary data."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes CodeChunk to dictionary."""
        return self.model_dump() if hasattr(self, "model_dump") else self.dict()

    @classmethod
    def generate_id(cls, repo_name: str, file_path: str, start_line: int, end_line: int, symbol: Optional[str] = None) -> str:
        """Deterministically generates a chunk ID."""
        raw_key = f"{repo_name}:{file_path}:{start_line}-{end_line}:{symbol or ''}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

    def get_embeddable_text(self) -> str:
        """Produces an enriched textual representation optimized for semantic vector embeddings.

        Embedding source code alone can miss architectural intent. By prefixing the chunk
        with file path, language, AST symbol type, and docstring, the embedding model can
        bridge natural language queries (e.g. 'how does authentication work?') with the
        underlying implementation.
        """
        parts = []
        parts.append(f"File: {self.file_path}")
        parts.append(f"Language: {self.language}")
        if self.symbol_name:
            parts.append(f"{self.chunk_type.value.capitalize()}: {self.symbol_name}")
        if self.context_prefix:
            parts.append(f"Scope: {self.context_prefix}")
        if self.docstring:
            parts.append(f"Description: {self.docstring.strip()}")
        parts.append(f"Code:\n{self.code.strip()}")
        return "\n".join(parts)


class SearchResult(BaseModel):
    """Represents a ranked semantic search match."""
    chunk: CodeChunk
    score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    rank: int = Field(..., description="1-indexed ranking position")


class IndexMetadata(BaseModel):
    """Metadata summary stored alongside the FAISS index."""
    repo_name: str
    repo_source: str  # local path or git URL
    indexed_at: str
    total_files: int
    total_chunks: int
    languages: Dict[str, int]
    chunk_types: Dict[str, int]
    embedding_model: str
    embedding_dimension: int
    ingestion_time_sec: float
    parsing_time_sec: float
    embedding_time_sec: float
    indexing_time_sec: float
    total_time_sec: float


class EvaluationQuery(BaseModel):
    """A ground truth benchmark test case."""
    query: str
    expected_file: str
    expected_symbol: Optional[str] = None
    category: Optional[str] = "general"


class EvaluationResult(BaseModel):
    """Result of benchmark evaluation on retrieval quality."""
    total_queries: int
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    mean_reciprocal_rank: float
    query_evaluations: List[Dict[str, Any]]
