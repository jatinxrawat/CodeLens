"""Repository file discovery and language identification engine."""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from app.config import settings
from app.ingestion.filters import FileFilter


class DiscoveredFile(BaseModel):
    """Represents a discovered source code file ready for parsing."""
    full_path: Path
    relative_path: str
    language: str
    size_bytes: int


class FileDiscovery:
    """Discovers source code files within a repository using optimized tree walking and pruning."""

    def __init__(self, file_filter: Optional[FileFilter] = None):
        self.file_filter = file_filter or FileFilter()

    def discover_files(self, repo_path: Path) -> List[DiscoveredFile]:
        """Walks the repository root, pruning excluded directories in-place and returning valid source files."""
        repo_path = Path(repo_path).resolve()
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

        discovered: List[DiscoveredFile] = []

        for root, dirs, files in os.walk(repo_path, topdown=True):
            # Prune excluded directories IN-PLACE to avoid descending into them
            dirs[:] = [d for d in dirs if not self.file_filter.should_skip_directory(d)]

            current_dir = Path(root)
            for file_name in sorted(files):
                file_path = current_dir / file_name
                if self.file_filter.should_process_file(file_path):
                    try:
                        rel_path = str(file_path.relative_to(repo_path))
                        ext = file_path.suffix.lower()
                        lang = settings.SUPPORTED_EXTENSIONS.get(ext, "unknown")
                        size = file_path.stat().st_size
                        total_size = sum(f.size_bytes for f in discovered) + size
                        if total_size > settings.MAX_REPO_SIZE_MB * 1024 * 1024:
                            raise ValueError(
                                f"Repository size exceeds maximum configured limit of {settings.MAX_REPO_SIZE_MB}MB."
                            )

                        if len(discovered) >= settings.MAX_FILES_COUNT:
                            raise ValueError(
                                f"Repository file count exceeds maximum configured limit of {settings.MAX_FILES_COUNT} files."
                            )

                        discovered.append(
                            DiscoveredFile(
                                full_path=file_path,
                                relative_path=rel_path,
                                language=lang,
                                size_bytes=size,
                            )
                        )
                    except (OSError, ValueError) as e:
                        if "exceeds maximum" in str(e):
                            raise e
                        continue

        return discovered
