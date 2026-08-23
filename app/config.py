"""Configuration management for Local AI Code Intelligence Engine (Phase 2)."""

import os
from pathlib import Path
from typing import List, Set
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load optional .env file
load_dotenv()


class Settings(BaseModel):
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
    REPOSITORIES_DIR: Path = DATA_DIR / "repositories"
    INDEXES_DIR: Path = Path(os.getenv("VECTOR_INDEX_PATH", str(DATA_DIR / "indexes")))
    BM25_INDEX_DIR: Path = Path(os.getenv("BM25_INDEX_PATH", str(DATA_DIR / "indexes")))
    MODELS_DIR: Path = BASE_DIR / "models"
    ML_RANKER_PATH: Path = Path(os.getenv("ML_RANKER_PATH", str(MODELS_DIR / "retrieval_ranker" / "v1")))
    MAINTAINABILITY_MODEL_PATH: Path = Path(os.getenv("MAINTAINABILITY_MODEL_PATH", str(MODELS_DIR / "maintainability" / "v1")))
    STATIC_DIR: Path = BASE_DIR / "frontend" / "dist"

    # LLM Settings (100% Local Inference)
    LLM_MODEL: str = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-Coder-1.5B-Instruct")
    MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "2048"))
    MAX_SOURCES: int = int(os.getenv("MAX_SOURCES", "5"))
    MAX_LLM_OUTPUT_TOKENS: int = int(os.getenv("MAX_LLM_OUTPUT_TOKENS", "1024"))

    # Embedding Model Settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"))
    EMBEDDING_MODEL_NAME: str = EMBEDDING_MODEL
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "auto")  # 'auto', 'cpu', 'cuda', or 'mps'

    # Retrieval & Hybrid Search Settings
    TOP_K: int = int(os.getenv("TOP_K", os.getenv("DEFAULT_TOP_K", "5")))
    DEFAULT_TOP_K: int = TOP_K
    DEFAULT_HYBRID_ALPHA: float = float(os.getenv("DEFAULT_HYBRID_ALPHA", "0.6"))  # 0.6 semantic + 0.4 keyword
    BM25_K1: float = float(os.getenv("BM25_K1", "1.5"))
    BM25_B: float = float(os.getenv("BM25_B", "0.75"))

    # Observability & Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Resource & Security Limits
    MAX_REPO_SIZE_MB: int = int(os.getenv("MAX_REPO_SIZE_MB", "200"))
    MAX_FILE_SIZE_BYTES: int = int(os.getenv("MAX_FILE_SIZE_BYTES", str(500 * 1024)))  # 500 KB limit
    MAX_FILES_COUNT: int = int(os.getenv("MAX_FILES_COUNT", "5000"))
    MAX_CHUNK_LINES: int = int(os.getenv("MAX_CHUNK_LINES", "300"))

    # Excluded directories
    EXCLUDED_DIRS: Set[str] = {
        ".git",
        ".svn",
        ".hg",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".venv",
        "venv",
        "env",
        "ENV",
        "dist",
        "build",
        "target",
        "out",
        ".idea",
        ".vscode",
        "bin",
        "obj",
        ".next",
        ".nuxt",
        "coverage",
        ".turbo",
        "vendor",
    }

    # Excluded file extensions
    EXCLUDED_EXTENSIONS: Set[str] = {
        ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a", ".lib", ".pyc", ".pyo", ".pyd", ".class",
        ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
        ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf", ".mp4", ".mp3", ".wav", ".woff", ".woff2", ".ttf", ".eot",
        ".lock", ".min.js", ".min.css", ".map", ".sqlite", ".db",
    }

    # Supported source code language extensions
    SUPPORTED_EXTENSIONS: dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".hh": "cpp",
        ".h": "cpp",
        ".c": "c",
    }


settings = Settings()
