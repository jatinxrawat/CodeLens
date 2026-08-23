"""Structured observability logging with redaction for credentials and sensitive data."""

import logging
import time
import uuid
from typing import Optional, Dict, Any
from app.config import settings

# Configure root logger
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)

logger = logging.getLogger("code_intelligence")

REDACTED_PATTERNS = ["password", "secret", "token", "key", "authorization", "api_key"]


def sanitize_data(data: Any) -> Any:
    """Recursively redacts sensitive keys from dictionaries or strings."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if any(p in k.lower() for p in REDACTED_PATTERNS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_data(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(x) for x in data]
    return data


class StructuredLogger:
    """Helper for logging structured tracing metrics without logging proprietary source code."""

    @staticmethod
    def log_request_trace(
        request_id: str,
        repository_id: str,
        query: Optional[str] = None,
        retrieval_time_ms: float = 0.0,
        ranking_time_ms: float = 0.0,
        generation_time_ms: float = 0.0,
        total_time_ms: float = 0.0,
        number_of_sources: int = 0,
        model_version: str = "v1",
        status: str = "success",
    ):
        trace = {
            "request_id": request_id,
            "repository_id": repository_id,
            "query_length": len(query) if query else 0,
            "retrieval_time_ms": round(retrieval_time_ms, 2),
            "ranking_time_ms": round(ranking_time_ms, 2),
            "generation_time_ms": round(generation_time_ms, 2),
            "total_time_ms": round(total_time_ms, 2),
            "number_of_sources": number_of_sources,
            "model_version": model_version,
            "status": status,
        }
        logger.info(f"REQUEST_TRACE: {trace}")
