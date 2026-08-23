"""Configurable repository file and directory filtering system."""

import os
from pathlib import Path
from typing import Set, Optional
from app.config import settings


class FileFilter:
    """Filters files and directories to prevent noise, binaries, and oversized files from polluting the vector index."""

    def __init__(
        self,
        excluded_dirs: Optional[Set[str]] = None,
        excluded_extensions: Optional[Set[str]] = None,
        max_file_size_bytes: Optional[int] = None,
        custom_ignore_patterns: Optional[Set[str]] = None,
    ):
        self.excluded_dirs = excluded_dirs or set(settings.EXCLUDED_DIRS)
        self.excluded_extensions = excluded_extensions or set(settings.EXCLUDED_EXTENSIONS)
        self.max_file_size_bytes = max_file_size_bytes or settings.MAX_FILE_SIZE_BYTES
        self.custom_ignore_patterns = custom_ignore_patterns or set()

    def should_skip_directory(self, dir_name: str) -> bool:
        """Determines if a directory should be skipped entirely during traversal."""
        if dir_name in self.excluded_dirs:
            return True
        if dir_name.startswith(".") and dir_name != ".":
            return True
        for pattern in self.custom_ignore_patterns:
            if pattern in dir_name:
                return True
        return False

    def is_binary_or_media(self, file_path: Path) -> bool:
        """Checks file extension against known binary and media patterns."""
        name_lower = file_path.name.lower()
        # Direct extension match
        if file_path.suffix.lower() in self.excluded_extensions:
            return True
        # Compound extensions like .min.js or .d.ts.map
        if any(name_lower.endswith(ext) for ext in self.excluded_extensions):
            return True
        return False

    def is_file_too_large(self, file_path: Path) -> bool:
        """Checks if file size exceeds the configured byte threshold."""
        try:
            return file_path.stat().st_size > self.max_file_size_bytes
        except OSError:
            return True

    def is_supported_language_file(self, file_path: Path) -> bool:
        """Returns True if the file has a supported code extension."""
        return file_path.suffix.lower() in settings.SUPPORTED_EXTENSIONS

    def should_process_file(self, file_path: Path) -> bool:
        """Complete evaluation of whether a file should be ingested and parsed."""
        # Must be a regular file
        if not file_path.is_file():
            return False

        # Skip hidden files (e.g. .DS_Store, .env)
        if file_path.name.startswith("."):
            return False

        # Skip binary / media / lock files
        if self.is_binary_or_media(file_path):
            return False

        # Skip oversized files
        if self.is_file_too_large(file_path):
            return False

        # Only process supported source code languages for AST parsing
        if not self.is_supported_language_file(file_path):
            return False

        return True
