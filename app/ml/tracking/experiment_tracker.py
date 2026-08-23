"""ML Experiment Tracker.

Records experiment metadata, hyperparameters, datasets, repository splits, and evaluation metrics.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone
import json
import uuid

from app.config import settings


class ExperimentTracker:
    """Tracks and persists ML experiment runs to disk in JSON format."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or (settings.BASE_DIR / "data" / "experiments")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.storage_dir / "experiments_log.json"

    def _load_all_records(self) -> List[Dict[str, Any]]:
        if self.log_file.exists():
            try:
                return json.loads(self.log_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_all_records(self, records: List[Dict[str, Any]]) -> None:
        self.log_file.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def log_experiment(
        self,
        model_name: str,
        model_version: str,
        hyperparameters: Dict[str, Any],
        dataset_info: Dict[str, Any],
        metrics: Dict[str, Any],
        git_commit: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Logs a new experiment run."""
        exp_id = f"exp_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        record = {
            "experiment_id": exp_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_name": model_name,
            "model_version": model_version,
            "hyperparameters": hyperparameters,
            "dataset_info": dataset_info,
            "metrics": metrics,
            "git_commit": git_commit or "local_dev",
            "notes": notes or "",
        }

        records = self._load_all_records()
        records.insert(0, record)
        self._save_all_records(records)
        return record

    def list_experiments(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all logged experiment records."""
        records = self._load_all_records()
        if model_name:
            records = [r for r in records if r.get("model_name") == model_name]
        return records


experiment_tracker = ExperimentTracker()
