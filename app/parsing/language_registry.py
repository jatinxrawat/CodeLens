"""Extensible language parser registry."""

from typing import Dict, Type, Optional, List
from app.parsing.languages.base import BaseLanguageParser
from app.parsing.languages.python import PythonParser
from app.parsing.languages.javascript import JavaScriptParser
from app.parsing.languages.typescript import TypeScriptParser
from app.parsing.languages.java import JavaParser
from app.parsing.languages.cpp import CppParser
from app.parsing.languages.c import CParser


class LanguageRegistry:
    """Registry mapping languages and file extensions to their corresponding AST parser implementations.

    Designed for open-closed extensibility: new languages can be registered at runtime
    without modifying the core parser engine.
    """

    def __init__(self):
        self._parsers: Dict[str, BaseLanguageParser] = {}
        self._extension_map: Dict[str, str] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Registers the 6 core languages supported in Phase 1."""
        self.register_language("python", [".py"], PythonParser())
        self.register_language("javascript", [".js", ".jsx", ".mjs", ".cjs"], JavaScriptParser())
        self.register_language("typescript", [".ts", ".tsx"], TypeScriptParser())
        self.register_language("java", [".java"], JavaParser())
        self.register_language("cpp", [".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h"], CppParser())
        self.register_language("c", [".c"], CParser())

    def register_language(
        self,
        language_name: str,
        extensions: List[str],
        parser_instance: BaseLanguageParser,
    ):
        """Registers a new language parser and its associated file extensions."""
        self._parsers[language_name.lower()] = parser_instance
        for ext in extensions:
            self._extension_map[ext.lower()] = language_name.lower()

    def get_parser_by_language(self, language_name: str) -> Optional[BaseLanguageParser]:
        """Retrieves parser instance for a given language name."""
        return self._parsers.get(language_name.lower())

    def get_parser_by_extension(self, extension: str) -> Optional[BaseLanguageParser]:
        """Retrieves parser instance for a given file extension (e.g. '.py')."""
        lang = self._extension_map.get(extension.lower())
        if lang:
            return self.get_parser_by_language(lang)
        return None

    def get_supported_languages(self) -> List[str]:
        """Returns list of registered language names."""
        return sorted(list(self._parsers.keys()))


# Global default registry singleton
default_registry = LanguageRegistry()
