"""Code Relevance Ranking Model.

Trainable GBDT/Tree-based learning-to-rank model predicting code relevance scores.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from app.models.code_chunk import CodeChunk
from app.ml.ranking.feature_extractor import RankingFeatureExtractor


class CodeRankerModel:
    """Trainable code relevance re-ranking model."""

    def __init__(
        self,
        model_type: str = "hist_gbdt",
        n_estimators: int = 100,
        learning_rate: float = 0.05,
        max_depth: int = 4,
        random_seed: int = 42,
    ):
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_seed = random_seed
        self.feature_extractor = RankingFeatureExtractor()
        self.feature_names = self.feature_extractor.FEATURE_NAMES
        self.scaler = StandardScaler()
        self.is_trained = False

        if model_type == "hist_gbdt":
            self.model = HistGradientBoostingClassifier(
                max_iter=n_estimators,
                learning_rate=learning_rate,
                max_depth=max_depth,
                random_state=random_seed,
            )
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingClassifier(
                n_estimators=n_estimators,
                learning_rate=learning_rate,
                max_depth=max_depth,
                random_state=random_seed,
            )
        else:
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_seed,
            )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "CodeRankerModel":
        """Trains the ranking classifier on feature matrix X and binary/graded target y."""
        if len(X) == 0:
            raise ValueError("Training dataset X is empty.")

        # Binarize labels if multi-class graded: label >= 1 is relevant
        y_binary = (y >= 1).astype(int)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y_binary)
        self.is_trained = True
        return self

    def predict_score(self, query: str, chunk: CodeChunk) -> float:
        """Predicts a continuous relevance score in [0.0, 1.0] for a single candidate."""
        if not self.is_trained:
            # Fallback to pure semantic cosine similarity if model not trained
            feats = self.feature_extractor.extract_features(query, chunk)
            return (feats["dense_cosine_similarity"] + 1.0) / 2.0

        vec = self.feature_extractor.extract_feature_vector(query, chunk)
        vec_scaled = self.scaler.transform(vec.reshape(1, -1))
        # Probability of class 1 (Relevant)
        probs = self.model.predict_proba(vec_scaled)[0]
        return float(probs[1])

    def rank_candidates(
        self,
        query: str,
        candidate_chunks: List[CodeChunk],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Reranks candidate code chunks using the trained ML model."""
        if not candidate_chunks:
            return []

        # Extract features for all candidates
        query_emb = self.feature_extractor.embedding_model.encode_single(query)
        scored_candidates = []

        for chunk in candidate_chunks:
            chunk_emb = self.feature_extractor.embedding_model.encode_single(chunk.get_embeddable_text())
            feats = self.feature_extractor.extract_features(
                query, chunk, query_embedding=query_emb, chunk_embedding=chunk_emb
            )
            vec = np.array([feats[name] for name in self.feature_names], dtype=np.float32)

            if self.is_trained:
                vec_scaled = self.scaler.transform(vec.reshape(1, -1))
                probs = self.model.predict_proba(vec_scaled)[0]
                relevance_score = float(probs[1])
            else:
                relevance_score = (feats["dense_cosine_similarity"] + 1.0) / 2.0

            scored_candidates.append({
                "chunk": chunk,
                "relevance_score": relevance_score,
                "features": feats,
            })

        # Sort descending by predicted relevance score
        scored_candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_candidates[:top_k]

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns feature importance dictionary."""
        if not self.is_trained:
            return {name: 1.0 / len(self.feature_names) for name in self.feature_names}

        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
        else:
            # For HistGradientBoosting, fallback to uniform or permutation importances
            importances = np.ones(len(self.feature_names)) / len(self.feature_names)

        return {name: round(float(imp), 4) for name, imp in zip(self.feature_names, importances)}

    def save(self, file_path: Path) -> None:
        """Serializes model artifact to disk."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "scaler": self.scaler,
                "model_type": self.model_type,
                "feature_names": self.feature_names,
                "is_trained": self.is_trained,
            }, f)

    @classmethod
    def load(cls, file_path: Path) -> "CodeRankerModel":
        """Loads serialized model artifact from disk."""
        with open(file_path, "rb") as f:
            data = pickle.load(f)

        ranker = cls(model_type=data["model_type"])
        ranker.model = data["model"]
        ranker.scaler = data["scaler"]
        ranker.feature_names = data["feature_names"]
        ranker.is_trained = data["is_trained"]
        return ranker
