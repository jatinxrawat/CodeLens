"""Tree-sitter parser manager and AST tree generator."""

from typing import Dict, Optional
import tree_sitter_languages
from tree_sitter import Parser, Language, Tree


class TreeSitterParserManager:
    """Manages tree-sitter parser instances and language grammar loaders."""

    _parsers: Dict[str, Parser] = {}

    @classmethod
    def get_parser(cls, language_name: str) -> Parser:
        """Retrieves or creates a cached Tree-sitter Parser for a given language."""
        if language_name in cls._parsers:
            return cls._parsers[language_name]

        try:
            parser = tree_sitter_languages.get_parser(language_name)
            cls._parsers[language_name] = parser
            return parser
        except Exception as e:
            raise ValueError(f"Failed to load Tree-sitter grammar for language '{language_name}': {e}") from e

    @classmethod
    def parse(cls, source_bytes: bytes, language_name: str) -> Tree:
        """Parses raw source code bytes into a Tree-sitter AST Tree."""
        parser = cls.get_parser(language_name)
        return parser.parse(source_bytes)
