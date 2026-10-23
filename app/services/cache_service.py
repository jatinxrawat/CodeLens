"""SQLite caching and persistence layer for embeddings, answers, GitHub feeds, and user bookmarks."""

import sqlite3
import json
import time
import hashlib
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from app.config import settings
from app.utils.logger import logger


class CacheService:
    """Thread-safe SQLite persistent cache for CodeLens."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.CACHE_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=20.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS answer_cache (
                    cache_key TEXT PRIMARY KEY,
                    answer TEXT NOT NULL,
                    sources TEXT,
                    reasoning_evidence TEXT,
                    confidence_score REAL,
                    latency_ms REAL,
                    created_at REAL
                );

                CREATE TABLE IF NOT EXISTS embedding_cache (
                    text_hash TEXT PRIMARY KEY,
                    vector_blob BLOB NOT NULL,
                    dimension INTEGER NOT NULL,
                    created_at REAL
                );

                CREATE TABLE IF NOT EXISTS file_hash_cache (
                    repo_name TEXT,
                    file_path TEXT,
                    file_hash TEXT,
                    updated_at REAL,
                    PRIMARY KEY (repo_name, file_path)
                );

                CREATE TABLE IF NOT EXISTS explore_cache (
                    cache_key TEXT PRIMARY KEY,
                    data_json TEXT NOT NULL,
                    expires_at REAL
                );

                CREATE TABLE IF NOT EXISTS issue_enrichment_cache (
                    issue_key TEXT PRIMARY KEY,
                    enriched_json TEXT NOT NULL,
                    updated_at TEXT,
                    expires_at REAL
                );

                CREATE TABLE IF NOT EXISTS user_bookmarks (
                    user_id TEXT NOT NULL,
                    issue_id TEXT NOT NULL,
                    repo_name TEXT,
                    title TEXT,
                    url TEXT,
                    created_at REAL,
                    PRIMARY KEY (user_id, issue_id)
                );

                CREATE TABLE IF NOT EXISTS user_working (
                    user_id TEXT NOT NULL,
                    issue_id TEXT NOT NULL,
                    repo_name TEXT,
                    title TEXT,
                    url TEXT,
                    status TEXT,
                    created_at REAL,
                    PRIMARY KEY (user_id, issue_id)
                );

                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    avatar_url TEXT,
                    top_languages TEXT,
                    created_at REAL
                );

                CREATE TABLE IF NOT EXISTS ingestion_jobs (
                    job_id TEXT PRIMARY KEY,
                    repository_id TEXT NOT NULL,
                    repository_name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_step TEXT NOT NULL,
                    stage TEXT,
                    progress_pct INTEGER NOT NULL,
                    message TEXT,
                    error TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    duration_sec REAL NOT NULL
                );
                """
            )
            conn.commit()

    # ----------------- Answers Cache -----------------
    def make_answer_key(self, repo_id: str, commit_or_hash: str, query: str, mode: str) -> str:
        raw = f"{repo_id}:{commit_or_hash}:{query.strip().lower()}:{mode.lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get_cached_answer(self, cache_key: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT answer, sources, reasoning_evidence, confidence_score, latency_ms FROM answer_cache WHERE cache_key = ?",
                    (cache_key,),
                )
                row = cur.fetchone()
                if row:
                    return {
                        "answer": row["answer"],
                        "sources": json.loads(row["sources"]) if row["sources"] else [],
                        "reasoning_evidence": json.loads(row["reasoning_evidence"]) if row["reasoning_evidence"] else [],
                        "confidence_score": row["confidence_score"],
                        "latency_ms": row["latency_ms"],
                    }
        except Exception as e:
            logger.warning(f"Failed to read from answer cache: {e}")
        return None

    def set_cached_answer(
        self,
        cache_key: str,
        answer: str,
        sources: List[Dict[str, Any]],
        reasoning_evidence: List[Dict[str, Any]],
        confidence_score: float,
        latency_ms: float = 0.0,
    ):
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO answer_cache
                    (cache_key, answer, sources, reasoning_evidence, confidence_score, latency_ms, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cache_key,
                        answer,
                        json.dumps(sources),
                        json.dumps(reasoning_evidence),
                        confidence_score,
                        latency_ms,
                        time.time(),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to write to answer cache: {e}")

    # ----------------- Embedding Cache -----------------
    def get_cached_embeddings(self, texts: List[str]) -> Tuple[Dict[int, np.ndarray], List[int]]:
        """Returns {original_index: embedding_vector} for found entries, and missing indices."""
        found: Dict[int, np.ndarray] = {}
        missing_indices: List[int] = []

        if not texts:
            return found, missing_indices

        text_hashes = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in texts]

        try:
            with self._get_connection() as conn:
                for idx, th in enumerate(text_hashes):
                    cur = conn.execute(
                        "SELECT vector_blob, dimension FROM embedding_cache WHERE text_hash = ?",
                        (th,),
                    )
                    row = cur.fetchone()
                    if row:
                        vec = np.frombuffer(row["vector_blob"], dtype=np.float32)
                        found[idx] = vec
                    else:
                        missing_indices.append(idx)
        except Exception as e:
            logger.warning(f"Failed to read embeddings cache: {e}")
            missing_indices = list(range(len(texts)))

        return found, missing_indices

    def set_cached_embeddings(self, texts: List[str], vectors: np.ndarray):
        try:
            with self._get_connection() as conn:
                for text, vec in zip(texts, vectors):
                    th = hashlib.sha256(text.encode("utf-8")).hexdigest()
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO embedding_cache (text_hash, vector_blob, dimension, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (th, vec.astype(np.float32).tobytes(), len(vec), time.time()),
                    )
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to write embeddings cache: {e}")

    # ----------------- File Hash Cache (Incremental Indexing) -----------------
    def get_file_hashes(self, repo_name: str) -> Dict[str, str]:
        hashes: Dict[str, str] = {}
        try:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT file_path, file_hash FROM file_hash_cache WHERE repo_name = ?",
                    (repo_name,),
                )
                for row in cur.fetchall():
                    hashes[row["file_path"]] = row["file_hash"]
        except Exception as e:
            logger.warning(f"Failed to read file hash cache: {e}")
        return hashes

    def update_file_hashes(self, repo_name: str, file_hashes: Dict[str, str]):
        try:
            with self._get_connection() as conn:
                for path, f_hash in file_hashes.items():
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO file_hash_cache (repo_name, file_path, file_hash, updated_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (repo_name, path, f_hash, time.time()),
                    )
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to write file hash cache: {e}")

    # ----------------- GitHub Explore / Feeds Cache -----------------
    def get_explore_cache(self, cache_key: str) -> Optional[Any]:
        try:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT data_json, expires_at FROM explore_cache WHERE cache_key = ?",
                    (cache_key,),
                )
                row = cur.fetchone()
                if row:
                    if row["expires_at"] is None or row["expires_at"] > time.time():
                        return json.loads(row["data_json"])
        except Exception as e:
            logger.warning(f"Failed to read explore cache: {e}")
        return None

    def set_explore_cache(self, cache_key: str, data: Any, ttl_seconds: int = 14400):  # 4 hours default
        try:
            with self._get_connection() as conn:
                expires_at = time.time() + ttl_seconds
                conn.execute(
                    """
                    INSERT OR REPLACE INTO explore_cache (cache_key, data_json, expires_at)
                    VALUES (?, ?, ?)
                    """,
                    (cache_key, json.dumps(data), expires_at),
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to write explore cache: {e}")

    # ----------------- Issue Enrichment Cache -----------------
    def get_issue_enrichment(self, issue_id: str, updated_at: str) -> Optional[Dict[str, Any]]:
        issue_key = f"{issue_id}:{updated_at}"
        try:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT enriched_json, expires_at FROM issue_enrichment_cache WHERE issue_key = ?",
                    (issue_key,),
                )
                row = cur.fetchone()
                if row:
                    return json.loads(row["enriched_json"])
        except Exception as e:
            logger.warning(f"Failed to read issue enrichment cache: {e}")
        return None

    def set_issue_enrichment(self, issue_id: str, updated_at: str, enrichment: Dict[str, Any], ttl_seconds: int = 604800):
        issue_key = f"{issue_id}:{updated_at}"
        try:
            with self._get_connection() as conn:
                expires_at = time.time() + ttl_seconds
                conn.execute(
                    """
                    INSERT OR REPLACE INTO issue_enrichment_cache (issue_key, enriched_json, updated_at, expires_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (issue_key, json.dumps(enrichment), updated_at, expires_at),
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to write issue enrichment cache: {e}")

    # ----------------- User Bookmarks & Working Status -----------------
    def toggle_bookmark(self, user_id: str, issue_id: str, repo_name: str, title: str, url: str) -> bool:
        """Toggles bookmark state. Returns True if bookmarked, False if unbookmarked."""
        try:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT 1 FROM user_bookmarks WHERE user_id = ? AND issue_id = ?",
                    (user_id, issue_id),
                )
                if cur.fetchone():
                    conn.execute("DELETE FROM user_bookmarks WHERE user_id = ? AND issue_id = ?", (user_id, issue_id))
                    conn.commit()
                    return False
                else:
                    conn.execute(
                        "INSERT INTO user_bookmarks (user_id, issue_id, repo_name, title, url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (user_id, issue_id, repo_name, title, url, time.time()),
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.warning(f"Failed to toggle bookmark: {e}")
            return False

    def get_bookmarks(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT issue_id, repo_name, title, url, created_at FROM user_bookmarks WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.warning(f"Failed to fetch bookmarks: {e}")
            return []

    def toggle_working(self, user_id: str, issue_id: str, repo_name: str, title: str, url: str, status: str = "in_progress") -> bool:
        """Toggles working-on-this state. Returns True if added, False if removed."""
        try:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT 1 FROM user_working WHERE user_id = ? AND issue_id = ?",
                    (user_id, issue_id),
                )
                if cur.fetchone():
                    conn.execute("DELETE FROM user_working WHERE user_id = ? AND issue_id = ?", (user_id, issue_id))
                    conn.commit()
                    return False
                else:
                    conn.execute(
                        "INSERT INTO user_working (user_id, issue_id, repo_name, title, url, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (user_id, issue_id, repo_name, title, url, status, time.time()),
                    )
                    conn.commit()
                    return True
        except Exception as e:
            logger.warning(f"Failed to toggle working status: {e}")
            return False

    def get_working(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT issue_id, repo_name, title, url, status, created_at FROM user_working WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.warning(f"Failed to fetch working list: {e}")
            return []

    def save_user_profile(self, user_id: str, username: str, avatar_url: str, top_languages: List[str]):
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO user_profiles (user_id, username, avatar_url, top_languages, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, username, avatar_url, json.dumps(top_languages), time.time()),
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to save user profile: {e}")

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT user_id, username, avatar_url, top_languages FROM user_profiles WHERE user_id = ?",
                    (user_id,),
                )
                row = cur.fetchone()
                if row:
                    return {
                        "user_id": row["user_id"],
                        "username": row["username"],
                        "avatar_url": row["avatar_url"],
                        "top_languages": json.loads(row["top_languages"]) if row["top_languages"] else [],
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch user profile: {e}")
        return None

    # ----------------- Ingestion Jobs Persistence -----------------
    def save_job(self, job_data: Dict[str, Any]):
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO ingestion_jobs (
                        job_id, repository_id, repository_name, source, status, current_step,
                        stage, progress_pct, message, error, created_at, updated_at, duration_sec
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job_data.get("job_id"),
                        job_data.get("repository_id"),
                        job_data.get("repository_name"),
                        job_data.get("source"),
                        job_data.get("status"),
                        job_data.get("current_step"),
                        job_data.get("stage"),
                        job_data.get("progress_pct", 0),
                        job_data.get("message"),
                        job_data.get("error"),
                        job_data.get("created_at", time.time()),
                        job_data.get("updated_at", time.time()),
                        job_data.get("duration_sec", 0.0),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to persist job {job_data.get('job_id')}: {e}")

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT * FROM ingestion_jobs WHERE job_id = ?",
                    (job_id,),
                )
                row = cur.fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            logger.warning(f"Failed to fetch job {job_id}: {e}")
        return None

    def get_latest_job_for_repo(self, repo_name: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cur = conn.execute(
                    "SELECT * FROM ingestion_jobs WHERE repository_name = ? OR repository_id = ? ORDER BY created_at DESC LIMIT 1",
                    (repo_name, repo_name),
                )
                row = cur.fetchone()
                if row:
                    return dict(row)
        except Exception as e:
            logger.warning(f"Failed to fetch latest job for {repo_name}: {e}")
        return None


cache_service = CacheService()

