"""API tests for Phase 5 ML Studio and model endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_ml_dataset_stats():
    res = client.get("/api/ml/dataset/stats")
    assert res.status_code == 200
    data = res.json()
    assert "ranking_dataset" in data
    assert "maintainability_dataset" in data
    assert "repositories" in data


def test_api_ml_ranker_baselines():
    res = client.get("/api/ml/ranker/baselines")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_api_ml_ranker_ablation():
    res = client.get("/api/ml/ranker/ablation")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_api_ml_maintainability_metrics():
    res = client.get("/api/ml/maintainability/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "accuracy" in data
    assert "confusion_matrix" in data
    assert "feature_importances" in data


def test_api_ml_experiments_and_failures():
    res_exp = client.get("/api/ml/experiments")
    assert res_exp.status_code == 200
    assert isinstance(res_exp.json(), list)

    res_fail = client.get("/api/ml/failures")
    assert res_fail.status_code == 200
    data_fail = res_fail.json()
    assert "ranking_failures" in data_fail
    assert "maintainability_failures" in data_fail
