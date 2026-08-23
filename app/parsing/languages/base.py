"""Abstract base class and utilities for language-specific Tree-sitter AST parsers."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from tree_sitter import Node, Tree
from app.models.code_chunk import CodeChunk, ChunkType
from app.config import settings


class BaseLanguageParser(ABC):
    """Abstract base class for AST-based source code parsing across languages."""

    def __init__(self, language_name: str):
        self.language_name = language_name

    @abstractmethod
    def extract_chunks(
        self,
        tree: Tree,
        source_bytes: bytes,
        file_path: str,
        repo_name: str,
    ) -> List[CodeChunk]:
        """Extracts structural code chunks (functions, classes, interfaces, etc.) from AST tree."""
        pass

    def get_node_text(self, node: Node, source_bytes: bytes) -> str:
        """Decodes raw source slice for a given AST node."""
        return source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")

    def get_preceding_comment(self, node: Node, source_bytes: bytes) -> Optional[str]:
        """Extracts comment/docstring directly preceding an AST node if present."""
        prev = node.prev_named_sibling
        if prev and prev.type in {"comment", "block_comment", "line_comment"}:
            return self.get_node_text(prev, source_bytes).strip()
        return None

    def create_fallback_chunks(
        self,
        source_bytes: bytes,
        file_path: str,
        repo_name: str,
        max_lines: int = 100,
        overlap_lines: int = 20,
    ) -> List[CodeChunk]:
        """Fallback chunker for source files without identified AST symbols or unstructured scripts.

        Uses line-based sliding windows with overlap to ensure complete coverage without dropping code.
        """
        text = source_bytes.decode("utf-8", errors="replace")
        lines = text.splitlines(keepends=True)
        if not lines:
            return []

        chunks: List[CodeChunk] = []
        total_lines = len(lines)
        step = max(1, max_lines - overlap_lines)

        for start_idx in range(0, total_lines, step):
            end_idx = min(start_idx + max_lines, total_lines)
            chunk_lines = lines[start_idx:end_idx]
            chunk_text = "".join(chunk_lines).strip()
            if not chunk_text:
                continue

            start_line = start_idx + 1
            end_line = end_idx

            chunk_id = CodeChunk.generate_id(repo_name, file_path, start_line, end_line, f"block_{start_line}")
            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    repo_name=repo_name,
                    file_path=file_path,
                    language=self.language_name,
                    chunk_type=ChunkType.BLOCK,
                    symbol_name=f"lines_{start_line}_{end_line}",
                    start_line=start_line,
                    end_line=end_line,
                    code=chunk_text,
                    docstring=None,
                    context_prefix=None,
                )
            )
            if end_idx >= total_lines:
                break

        return chunks
