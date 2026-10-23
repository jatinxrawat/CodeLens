"""Contribution-Readiness Scoring Engine for Open-Source Repositories.

Computes an explainable 0-100 score based on 6 weighted factors:
1. Recent commit activity (20%)
2. Median PR merge time (20%)
3. Maintainer response time on issues (20%)
4. Presence of CONTRIBUTING.md (15%)
5. Ratio of labeled beginner issues (15%)
6. Open-PR backlog (10%)

Structured with a clean interface so a trained ML model can replace or calibrate weights later.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ReadinessScoreResult(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Overall readiness score (0-100)")
    grade: str = Field(..., description="Letter grade (A+, A, B, C, D)")
    breakdown: Dict[str, float] = Field(..., description="Score awarded per factor")
    weights: Dict[str, float] = Field(..., description="Weight ceiling per factor")
    details: Dict[str, Any] = Field(..., description="Raw metric observations")


class BaseReadinessScorer:
    """Interface for repository readiness scoring."""

    def calculate_score(self, repo_metrics: Dict[str, Any]) -> ReadinessScoreResult:
        raise NotImplementedError


class WeightedReadinessScorer(BaseReadinessScorer):
    """Explainable weighted rule-based model for student contribution readiness."""

    WEIGHTS = {
        "recent_commit_activity": 20.0,
        "pr_merge_time": 20.0,
        "maintainer_response_time": 20.0,
        "contributing_guidelines": 15.0,
        "beginner_issue_ratio": 15.0,
        "open_pr_backlog": 10.0,
    }

    def calculate_score(self, repo_metrics: Dict[str, Any]) -> ReadinessScoreResult:
        commits_30d = int(repo_metrics.get("commits_last_30_days", 25))
        median_pr_merge_days = float(repo_metrics.get("median_pr_merge_days", 3.0))
        response_hours = float(repo_metrics.get("maintainer_response_hours", 24.0))
        has_contributing = bool(repo_metrics.get("has_contributing_md", True))
        good_first_issues = int(repo_metrics.get("good_first_issue_count", 8))
        open_issues = max(1, int(repo_metrics.get("open_issues_count", 40)))
        open_prs = int(repo_metrics.get("open_pr_count", 15))

        # 1. Recent commit activity (max 20 pts)
        if commits_30d >= 40:
            commit_pts = 20.0
        elif commits_30d >= 20:
            commit_pts = 16.0
        elif commits_30d >= 8:
            commit_pts = 12.0
        elif commits_30d >= 1:
            commit_pts = 6.0
        else:
            commit_pts = 0.0

        # 2. Median PR merge time (max 20 pts)
        if median_pr_merge_days <= 1.5:
            pr_pts = 20.0
        elif median_pr_merge_days <= 4.0:
            pr_pts = 17.0
        elif median_pr_merge_days <= 10.0:
            pr_pts = 12.0
        elif median_pr_merge_days <= 21.0:
            pr_pts = 6.0
        else:
            pr_pts = 2.0

        # 3. Maintainer response time on issues (max 20 pts)
        if response_hours <= 12.0:
            resp_pts = 20.0
        elif response_hours <= 36.0:
            resp_pts = 16.0
        elif response_hours <= 72.0:
            resp_pts = 11.0
        elif response_hours <= 168.0:  # 1 week
            resp_pts = 6.0
        else:
            resp_pts = 2.0

        # 4. Presence of CONTRIBUTING.md (max 15 pts)
        contrib_pts = 15.0 if has_contributing else 0.0

        # 5. Ratio of beginner issues (max 15 pts)
        beginner_ratio = good_first_issues / open_issues
        if beginner_ratio >= 0.12 or good_first_issues >= 15:
            beginner_pts = 15.0
        elif beginner_ratio >= 0.06 or good_first_issues >= 6:
            beginner_pts = 12.0
        elif beginner_ratio >= 0.02 or good_first_issues >= 2:
            beginner_pts = 8.0
        elif good_first_issues >= 1:
            beginner_pts = 4.0
        else:
            beginner_pts = 0.0

        # 6. Open-PR backlog (max 10 pts)
        if open_prs <= 25:
            backlog_pts = 10.0
        elif open_prs <= 75:
            backlog_pts = 8.0
        elif open_prs <= 180:
            backlog_pts = 5.0
        elif open_prs <= 400:
            backlog_pts = 2.0
        else:
            backlog_pts = 0.0

        total_score = int(round(commit_pts + pr_pts + resp_pts + contrib_pts + beginner_pts + backlog_pts))
        total_score = max(0, min(100, total_score))

        if total_score >= 85:
            grade = "A+"
        elif total_score >= 70:
            grade = "A"
        elif total_score >= 55:
            grade = "B"
        elif total_score >= 40:
            grade = "C"
        else:
            grade = "D"

        breakdown = {
            "recent_commit_activity": round(commit_pts, 1),
            "pr_merge_time": round(pr_pts, 1),
            "maintainer_response_time": round(resp_pts, 1),
            "contributing_guidelines": round(contrib_pts, 1),
            "beginner_issue_ratio": round(beginner_pts, 1),
            "open_pr_backlog": round(backlog_pts, 1),
        }

        details = {
            "commits_last_30_days": commits_30d,
            "median_pr_merge_days": median_pr_merge_days,
            "maintainer_response_hours": response_hours,
            "has_contributing_md": has_contributing,
            "good_first_issue_count": good_first_issues,
            "open_issues_count": open_issues,
            "beginner_issue_ratio": round(beginner_ratio, 3),
            "open_pr_count": open_prs,
        }

        return ReadinessScoreResult(
            score=total_score,
            grade=grade,
            breakdown=breakdown,
            weights=self.WEIGHTS,
            details=details,
        )


readiness_scorer = WeightedReadinessScorer()
