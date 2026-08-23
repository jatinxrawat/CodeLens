"""Versioned ML Model Registry.

Manages saving, loading, versioning, and activation of trained model artifacts.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime, timezone

from app.config import settings
from app.ml.ranking.ranker_model import CodeRankerModel
from app.ml.maintainability.risk_model import MaintainabilityRiskModel


class ModelRegistry:
    """Manages versioned model artifacts stored on disk."""

    def __init__(self, base_models_dir: Optional[Path] = None):
        self.base_dir = base_models_dir or (settings.BASE_DIR / "models")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.active_ranker: Optional[CodeRankerModel] = None
        self.active_maintainability: Optional[MaintainabilityRiskModel] = None
        self._load_active_models()

    def _get_model_dir(self, model_type: str, version: str) -> Path:
        p = self.base_dir / model_type / version
        p.mkdir(parents=True, exist_ok=True)
        return p

    def register_ranker_model(
        self,
        model: CodeRankerModel,
        version: str = "v1",
        metrics: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Saves ranker model artifact and metadata."""
        model_dir = self._get_model_dir("retrieval_ranker", version)
        artifact_path = model_dir / "ranker.pkl"
        model.save(artifact_path)

        meta = {
            "model_type": "retrieval_ranker",
            "version": version,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics or {},
            "config": config or {},
            "feature_names": model.feature_names,
        }
        (model_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        self.active_ranker = model
        return artifact_path

    def register_maintainability_model(
        self,
        model: MaintainabilityRiskModel,
        version: str = "v1",
        metrics: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Saves maintainability model artifact and metadata."""
        model_dir = self._get_model_dir("maintainability", version)
        artifact_path = model_dir / "maintainability.pkl"
        model.save(artifact_path)

        meta = {
            "model_type": "maintainability",
            "version": version,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics or {},
            "config": config or {},
            "feature_names": model.feature_names,
        }
        (model_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        self.active_maintainability = model
        return artifact_path

    def _load_active_models(self) -> None:
        """Auto-loads latest active model versions if present."""
        # 1. Load Ranker
        ranker_v1 = self.base_dir / "retrieval_ranker" / "v1" / "ranker.pkl"
        if ranker_v1.exists():
            try:
                self.active_ranker = CodeRankerModel.load(ranker_v1)
            except Exception:
                pass

        # 2. Load Maintainability
        maint_v1 = self.base_dir / "maintainability" / "v1" / "maintainability.pkl"
        if maint_v1.exists():
            try:
                self.active_maintainability = MaintainabilityRiskModel.load(maint_v1)
            except Exception:
                pass

    def get_active_ranker(self) -> Optional[CodeRankerModel]:
        return self.active_ranker

    def get_active_maintainability(self) -> Optional[MaintainabilityRiskModel]:
        return self.active_maintainability


model_registry = ModelRegistry()
