"""Tests for Phase 5 ML dataset generation and repository split leakage protection."""

import pytest
from app.ml.dataset.split_manager import SplitManager
from app.ml.dataset.dataset_schema import RankingSample, MaintainabilitySample
from app.ml.dataset.dataset_generator import RankingDatasetGenerator
from app.ml.dataset.maintainability_dataset import MaintainabilityDatasetGenerator


def test_split_manager_zero_leakage():
    sm = SplitManager(random_seed=42)
    repos = ["repo_alpha", "repo_beta", "repo_gamma", "repo_delta", "repo_epsilon"]
    train, val, test = sm.split_repositories(repos)

    assert len(train) > 0
    assert len(val) > 0
    assert len(test) > 0

    # Ensure mutually exclusive partition
    assert len(set(train).intersection(set(val))) == 0
    assert len(set(train).intersection(set(test))) == 0
    assert len(set(val).intersection(set(test))) == 0


def test_leakage_verifier_method():
    train_data = [{"repository_id": "repoA"}, {"repository_id": "repoB"}]
    test_data_clean = [{"repository_id": "repoC"}]
    test_data_leaked = [{"repository_id": "repoA"}]

    assert SplitManager.verify_no_leakage(train_data, test_data_clean) is True
    assert SplitManager.verify_no_leakage(train_data, test_data_leaked) is False


def test_maintainability_dataset_generator():
    mg = MaintainabilityDatasetGenerator(random_seed=42)
    dataset = mg.build_dataset(repository_ids=["sample_repo"])

    assert dataset.total_samples > 0
    assert len(dataset.samples) == dataset.total_samples
    assert "LOW" in dataset.statistics["class_distribution"]
    
    first = dataset.samples[0]
    assert "cyclomatic_complexity" in first.features
    assert "loc" in first.features
    assert first.risk_label in ["LOW", "MEDIUM", "HIGH"]
