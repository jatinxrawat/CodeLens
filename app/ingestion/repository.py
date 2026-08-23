"""Repository management for cloning remote Git repositories and ingesting local directories."""

import os
import re
import shutil
from pathlib import Path
from typing import Tuple, Optional
import git
from app.config import settings


class RepositoryManager:
    """Manages cloning, validating, and preparing repositories for ingestion."""

    def __init__(self, target_dir: Optional[Path] = None):
        self.target_dir = target_dir or settings.REPOSITORIES_DIR
        self.target_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def extract_repo_name(source: str) -> str:
        """Extracts a clean, normalized repository name from a URL or file path."""
        # Handle remote Git URL: https://github.com/user/repo.git or git@github.com:user/repo.git
        if source.startswith(("http://", "https://", "git@", "ssh://")):
            clean_url = source.rstrip("/")
            if clean_url.endswith(".git"):
                clean_url = clean_url[:-4]
            name = clean_url.split("/")[-1].split(":")[-1]
            return re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
        else:
            # Handle local path
            path = Path(source).resolve()
            return re.sub(r"[^a-zA-Z0-9_\-]", "_", path.name)

    def clone_repository(self, git_url: str, force_reclone: bool = False) -> Tuple[str, Path]:
        """Clones a remote git repository using a shallow clone (--depth 1) for speed and efficiency."""
        repo_name = self.extract_repo_name(git_url)
        clone_destination = self.target_dir / repo_name

        if clone_destination.exists():
            if force_reclone:
                shutil.rmtree(clone_destination, ignore_errors=True)
            else:
                return repo_name, clone_destination

        try:
            # Shallow clone depth=1 to minimize bandwidth and storage
            git.Repo.clone_from(git_url, str(clone_destination), depth=1)
            return repo_name, clone_destination
        except Exception as e:
            if clone_destination.exists():
                shutil.rmtree(clone_destination, ignore_errors=True)
            raise RuntimeError(f"Failed to clone repository from {git_url}: {e}") from e

    def prepare_local_repository(self, local_path: Path) -> Tuple[str, Path]:
        """Validates and prepares a local directory for ingestion."""
        resolved_path = Path(local_path).resolve()
        if not resolved_path.exists():
            raise FileNotFoundError(f"Local path does not exist: {local_path}")
        if not resolved_path.is_dir():
            raise NotADirectoryError(f"Provided path is not a directory: {local_path}")

        repo_name = self.extract_repo_name(str(resolved_path))
        return repo_name, resolved_path
