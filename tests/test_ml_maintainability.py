"""Tests for Code Maintainability Risk model, training, and explainability."""

import pytest
import numpy as np
from app.models.code_chunk import CodeChunk, ChunkType
from app.ml.maintainability.feature_extractor import MaintainabilityFeatureExtractor
from app.ml.maintainability.risk_model import MaintainabilityRiskModel
from app.ml.maintainability.explainer import MaintainabilityExplainer


def test_maintainability_feature_extractor():
    extractor = MaintainabilityFeatureExtractor()
    chunk = CodeChunk(
        chunk_id="test_m1",
        repo_name="sample_repo",
        file_path="src/complex.py",
        language="python",
        chunk_type=ChunkType.FUNCTION,
        symbol_name="complex_fn",
        start_line=1,
        end_line=20,
        code="def complex_fn(a, b, c):\n    if a:\n        if b:\n            return True\n    return False",
    )

    feats = extractor.extract_features(chunk)
    assert feats["cyclomatic_complexity"] >= 3
    assert feats["nesting_depth"] >= 2
    assert feats["param_count"] == 3


def test_maintainability_model_train_and_predict():
    model = MaintainabilityRiskModel(model_type="hist_gbdt", n_estimators=10)
    X = np.random.randn(30, len(model.feature_names)).astype(np.float32)
    y = np.array([i % 3 for i in range(30)], dtype=np.int32)

    model.fit(X, y)
    assert model.is_trained is True

    chunk = CodeChunk(
        chunk_id="test_m2",
        repo_name="sample_repo",
        file_path="src/service.py",
        language="python",
        chunk_type=ChunkType.FUNCTION,
        symbol_name="service_call",
        start_line=1,
        end_line=5,
        code="def service_call(): return 42",
    )

    prediction = model.predict_chunk_risk(chunk)
    assert prediction["predicted_risk"] in ["LOW", "MEDIUM", "HIGH"]
    assert "probabilities" in prediction

    explainer = MaintainabilityExplainer(model)
    explanation = explainer.explain_chunk(chunk)
    assert len(explanation["measured_facts"]) > 0
    assert "recommendation" in explanation
