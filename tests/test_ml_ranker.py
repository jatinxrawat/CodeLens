"""Tests for Code Relevance Ranker model training, feature extraction, and explainability."""

import pytest
import numpy as np
from app.models.code_chunk import CodeChunk, ChunkType
from app.ml.ranking.feature_extractor import RankingFeatureExtractor
from app.ml.ranking.ranker_model import CodeRankerModel
from app.ml.ranking.explainer import RankingExplainer


def test_ranking_feature_extractor():
    extractor = RankingFeatureExtractor()
    chunk = CodeChunk(
        chunk_id="test_c1",
        repo_name="sample_repo",
        file_path="src/auth.py",
        language="python",
        chunk_type=ChunkType.FUNCTION,
        symbol_name="authenticate_user",
        start_line=1,
        end_line=10,
        code="def authenticate_user(username, password):\n    return True",
        docstring="Authenticates user credentials against the database.",
    )

    feats = extractor.extract_features("Where is authenticate_user located?", chunk)
    assert "dense_cosine_similarity" in feats
    assert feats["symbol_exact_match"] == 1.0
    assert feats["is_function"] == 1.0
    assert feats["has_docstring"] == 1.0

    vec = extractor.extract_feature_vector("Where is authenticate_user located?", chunk)
    assert len(vec) == len(extractor.FEATURE_NAMES)
    assert isinstance(vec, np.ndarray)


def test_ranker_model_train_and_predict():
    ranker = CodeRankerModel(model_type="hist_gbdt", n_estimators=10)
    
    # Create synthetic feature matrix
    X = np.random.randn(20, len(ranker.feature_names)).astype(np.float32)
    y = np.array([1 if i % 2 == 0 else 0 for i in range(20)], dtype=np.int32)

    ranker.fit(X, y)
    assert ranker.is_trained is True

    chunk = CodeChunk(
        chunk_id="test_c2",
        repo_name="sample_repo",
        file_path="src/login.py",
        language="python",
        chunk_type=ChunkType.FUNCTION,
        symbol_name="login_handler",
        start_line=1,
        end_line=5,
        code="def login_handler(): pass",
    )

    score = ranker.predict_score("login handler", chunk)
    assert 0.0 <= score <= 1.0

    explainer = RankingExplainer(ranker)
    explanation = explainer.explain_candidate("login handler", chunk, score)
    assert "factors" in explanation
    assert len(explanation["factors"]) > 0
