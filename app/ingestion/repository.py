"""Repository management for cloning remote Git repositories and ingesting local directories."""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Tuple, Optional
import git
from app.config import settings
from app.utils.logger import logger


class RepositoryManager:
    """Manages cloning, validating, and preparing repositories for ingestion."""

    def __init__(self, target_dir: Optional[Path] = None):
        self.target_dir = target_dir or settings.REPOSITORIES_DIR
        self.target_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def is_git_available() -> bool:
        """Verifies if the git executable is installed and accessible in system PATH."""
        return shutil.which("git") is not None

    @staticmethod
    def normalize_clone_url(source: str) -> str:
        """Normalizes user input into a valid git clone URL.

        Accepts:
        - 'pallets/click' -> 'https://github.com/pallets/click.git'
        - 'https://github.com/pallets/click' -> 'https://github.com/pallets/click.git'
        - 'https://github.com/pallets/click.git' -> 'https://github.com/pallets/click.git'
        - 'git@github.com:pallets/click.git' -> 'git@github.com:pallets/click.git'
        """
        raw = source.strip()
        if not raw:
            raise ValueError("Repository URL or identifier cannot be empty.")

        # Shorthand 'owner/repo' without protocol
        if not raw.startswith(("http://", "https://", "git@", "ssh://")):
            # Remove any leading github.com/ if user typed that without protocol
            if raw.startswith("github.com/"):
                raw = raw[len("github.com/"):]
            parts = [p for p in raw.split("/") if p]
            if len(parts) == 2:
                owner, repo = parts[0], parts[1]
                if repo.endswith(".git"):
                    repo = repo[:-4]
                return f"https://github.com/{owner}/{repo}.git"
            else:
                raise ValueError(
                    f"Invalid repository specification '{source}'. Please provide 'owner/repo' or a full git URL."
                )

        clean_url = raw.rstrip("/")
        if not clean_url.endswith(".git") and not clean_url.startswith("git@"):
            clean_url = f"{clean_url}.git"
        return clean_url

    @staticmethod
    def extract_repo_name(source: str) -> str:
        """Extracts a clean, normalized repository name from a URL or file path."""
        try:
            norm = RepositoryManager.normalize_clone_url(source)
            clean = norm.rstrip("/")
            if clean.endswith(".git"):
                clean = clean[:-4]
            name = clean.split("/")[-1].split(":")[-1]
            return re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
        except Exception:
            clean_url = source.strip().rstrip("/")
            if clean_url.endswith(".git"):
                clean_url = clean_url[:-4]
            name = clean_url.split("/")[-1].split(":")[-1]
            return re.sub(r"[^a-zA-Z0-9_\-]", "_", name)

    def clone_repository(
        self,
        git_url: str,
        force_reclone: bool = False,
        timeout_sec: int = 60,
    ) -> Tuple[str, Path]:
        """Clones a remote git repository using a shallow clone (--depth 1) with timeout and credential protection."""
        if not self.is_git_available():
            raise RuntimeError("Git executable is not installed or not found in system PATH. Please install git.")

        normalized_url = self.normalize_clone_url(git_url)
        repo_name = self.extract_repo_name(normalized_url)
        clone_destination = self.target_dir / repo_name

        if clone_destination.exists():
            if force_reclone:
                shutil.rmtree(clone_destination, ignore_errors=True)
            else:
                logger.info(f"Repository directory already exists for {repo_name}, reusing existing clone.")
                return repo_name, clone_destination

        # Clone using subprocess with strict non-interactive environment and timeout
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GIT_ASKPASS"] = ""

        try:
            cmd = ["git", "clone", "--depth", "1", normalized_url, str(clone_destination)]
            logger.info(f"Starting git clone for {normalized_url} (timeout={timeout_sec}s)...")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            if result.returncode != 0:
                err_msg = result.stderr.strip() or result.stdout.strip() or "Unknown git error"
                if clone_destination.exists():
                    shutil.rmtree(clone_destination, ignore_errors=True)
                raise RuntimeError(f"Git clone failed: {err_msg}")

            logger.info(f"Successfully cloned {repo_name} to {clone_destination}")
            return repo_name, clone_destination
        except subprocess.TimeoutExpired:
            if clone_destination.exists():
                shutil.rmtree(clone_destination, ignore_errors=True)
            raise TimeoutError(f"Git clone timed out after {timeout_sec}s for {normalized_url}")
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

