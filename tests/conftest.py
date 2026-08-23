"""Shared pytest fixtures."""

import pytest
from pathlib import Path
from app.config import settings
from app.ingestion.filters import FileFilter
from app.ingestion.file_discovery import FileDiscovery
from app.parsing.parser import CodeParser


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_repo_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample_repo"


@pytest.fixture
def file_filter() -> FileFilter:
    return FileFilter()


@pytest.fixture
def file_discovery(file_filter: FileFilter) -> FileDiscovery:
    return FileDiscovery(file_filter=file_filter)


@pytest.fixture
def code_parser() -> CodeParser:
    return CodeParser()
