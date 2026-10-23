"""Per-user and IP-based Rate Limiter."""

import time
import threading
from typing import Dict, List, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException, status
from app.config import settings


class SlidingWindowRateLimiter:
    """Sliding-window in-memory rate limiter per client identifier."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60.0
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, client_id: str) -> Tuple[bool, int, float]:
        """Checks if request is allowed.
        Returns: (allowed: bool, remaining: int, retry_after: float)
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            # Filter timestamps inside current window
            timestamps = [t for t in self._history[client_id] if t > window_start]
            count = len(timestamps)

            if count >= self.requests_per_minute:
                # Calculate retry after based on the oldest timestamp in window
                oldest = timestamps[0]
                retry_after = max(1.0, oldest + self.window_seconds - now)
                self._history[client_id] = timestamps
                return False, 0, retry_after

            timestamps.append(now)
            self._history[client_id] = timestamps
            remaining = self.requests_per_minute - len(timestamps)
            return True, remaining, 0.0

    def cleanup(self):
        """Removes idle client records to prevent memory growth."""
        now = time.time()
        window_start = now - self.window_seconds
        with self._lock:
            keys_to_delete = [
                k for k, v in self._history.items() if not v or v[-1] < window_start
            ]
            for k in keys_to_delete:
                del self._history[k]


rate_limiter = SlidingWindowRateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)


def check_rate_limit(request: Request):
    """FastAPI dependency to enforce rate limiting on API endpoints."""
    # Extract client identifier: X-User-ID header or X-Forwarded-For or client host
    client_id = (
        request.headers.get("X-User-ID")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown-client")
    )

    allowed, remaining, retry_after = rate_limiter.is_allowed(client_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please wait {int(retry_after)} seconds before retrying.",
            headers={"Retry-After": str(int(retry_after))},
        )
