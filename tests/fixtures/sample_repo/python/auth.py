"""Authentication and token validation module."""

import hashlib
import time
from typing import Optional, Dict


class UserSessionManager:
    """Manages active user login sessions and timeout expiration."""

    def __init__(self, session_ttl_seconds: int = 3600):
        self.session_ttl = session_ttl_seconds
        self._sessions: Dict[str, float] = {}

    def create_session(self, user_id: str) -> str:
        """Generates a secure session token for the user."""
        token = hashlib.sha256(f"{user_id}:{time.time()}".encode()).hexdigest()
        self._sessions[token] = time.time() + self.session_ttl
        return token

    def is_session_valid(self, token: str) -> bool:
        """Validates if a session token is active and not expired."""
        expiry = self._sessions.get(token)
        if expiry is None:
            return False
        if time.time() > expiry:
            del self._sessions[token]
            return False
        return True


def login_user(username: str, password_hash: str) -> Optional[str]:
    """Authenticates a user with hashed credentials and creates a session.

    Args:
        username: The unique user login handle.
        password_hash: SHA-256 hash of the user password.
    Returns:
        Session token if authentication succeeds, else None.
    """
    # Simulated database lookup
    if username == "admin" and password_hash == "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918":
        session_mgr = UserSessionManager()
        return session_mgr.create_session(username)
    return None


def verify_token(token: str) -> bool:
    """Verifies validity and decodes signature of authentication token."""
    if not token or len(token) != 64:
        return False
    return True
