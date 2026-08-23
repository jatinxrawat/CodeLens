"""Core source code parsing orchestrator."""

from pathlib import Path
from typing import List, Optional
from app.models.code_chunk import CodeChunk
from app.ingestion.file_discovery import DiscoveredFile
from app.parsing.language_registry import LanguageRegistry, default_registry
from app.parsing.tree_sitter_parser import TreeSitterParserManager


class CodeParser:
    """Orchestrates source code parsing into structural CodeChunks across all supported languages."""

    def __init__(self, registry: Optional[LanguageRegistry] = None):
        self.registry = registry or default_registry

    def parse_file(
        self,
        file_path: Path,
        repo_name: str,
        relative_path: Optional[str] = None,
    ) -> List[CodeChunk]:
        """Parses a single file into structural chunks using Tree-sitter AST or fallback chunking."""
        file_path = Path(file_path)
        rel_path = relative_path or file_path.name
        ext = file_path.suffix.lower()

        parser = self.registry.get_parser_by_extension(ext)
        if not parser:
            return []

        try:
            source_bytes = file_path.read_bytes()
        except OSError:
            return []

        if not source_bytes.strip():
            return []

        try:
            # Generate Tree-sitter AST Tree
            tree = TreeSitterParserManager.parse(source_bytes, parser.language_name)
            chunks = parser.extract_chunks(tree, source_bytes, rel_path, repo_name)
            return chunks
        except Exception:
            # If Tree-sitter AST parsing fails on syntax errors/partial code, gracefully use fallback sliding window
            return parser.create_fallback_chunks(source_bytes, rel_path, repo_name)

    def parse_discovered_files(
        self,
        discovered_files: List[DiscoveredFile],
        repo_name: str,
    ) -> List[CodeChunk]:
        """Parses a batch of discovered repository files into structural code chunks."""
        all_chunks: List[CodeChunk] = []

        for item in discovered_files:
            file_chunks = self.parse_file(
                file_path=item.full_path,
                repo_name=repo_name,
                relative_path=item.relative_path,
            )
            all_chunks.extend(file_chunks)

        return all_chunks
