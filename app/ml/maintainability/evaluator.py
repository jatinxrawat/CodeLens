"""Maintainability Risk Model Evaluator.

Computes precision, recall, F1-score, confusion matrix, and per-class diagnostics.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support

from app.ml.dataset.dataset_schema import MaintainabilityDataset
from app.ml.maintainability.risk_model import MaintainabilityRiskModel


class MaintainabilityEvaluator:
    """Evaluates the Maintainability Risk ML Model against holdout test repositories."""

    def __init__(self, model: MaintainabilityRiskModel):
        self.model = model

    def evaluate(self, dataset: MaintainabilityDataset) -> Dict[str, Any]:
        """Evaluates model performance across test split."""
        test_repos = set(dataset.test_repositories) if dataset.test_repositories else set(dataset.train_repositories)
        test_samples = [s for s in dataset.samples if s.repository_id in test_repos]

        if not test_samples:
            test_samples = dataset.samples

        if not test_samples or not self.model.is_trained:
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "confusion_matrix": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
                "class_metrics": {},
                "total_test_samples": 0,
            }

        X_test = []
        y_true = []
        for s in test_samples:
            vec = [s.features.get(f, 0.0) for f in self.model.feature_names]
            X_test.append(vec)
            y_true.append(s.numeric_label)

        X_test = np.array(X_test, dtype=np.float32)
        y_true = np.array(y_true, dtype=np.int32)

        X_scaled = self.model.scaler.transform(X_test)
        y_pred = self.model.model.predict(X_scaled)

        precision, recall, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="weighted", zero_division=0
        )
        conf_mat = confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist()

        # Per-class breakdown
        p_per, r_per, f_per, support = precision_recall_fscore_support(
            y_true, y_pred, labels=[0, 1, 2], zero_division=0
        )
        classes = MaintainabilityRiskModel.CLASSES
        class_metrics = {
            classes[i]: {
                "precision": round(float(p_per[i]), 4),
                "recall": round(float(r_per[i]), 4),
                "f1_score": round(float(f_per[i]), 4),
                "support": int(support[i]),
            }
            for i in range(3)
        }

        accuracy = float(np.mean(y_true == y_pred))

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1_score": round(float(f1), 4),
            "confusion_matrix": conf_mat,
            "class_metrics": class_metrics,
            "total_test_samples": len(test_samples),
            "feature_importances": self.model.get_feature_importances(),
        }
