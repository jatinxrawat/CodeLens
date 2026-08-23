"""Maintainability Risk Model Trainer.

Trains the multi-class risk classifier with class-imbalance awareness.
"""

from typing import Dict, Any, Tuple
import numpy as np

from app.ml.dataset.dataset_schema import MaintainabilityDataset
from app.ml.maintainability.risk_model import MaintainabilityRiskModel
from app.ml.maintainability.evaluator import MaintainabilityEvaluator


class MaintainabilityTrainer:
    """Trainer for the Code Maintainability Risk Model."""

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

    def _prepare_data(
        self,
        dataset: MaintainabilityDataset,
        target_repositories: list = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Extracts X and y arrays from dataset samples."""
        allowed_repos = set(target_repositories) if target_repositories else None
        selected_samples = [
            s for s in dataset.samples
            if allowed_repos is None or s.repository_id in allowed_repos
        ]

        if not selected_samples:
            selected_samples = dataset.samples

        feature_names = MaintainabilityRiskModel().feature_names
        X = []
        y = []

        for s in selected_samples:
            vec = [s.features.get(f, 0.0) for f in feature_names]
            X.append(vec)
            y.append(s.numeric_label)

        return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)

    def train(
        self,
        dataset: MaintainabilityDataset,
    ) -> Tuple[MaintainabilityRiskModel, Dict[str, Any]]:
        """Trains the maintainability model on train split and evaluates on val/test split."""
        train_repos = dataset.train_repositories if dataset.train_repositories else None
        X_train, y_train = self._prepare_data(dataset, train_repos)

        model = MaintainabilityRiskModel(
            model_type=self.model_type,
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            random_seed=self.random_seed,
        )
        model.fit(X_train, y_train)

        evaluator = MaintainabilityEvaluator(model)
        eval_metrics = evaluator.evaluate(dataset)

        return model, eval_metrics
