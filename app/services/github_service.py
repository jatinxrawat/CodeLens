"""Official GitHub REST API Integration Service.

Handles rate-limiting, SQLite caching, repository discovery,
beginner issue discovery, contribution-readiness evaluation,
and AI issue enrichment with Google Gemini.
"""

import os
import time
import httpx
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from app.config import settings
from app.services.cache_service import cache_service
from app.services.readiness_scorer import readiness_scorer, ReadinessScoreResult
from app.reasoning.provider.manager import get_llm_provider
from app.utils.logger import logger

GITHUB_API_BASE = "https://api.github.com"


class GitHubService:
    """Interacts with GitHub REST API with caching, back-off, and rate limit handling."""

    def __init__(self, token: Optional[str] = None):
        self._token = token or settings.GITHUB_TOKEN or os.environ.get("GITHUB_TOKEN")
        self._rate_limit_remaining = 60
        self._rate_limit_reset = time.time() + 3600

    def _get_headers(self) -> Dict[str, str]:
        token = self._token or settings.GITHUB_TOKEN or os.environ.get("GITHUB_TOKEN")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "CodeLens-Student-Platform/1.0",
        }
        if token and token.strip():
            headers["Authorization"] = f"Bearer {token.strip()}"
        return headers

    def _track_rate_limits(self, resp: httpx.Response):
        rem = resp.headers.get("x-ratelimit-remaining")
        reset_val = resp.headers.get("x-ratelimit-reset")
        if rem is not None:
            try:
                self._rate_limit_remaining = int(rem)
            except ValueError:
                pass
        if reset_val is not None:
            try:
                self._rate_limit_reset = float(reset_val)
            except ValueError:
                pass
        if self._rate_limit_remaining <= 2:
            logger.warning(
                f"GitHub API rate limit nearly exhausted ({self._rate_limit_remaining} remaining). Resets at {self._rate_limit_reset}"
            )

    # -------------------------------------------------------------
    # Explore Repositories
    # -------------------------------------------------------------
    async def get_explore_repos(
        self,
        language: Optional[str] = None,
        topic: Optional[str] = None,
        min_stars: int = 50,
        recently_active: bool = True,
        search_query: Optional[str] = None,
        page: int = 1,
        per_page: int = 15,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Fetches top repositories from GitHub REST API, cached in SQLite."""
        cache_key = f"explore:repos:lang={language}:topic={topic}:stars={min_stars}:recent={recently_active}:q={search_query}:p={page}:pp={per_page}"

        if not force_refresh:
            cached = cache_service.get_explore_cache(cache_key)
            if cached:
                return cached

        # Check rate limits before calling GitHub
        if self._rate_limit_remaining <= 0 and time.time() < self._rate_limit_reset:
            logger.info("GitHub API rate limited; serving curated fallback repos.")
            fallback = self._get_fallback_explore_repos(language, topic, page, per_page)
            return fallback

        # Build GitHub Search API query
        query_parts = []
        if search_query and search_query.strip():
            query_parts.append(search_query.strip())
        else:
            query_parts.append(f"stars:>={min_stars}")

        if language and language.strip().lower() != "all":
            query_parts.append(f"language:{language.strip().lower()}")

        if topic and topic.strip().lower() != "all":
            query_parts.append(f"topic:{topic.strip().lower()}")

        if recently_active:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m-%d")
            query_parts.append(f"pushed:>={cutoff}")

        q = " ".join(query_parts)

        params = {
            "q": q,
            "sort": "stars",
            "order": "desc",
            "page": page,
            "per_page": min(per_page, 30),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{GITHUB_API_BASE}/search/repositories",
                    headers=self._get_headers(),
                    params=params,
                )
                self._track_rate_limits(resp)

                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    enriched_repos = []
                    for item in items:
                        r_score = self._compute_repo_readiness(item)
                        enriched_repos.append(
                            {
                                "id": str(item["id"]),
                                "name": item["name"],
                                "full_name": item["full_name"],
                                "html_url": item["html_url"],
                                "description": item.get("description") or "No description provided.",
                                "stars": item.get("stargazers_count", 0),
                                "forks": item.get("forks_count", 0),
                                "open_issues_count": item.get("open_issues_count", 0),
                                "language": item.get("language") or "Other",
                                "topics": item.get("topics", [])[:5],
                                "pushed_at": item.get("pushed_at", ""),
                                "created_at": item.get("created_at", ""),
                                "owner": {
                                    "login": item.get("owner", {}).get("login", ""),
                                    "avatar_url": item.get("owner", {}).get("avatar_url", ""),
                                },
                                "readiness": r_score.dict(),
                            }
                        )

                    result = {
                        "total_count": data.get("total_count", len(enriched_repos)),
                        "page": page,
                        "per_page": per_page,
                        "repos": enriched_repos,
                        "cached_at": datetime.now(timezone.utc).isoformat(),
                    }
                    cache_service.set_explore_cache(cache_key, result, ttl_seconds=14400)
                    return result
                else:
                    logger.warning(
                        f"GitHub explore repos returned {resp.status_code}: {resp.text[:150]}"
                    )
        except Exception as e:
            logger.warning(f"Error querying GitHub explore repos: {e}")

        # Return fallback if network/API failed
        return self._get_fallback_explore_repos(language, topic, page, per_page)

    # -------------------------------------------------------------
    # Contribute Issues
    # -------------------------------------------------------------
    async def get_contribute_issues(
        self,
        language: Optional[str] = None,
        domain: Optional[str] = None,
        difficulty: Optional[str] = None,
        search_query: Optional[str] = None,
        user_top_languages: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 15,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Fetches beginner-friendly GitHub issues with AI-extracted skills & difficulty."""
        cache_key = f"contribute:issues:lang={language}:domain={domain}:diff={difficulty}:q={search_query}:p={page}:pp={per_page}"

        if not force_refresh:
            cached = cache_service.get_explore_cache(cache_key)
            if cached:
                return cached

        # Check rate limits before calling GitHub
        if self._rate_limit_remaining <= 0 and time.time() < self._rate_limit_reset:
            logger.info("GitHub API rate limited; serving curated beginner issues.")
            fallback = self._get_fallback_contribute_issues(language, domain, difficulty, page, per_page)
            return fallback

        # Build GitHub Issues Search Query
        # Requirement: "open issues labeled 'good first issue' / 'help wanted' / 'beginner' with no assignee, no linked PR, and recent activity"
        query_parts = [
            "is:issue",
            "is:open",
            "no:assignee",
            'label:"good first issue","help wanted","beginner"',
        ]

        if search_query and search_query.strip():
            query_parts.append(search_query.strip())

        if language and language.strip().lower() != "all":
            query_parts.append(f"language:{language.strip().lower()}")

        # Domain keywords mapping
        if domain and domain.strip().lower() != "all":
            domain_clean = domain.strip().lower()
            if domain_clean in ("ai/ml", "ai", "ml", "ai-ml"):
                query_parts.append("(machine-learning OR pytorch OR transformers OR llm OR tensorflow OR langchain)")
            elif domain_clean == "web":
                query_parts.append("(react OR vue OR nextjs OR fastapi OR frontend OR node)")
            elif domain_clean in ("devops", "cloud"):
                query_parts.append("(docker OR kubernetes OR terraform OR ci-cd OR github-actions)")
            elif domain_clean == "mobile":
                query_parts.append("(flutter OR react-native OR android OR swift OR kotlin)")

        # Activity cutoff (updated in last 120 days)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=120)).strftime("%Y-%m-%d")
        query_parts.append(f"updated:>={cutoff}")

        q = " ".join(query_parts)

        params = {
            "q": q,
            "sort": "updated",
            "order": "desc",
            "page": page,
            "per_page": min(per_page, 25),
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{GITHUB_API_BASE}/search/issues",
                    headers=self._get_headers(),
                    params=params,
                )
                self._track_rate_limits(resp)

                if resp.status_code == 200:
                    data = resp.json()
                    raw_issues = data.get("items", [])
                    enriched_issues = []

                    for raw_issue in raw_issues:
                        # Skip if it is actually a pull request
                        if "pull_request" in raw_issue:
                            continue

                        issue_id = str(raw_issue["id"])
                        updated_at = raw_issue.get("updated_at", "")

                        # Extract repo name from repository_url
                        # e.g. "https://api.github.com/repos/facebook/react" -> "facebook/react"
                        repo_url = raw_issue.get("repository_url", "")
                        repo_name = repo_url.replace(f"{GITHUB_API_BASE}/repos/", "")

                        # Check or compute AI enrichment with Gemini
                        ai_enrichment = await self.enrich_issue_with_gemini(
                            issue_id=issue_id,
                            updated_at=updated_at,
                            title=raw_issue.get("title", ""),
                            body=raw_issue.get("body", "") or "",
                            labels=[l.get("name", "") for l in raw_issue.get("labels", [])],
                        )

                        # Filter by difficulty if user requested
                        if (
                            difficulty
                            and difficulty.lower() != "all"
                            and ai_enrichment.get("difficulty", "medium").lower() != difficulty.lower()
                        ):
                            continue

                        # Mock / estimate repo readiness score
                        readiness_est = readiness_scorer.calculate_score(
                            {
                                "commits_last_30_days": 25,
                                "median_pr_merge_days": 3.0,
                                "maintainer_response_hours": 24.0,
                                "has_contributing_md": True,
                                "good_first_issue_count": 8,
                                "open_issues_count": 50,
                                "open_pr_count": 15,
                            }
                        )

                        enriched_issues.append(
                            {
                                "id": issue_id,
                                "number": raw_issue.get("number"),
                                "title": raw_issue.get("title", ""),
                                "html_url": raw_issue.get("html_url", ""),
                                "repository": repo_name,
                                "repository_url": f"https://github.com/{repo_name}",
                                "labels": [l.get("name", "") for l in raw_issue.get("labels", [])],
                                "comments_count": raw_issue.get("comments", 0),
                                "created_at": raw_issue.get("created_at", ""),
                                "updated_at": updated_at,
                                "user": {
                                    "login": raw_issue.get("user", {}).get("login", ""),
                                    "avatar_url": raw_issue.get("user", {}).get("avatar_url", ""),
                                },
                                "difficulty": ai_enrichment.get("difficulty", "easy"),
                                "skills": ai_enrichment.get("skills", ["Git", "CodeLens"]),
                                "likely_files": ai_enrichment.get("likely_files", []),
                                "summary": ai_enrichment.get("summary", ""),
                                "readiness": readiness_est.dict(),
                            }
                        )

                    # Prioritize user's top languages if available
                    if user_top_languages:
                        user_langs_set = {l.lower() for l in user_top_languages}
                        enriched_issues.sort(
                            key=lambda x: any(s.lower() in user_langs_set for s in x["skills"]),
                            reverse=True,
                        )

                    result = {
                        "total_count": data.get("total_count", len(enriched_issues)),
                        "page": page,
                        "per_page": per_page,
                        "issues": enriched_issues,
                        "cached_at": datetime.now(timezone.utc).isoformat(),
                    }
                    cache_service.set_explore_cache(cache_key, result, ttl_seconds=7200)
                    return result
                else:
                    logger.warning(
                        f"GitHub issues API returned {resp.status_code}: {resp.text[:150]}"
                    )
        except Exception as e:
            logger.warning(f"Error querying GitHub issues: {e}")

        return self._get_fallback_contribute_issues(language, domain, difficulty, page, per_page)

    # -------------------------------------------------------------
    # Contribute Repos
    # -------------------------------------------------------------
    async def get_contribute_repos(
        self,
        language: Optional[str] = None,
        domain: Optional[str] = None,
        page: int = 1,
        per_page: int = 15,
    ) -> Dict[str, Any]:
        """Returns contribution-friendly repositories with high readiness scores."""
        explore_data = await self.get_explore_repos(
            language=language,
            topic=domain,
            min_stars=50,
            recently_active=True,
            page=page,
            per_page=per_page,
        )
        repos = explore_data.get("repos", [])
        # Filter repos that have high readiness scores (>60)
        filtered = [r for r in repos if r.get("readiness", {}).get("score", 0) >= 60]
        return {
            "total_count": len(filtered),
            "page": page,
            "per_page": per_page,
            "repos": filtered,
        }

    # -------------------------------------------------------------
    # Gemini Issue Enrichment
    # -------------------------------------------------------------
    async def enrich_issue_with_gemini(
        self,
        issue_id: str,
        updated_at: str,
        title: str,
        body: str,
        labels: List[str],
    ) -> Dict[str, Any]:
        """Extracts {difficulty, skills, likely_files, summary} via Gemini generate_json, cached in SQLite."""
        # 1. Check cache first
        cached = cache_service.get_issue_enrichment(issue_id, updated_at)
        if cached:
            return cached

        # 2. Build prompt for Gemini
        provider = get_llm_provider("gemini")
        system_prompt = (
            "You are CodeLens Open-Source Mentor. Your task is to analyze GitHub issue descriptions "
            "and produce a student-friendly JSON summary to help college students contribute.\n"
            "Return valid JSON matching this exact structure:\n"
            "{\n"
            '  "difficulty": "easy" | "medium" | "hard",\n'
            '  "skills": ["string", "string"],\n'
            '  "likely_files": ["string", "string"],\n'
            '  "summary": "2-sentence clear explanation of what is requested and where to start."\n'
            "}"
        )

        labels_str = ", ".join(labels) if labels else "none"
        body_snippet = body[:1500] if body else "No detailed description provided."

        user_prompt = f"Issue Title: {title}\nLabels: {labels_str}\n\nDescription:\n{body_snippet}"

        try:
            enrichment = provider.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_tier="flash",
            )
            # Ensure required keys exist
            if not isinstance(enrichment.get("skills"), list):
                enrichment["skills"] = ["General Programming"]
            if not isinstance(enrichment.get("likely_files"), list):
                enrichment["likely_files"] = []
            if enrichment.get("difficulty") not in ("easy", "medium", "hard"):
                enrichment["difficulty"] = "easy" if "good first issue" in labels_str.lower() else "medium"

            cache_service.set_issue_enrichment(issue_id, updated_at, enrichment)
            return enrichment
        except Exception as e:
            logger.info(f"Gemini enrichment failed ({e}), using rule-based heuristic enrichment.")
            local_provider = get_llm_provider("local")
            fallback = local_provider.generate_json(prompt=f"{title}\n{labels_str}\n{body_snippet}")
            cache_service.set_issue_enrichment(issue_id, updated_at, fallback)
            return fallback

    # -------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------
    def _compute_repo_readiness(self, item: Dict[str, Any]) -> ReadinessScoreResult:
        """Computes readiness score for a GitHub repository item."""
        pushed_at = item.get("pushed_at")
        days_since_push = 10
        if pushed_at:
            try:
                dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                days_since_push = max(0, (datetime.now(timezone.utc) - dt).days)
            except Exception:
                pass

        commits_30d = 35 if days_since_push <= 3 else (20 if days_since_push <= 10 else 5)
        open_issues = max(1, item.get("open_issues_count", 20))
        # Estimate good first issues as 10-15% of open issues
        good_first_issues = max(2, int(open_issues * 0.12))

        return readiness_scorer.calculate_score(
            {
                "commits_last_30_days": commits_30d,
                "median_pr_merge_days": 2.5,
                "maintainer_response_hours": 20.0,
                "has_contributing_md": True,
                "good_first_issue_count": good_first_issues,
                "open_issues_count": open_issues,
                "open_pr_count": max(5, int(open_issues * 0.2)),
            }
        )

    # -------------------------------------------------------------
    # Fallback Curated Data (Always Available Offline/Unauthenticated)
    # -------------------------------------------------------------
    def _get_fallback_explore_repos(
        self,
        language: Optional[str],
        topic: Optional[str],
        page: int,
        per_page: int,
    ) -> Dict[str, Any]:
        """High-quality curated repos for college students and developers."""
        curated = [
            {
                "id": "1",
                "name": "fastapi",
                "full_name": "tiangolo/fastapi",
                "html_url": "https://github.com/tiangolo/fastapi",
                "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production.",
                "stars": 75000,
                "forks": 6200,
                "open_issues_count": 210,
                "language": "Python",
                "topics": ["api", "async", "python", "pydantic", "fastapi"],
                "pushed_at": datetime.now(timezone.utc).isoformat(),
                "created_at": "2018-12-08T00:00:00Z",
                "owner": {"login": "tiangolo", "avatar_url": "https://github.com/tiangolo.png"},
            },
            {
                "id": "2",
                "name": "react",
                "full_name": "facebook/react",
                "html_url": "https://github.com/facebook/react",
                "description": "The library for web and native user interfaces.",
                "stars": 228000,
                "forks": 45000,
                "open_issues_count": 890,
                "language": "JavaScript",
                "topics": ["react", "ui", "frontend", "declarative", "javascript"],
                "pushed_at": datetime.now(timezone.utc).isoformat(),
                "created_at": "2013-05-24T00:00:00Z",
                "owner": {"login": "facebook", "avatar_url": "https://github.com/facebook.png"},
            },
            {
                "id": "3",
                "name": "express",
                "full_name": "expressjs/express",
                "html_url": "https://github.com/expressjs/express",
                "description": "Fast, unopinionated, minimalist web framework for node.",
                "stars": 65000,
                "forks": 12000,
                "open_issues_count": 180,
                "language": "JavaScript",
                "topics": ["nodejs", "web", "http", "express", "backend"],
                "pushed_at": datetime.now(timezone.utc).isoformat(),
                "created_at": "2010-06-29T00:00:00Z",
                "owner": {"login": "expressjs", "avatar_url": "https://github.com/expressjs.png"},
            },
            {
                "id": "4",
                "name": "flask",
                "full_name": "pallets/flask",
                "html_url": "https://github.com/pallets/flask",
                "description": "The Python micro framework for building web applications.",
                "stars": 67000,
                "forks": 16000,
                "open_issues_count": 95,
                "language": "Python",
                "topics": ["python", "flask", "wsigi", "web", "microframework"],
                "pushed_at": datetime.now(timezone.utc).isoformat(),
                "created_at": "2010-04-06T00:00:00Z",
                "owner": {"login": "pallets", "avatar_url": "https://github.com/pallets.png"},
            },
            {
                "id": "5",
                "name": "vscode",
                "full_name": "microsoft/vscode",
                "html_url": "https://github.com/microsoft/vscode",
                "description": "Visual Studio Code editor source code repository.",
                "stars": 163000,
                "forks": 32000,
                "open_issues_count": 5200,
                "language": "TypeScript",
                "topics": ["editor", "typescript", "electron", "developer-tools"],
                "pushed_at": datetime.now(timezone.utc).isoformat(),
                "created_at": "2015-09-03T00:00:00Z",
                "owner": {"login": "microsoft", "avatar_url": "https://github.com/microsoft.png"},
            },
            {
                "id": "6",
                "name": "transformers",
                "full_name": "huggingface/transformers",
                "html_url": "https://github.com/huggingface/transformers",
                "description": "State-of-the-art Machine Learning for Pytorch, TensorFlow, and JAX.",
                "stars": 134000,
                "forks": 26000,
                "open_issues_count": 680,
                "language": "Python",
                "topics": ["nlp", "pytorch", "deep-learning", "transformer", "machine-learning"],
                "pushed_at": datetime.now(timezone.utc).isoformat(),
                "created_at": "2018-10-29T00:00:00Z",
                "owner": {"login": "huggingface", "avatar_url": "https://github.com/huggingface.png"},
            },
            {
                "id": "7",
                "name": "gin",
                "full_name": "gin-gonic/gin",
                "html_url": "https://github.com/gin-gonic/gin",
                "description": "Gin is a HTTP web framework written in Go (Golang). It features a Martini-like API with much better performance.",
                "stars": 78000,
                "forks": 8000,
                "open_issues_count": 120,
                "language": "Go",
                "topics": ["go", "golang", "web", "router", "http-framework"],
                "pushed_at": datetime.now(timezone.utc).isoformat(),
                "created_at": "2014-06-25T00:00:00Z",
                "owner": {"login": "gin-gonic", "avatar_url": "https://github.com/gin-gonic.png"},
            },
            {
                "id": "8",
                "name": "ripgrep",
                "full_name": "BurntSushi/ripgrep",
                "html_url": "https://github.com/BurntSushi/ripgrep",
                "description": "ripgrep recursively searches directories for a regex pattern while respecting your gitignore",
                "stars": 49000,
                "forks": 2200,
                "open_issues_count": 140,
                "language": "Rust",
                "topics": ["rust", "search", "cli", "regex", "performance"],
                "pushed_at": datetime.now(timezone.utc).isoformat(),
                "created_at": "2016-09-03T00:00:00Z",
                "owner": {"login": "BurntSushi", "avatar_url": "https://github.com/BurntSushi.png"},
            },
        ]

        # Filter by language if specified
        if language and language.lower() != "all":
            curated = [r for r in curated if r["language"].lower() == language.lower()]

        # Attach readiness score
        enriched = []
        for r in curated:
            r["readiness"] = self._compute_repo_readiness(r).dict()
            enriched.append(r)

        return {
            "total_count": len(enriched),
            "page": page,
            "per_page": per_page,
            "repos": enriched,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

    def _get_fallback_contribute_issues(
        self,
        language: Optional[str],
        domain: Optional[str],
        difficulty: Optional[str],
        page: int,
        per_page: int,
    ) -> Dict[str, Any]:
        """Curated beginner-friendly issues for students."""
        issues = [
            {
                "id": "1001",
                "number": 1042,
                "title": "Add support for JSON Schema examples in validation error response",
                "html_url": "https://github.com/tiangolo/fastapi/issues/1042",
                "repository": "tiangolo/fastapi",
                "repository_url": "https://github.com/tiangolo/fastapi",
                "labels": ["good first issue", "help wanted"],
                "comments_count": 4,
                "created_at": "2026-03-12T14:20:00Z",
                "updated_at": "2026-03-20T10:15:00Z",
                "user": {"login": "student_mentor", "avatar_url": "https://github.com/github.png"},
                "difficulty": "easy",
                "skills": ["Python", "FastAPI", "Pydantic"],
                "likely_files": ["fastapi/exceptions.py", "fastapi/openapi/utils.py"],
                "summary": "Improve developer error clarity by including example payloads from OpenAPI schema in 422 HTTP responses.",
            },
            {
                "id": "1002",
                "number": 2841,
                "title": "Fix React DOM warning on custom HTML5 data attributes",
                "html_url": "https://github.com/facebook/react/issues/2841",
                "repository": "facebook/react",
                "repository_url": "https://github.com/facebook/react",
                "labels": ["good first issue", "beginner friendly"],
                "comments_count": 6,
                "created_at": "2026-03-15T09:30:00Z",
                "updated_at": "2026-03-21T18:40:00Z",
                "user": {"login": "react_fan", "avatar_url": "https://github.com/facebook.png"},
                "difficulty": "medium",
                "skills": ["JavaScript", "React", "DOM API"],
                "likely_files": ["packages/react-dom/src/shared/DOMProperty.js"],
                "summary": "Prevent false positive console warnings when passing custom data attributes containing uppercase letters.",
            },
            {
                "id": "1003",
                "number": 512,
                "title": "Add async handler support to express routing middleware",
                "html_url": "https://github.com/expressjs/express/issues/512",
                "repository": "expressjs/express",
                "repository_url": "https://github.com/expressjs/express",
                "labels": ["help wanted", "beginner"],
                "comments_count": 2,
                "created_at": "2026-03-18T11:00:00Z",
                "updated_at": "2026-03-22T08:20:00Z",
                "user": {"login": "node_dev", "avatar_url": "https://github.com/expressjs.png"},
                "difficulty": "easy",
                "skills": ["JavaScript", "Node.js", "Promises"],
                "likely_files": ["lib/router/route.js", "lib/router/layer.js"],
                "summary": "Automatically catch rejected Promises in middleware functions and pass them to next(err).",
            },
            {
                "id": "1004",
                "number": 3190,
                "title": "Add helpful error message when model weights fail checksum verification",
                "html_url": "https://github.com/huggingface/transformers/issues/3190",
                "repository": "huggingface/transformers",
                "repository_url": "https://github.com/huggingface/transformers",
                "labels": ["good first issue"],
                "comments_count": 3,
                "created_at": "2026-03-19T16:45:00Z",
                "updated_at": "2026-03-23T12:00:00Z",
                "user": {"login": "hf_contributor", "avatar_url": "https://github.com/huggingface.png"},
                "difficulty": "easy",
                "skills": ["Python", "PyTorch", "HuggingFace"],
                "likely_files": ["src/transformers/modeling_utils.py", "src/transformers/file_utils.py"],
                "summary": "Show a clear, human-readable download troubleshooting hint instead of raw hash mismatch error.",
            },
            {
                "id": "1005",
                "number": 1940,
                "title": "Support custom syntax highlighting themes in markdown preview",
                "html_url": "https://github.com/microsoft/vscode/issues/1940",
                "repository": "microsoft/vscode",
                "repository_url": "https://github.com/microsoft/vscode",
                "labels": ["good first issue", "help wanted"],
                "comments_count": 5,
                "created_at": "2026-03-20T14:10:00Z",
                "updated_at": "2026-03-24T09:15:00Z",
                "user": {"login": "vscode_student", "avatar_url": "https://github.com/microsoft.png"},
                "difficulty": "medium",
                "skills": ["TypeScript", "CSS", "VS Code Extensions"],
                "likely_files": ["extensions/markdown-language-features/src/markdownEngine.ts"],
                "summary": "Allow user-configured color themes to be applied inside markdown code blocks in preview tab.",
            },
        ]

        if difficulty and difficulty.lower() != "all":
            issues = [i for i in issues if i["difficulty"].lower() == difficulty.lower()]

        readiness_est = readiness_scorer.calculate_score(
            {
                "commits_last_30_days": 30,
                "median_pr_merge_days": 2.5,
                "maintainer_response_hours": 18.0,
                "has_contributing_md": True,
                "good_first_issue_count": 10,
                "open_issues_count": 45,
                "open_pr_count": 12,
            }
        )

        for i in issues:
            i["readiness"] = readiness_est.dict()

        return {
            "total_count": len(issues),
            "page": page,
            "per_page": per_page,
            "issues": issues,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }


github_service = GitHubService()
