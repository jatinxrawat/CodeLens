"""Unit tests for repository discovery and file filtering."""

from pathlib import Path
from app.ingestion.filters import FileFilter
from app.ingestion.file_discovery import FileDiscovery
from app.ingestion.repository import RepositoryManager


def test_file_filtering_exclusions(file_filter: FileFilter):
    # Directories to skip
    assert file_filter.should_skip_directory("node_modules") is True
    assert file_filter.should_skip_directory(".git") is True
    assert file_filter.should_skip_directory("__pycache__") is True
    assert file_filter.should_skip_directory(".venv") is True
    assert file_filter.should_skip_directory("src") is False

    # Binary/media extensions to ignore
    assert file_filter.is_binary_or_media(Path("image.png")) is True
    assert file_filter.is_binary_or_media(Path("model.pkl")) is False  # not binary extension unless added
    assert file_filter.is_binary_or_media(Path("lib.so")) is True
    assert file_filter.is_binary_or_media(Path("bundle.min.js")) is True
    assert file_filter.is_binary_or_media(Path("main.py")) is False

    # Supported language files
    assert file_filter.is_supported_language_file(Path("main.py")) is True
    assert file_filter.is_supported_language_file(Path("index.js")) is True
    assert file_filter.is_supported_language_file(Path("app.ts")) is True
    assert file_filter.is_supported_language_file(Path("Service.java")) is True
    assert file_filter.is_supported_language_file(Path("cache.cpp")) is True
    assert file_filter.is_supported_language_file(Path("memory.c")) is True
    assert file_filter.is_supported_language_file(Path("readme.md")) is False


def test_file_discovery_on_sample_repo(file_discovery: FileDiscovery, sample_repo_path: Path):
    discovered = file_discovery.discover_files(sample_repo_path)
    rel_paths = [f.relative_path for f in discovered]

    # Should discover supported files
    assert any("python/auth.py" in p for p in rel_paths)
    assert any("javascript/user.js" in p for p in rel_paths)
    assert any("typescript/payment.ts" in p for p in rel_paths)
    assert any("java/OrderService.java" in p for p in rel_paths)
    assert any("cpp/cache.cpp" in p for p in rel_paths)
    assert any("c/memory.c" in p for p in rel_paths)

    # Should NOT discover noise files in node_modules or dist/bundle.min.js
    assert not any("node_modules" in p for p in rel_paths)
    assert not any("bundle.min.js" in p for p in rel_paths)


def test_repository_name_extraction():
    assert RepositoryManager.extract_repo_name("https://github.com/pallets/click.git") == "click"
    assert RepositoryManager.extract_repo_name("git@github.com:facebook/react.git") == "react"
    assert RepositoryManager.extract_repo_name("/Users/dev/my-project") == "my-project"
