"""Unit tests for the Contribution-Readiness Scoring Engine."""

import pytest
from app.services.readiness_scorer import (
    WeightedReadinessScorer,
    ReadinessScoreResult,
    readiness_scorer,
)


def test_perfect_readiness_score():
    scorer = WeightedReadinessScorer()
    metrics = {
        "commits_last_30_days": 50,
        "median_pr_merge_days": 1.0,
        "maintainer_response_hours": 8.0,
        "has_contributing_md": True,
        "good_first_issue_count": 20,
        "open_issues_count": 50,
        "open_pr_count": 10,
    }
    result = scorer.calculate_score(metrics)
    assert isinstance(result, ReadinessScoreResult)
    assert result.score == 100
    assert result.grade == "A+"
    assert result.breakdown["recent_commit_activity"] == 20.0
    assert result.breakdown["pr_merge_time"] == 20.0
    assert result.breakdown["maintainer_response_time"] == 20.0
    assert result.breakdown["contributing_guidelines"] == 15.0
    assert result.breakdown["beginner_issue_ratio"] == 15.0
    assert result.breakdown["open_pr_backlog"] == 10.0


def test_low_readiness_score_for_dormant_repo():
    scorer = WeightedReadinessScorer()
    metrics = {
        "commits_last_30_days": 0,
        "median_pr_merge_days": 45.0,
        "maintainer_response_hours": 300.0,
        "has_contributing_md": False,
        "good_first_issue_count": 0,
        "open_issues_count": 500,
        "open_pr_count": 120,
    }
    result = scorer.calculate_score(metrics)
    assert result.score < 20
    assert result.grade == "D"
    assert result.breakdown["recent_commit_activity"] == 0.0
    assert result.breakdown["contributing_guidelines"] == 0.0
    assert result.breakdown["beginner_issue_ratio"] == 0.0


def test_grade_boundaries():
    scorer = WeightedReadinessScorer()
    # Grade A: 80-89
    m_a = {
        "commits_last_30_days": 25,       # 16
        "median_pr_merge_days": 3.0,       # 17
        "maintainer_response_hours": 24.0, # 16
        "has_contributing_md": True,       # 15
        "good_first_issue_count": 6,       # 12
        "open_issues_count": 60,
        "open_pr_count": 20,              # 8
    }
    res_a = scorer.calculate_score(m_a)
    assert res_a.grade in ["A", "A+"]
    assert 80 <= res_a.score <= 100


def test_weights_sum_to_100():
    scorer = WeightedReadinessScorer()
    total_weights = sum(scorer.WEIGHTS.values())
    assert total_weights == 100.0


def test_details_preservation():
    metrics = {
        "commits_last_30_days": 15,
        "median_pr_merge_days": 2.5,
        "maintainer_response_hours": 18.0,
        "has_contributing_md": True,
        "good_first_issue_count": 4,
        "open_issues_count": 30,
        "open_pr_count": 8,
    }
    res = readiness_scorer.calculate_score(metrics)
    assert res.details["commits_last_30_days"] == 15
    assert res.details["has_contributing_md"] is True
    assert 0 <= res.score <= 100
