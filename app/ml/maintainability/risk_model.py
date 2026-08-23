"""Code Maintainability Risk Model.

Multi-class classifier predicting maintainability risk levels (LOW, MEDIUM, HIGH)
from extracted static code complexity metrics.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import pickle
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from app.models.code_chunk import CodeChunk
from app.ml.maintainability.feature_extractor import MaintainabilityFeatureExtractor


class MaintainabilityRiskModel:
    """Trainable model for predicting software maintainability risk."""

    CLASSES = ["LOW", "MEDIUM", "HIGH"]

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
        self.feature_extractor = MaintainabilityFeatureExtractor()
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
        else:
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_seed,
            )

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MaintainabilityRiskModel":
        """Trains the multi-class risk classifier."""
        if len(X) == 0:
            raise ValueError("Training dataset X is empty.")

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        return self

    def predict_chunk_risk(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Predicts maintainability risk level and class probabilities for a single code chunk."""
        feats = self.feature_extractor.extract_features(chunk)
        vec = np.array([feats[name] for name in self.feature_names], dtype=np.float32)

        if not self.is_trained:
            # Heuristic fallback based on CC
            cc = feats["cyclomatic_complexity"]
            label = "HIGH" if cc >= 10 else "MEDIUM" if cc >= 5 else "LOW"
            probs = {"LOW": 0.8 if label == "LOW" else 0.1, "MEDIUM": 0.8 if label == "MEDIUM" else 0.1, "HIGH": 0.8 if label == "HIGH" else 0.1}
            return {
                "predicted_risk": label,
                "probabilities": probs,
                "confidence": max(probs.values()),
                "measured_features": feats,
            }

        vec_scaled = self.scaler.transform(vec.reshape(1, -1))
        pred_idx = int(self.model.predict(vec_scaled)[0])
        pred_label = self.CLASSES[pred_idx]
        raw_probs = self.model.predict_proba(vec_scaled)[0]

        probs_dict = {
            cls_name: round(float(raw_probs[i]), 4)
            for i, cls_name in enumerate(self.CLASSES)
            if i < len(raw_probs)
        }

        return {
            "predicted_risk": pred_label,
            "probabilities": probs_dict,
            "confidence": round(float(max(raw_probs)), 4),
            "measured_features": feats,
        }

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns relative feature importance dictionary."""
        if not self.is_trained:
            return {name: 1.0 / len(self.feature_names) for name in self.feature_names}

        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
        else:
            importances = np.ones(len(self.feature_names)) / len(self.feature_names)

        return {name: round(float(imp), 4) for name, imp in zip(self.feature_names, importances)}

    def save(self, file_path: Path) -> None:
        """Serializes model to disk."""
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
    def load(cls, file_path: Path) -> "MaintainabilityRiskModel":
        """Loads serialized model artifact."""
        with open(file_path, "rb") as f:
            data = pickle.load(f)

        model = cls(model_type=data["model_type"])
        model.model = data["model"]
        model.scaler = data["scaler"]
        model.feature_names = data["feature_names"]
        model.is_trained = data["is_trained"]
        return model
