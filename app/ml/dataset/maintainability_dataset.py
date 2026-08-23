"""Maintainability Risk Dataset Generator.

Extracts multidimensional code quality features (McCabe CC, LOC, nesting, parameters,
fan-in/fan-out, branching, comment ratio) and assigns structured ground-truth labels.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from app.config import settings
from app.models.code_chunk import CodeChunk
from app.ml.dataset.dataset_schema import MaintainabilitySample, MaintainabilityDataset
from app.ml.dataset.split_manager import SplitManager
from app.analysis.quality_metrics import QualityMetricsCalculator
from app.services.repository_service import repository_service


class MaintainabilityDatasetGenerator:
    """Extracts features and builds datasets for the Maintainability Risk ML Model."""

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        self.split_manager = SplitManager(random_seed=random_seed)
        self.quality_calc = QualityMetricsCalculator()

    def extract_chunk_features(self, chunk: CodeChunk) -> Dict[str, float]:
        """Extracts numerical complexity and structural features from a single code chunk."""
        code = chunk.code
        lines = code.splitlines()
        loc = len([l for l in lines if l.strip()])
        raw_loc = len(lines)

        # 1. Cyclomatic Complexity
        cc = self.quality_calc.calculate_cyclomatic_complexity(code)

        # 2. Maximum Nesting Depth
        nesting = self.quality_calc.calculate_nesting_depth(code)

        # 3. Parameters count
        param_count = 0
        if "(" in code and ")" in code:
            signature = code.split("{")[0].split(":")[0]
            if "(" in signature and ")" in signature:
                param_str = signature[signature.find("(") + 1 : signature.rfind(")")]
                param_count = len([p for p in param_str.split(",") if p.strip()])

        # 4. Branches & Loops
        branch_count = float(code.count("if ") + code.count("elif ") + code.count("else:") + code.count("case ") + code.count("switch"))
        loop_count = float(code.count("for ") + code.count("while ") + code.count("do {"))

        # 5. Comment ratio
        comment_lines = len([l for l in lines if l.strip().startswith(("#", "//", "/*", "*", '"""', "'''"))])
        comment_ratio = float(comment_lines) / float(max(1, raw_loc))

        # 6. Return statements count
        return_count = float(code.count("return ") + code.count("yield "))

        # 7. Try/Catch blocks
        error_blocks = float(code.count("try:") + code.count("try {") + code.count("catch") + code.count("except"))

        return {
            "loc": float(loc),
            "cyclomatic_complexity": float(cc),
            "nesting_depth": float(nesting),
            "param_count": float(min(15, param_count)),
            "branch_count": branch_count,
            "loop_count": loop_count,
            "comment_ratio": round(comment_ratio, 3),
            "return_count": return_count,
            "error_blocks": error_blocks,
            "has_docstring": 1.0 if chunk.docstring else 0.0,
            "avg_line_length": float(sum(len(l) for l in lines) / max(1, len(lines))),
        }

    def _determine_ground_truth_label(self, features: Dict[str, float]) -> str:
        """Assigns ground-truth maintainability risk label based on empirical thresholds.

        HIGH Risk: CC > 10 OR (LOC > 80 AND Nesting >= 4) OR (CC > 7 AND Param Count >= 5)
        MEDIUM Risk: CC between 5 and 10 OR LOC between 40 and 80 OR Nesting == 3
        LOW Risk: CC <= 4, LOC < 40, Nesting <= 2
        """
        cc = features["cyclomatic_complexity"]
        loc = features["loc"]
        nesting = features["nesting_depth"]
        params = features["param_count"]

        if cc >= 10.0 or (loc >= 80.0 and nesting >= 4.0) or (cc >= 7.0 and params >= 5.0):
            return "HIGH"
        elif cc >= 5.0 or loc >= 40.0 or nesting >= 3.0:
            return "MEDIUM"
        else:
            return "LOW"

    def build_dataset(
        self,
        repository_ids: Optional[List[str]] = None,
    ) -> MaintainabilityDataset:
        """Constructs a maintainability dataset from all indexed repository chunks."""
        if not repository_ids:
            repo_summaries = repository_service.list_repositories()
            repository_ids = [r.repository_id for r in repo_summaries]

        if not repository_ids:
            repository_ids = ["sample_repo"]

        train_repos, val_repos, test_repos = self.split_manager.split_repositories(repository_ids)

        samples: List[MaintainabilitySample] = []
        label_map = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

        for repo_id in repository_ids:
            raw_chunks = repository_service.get_chunks_for_repository(repo_id)
            if not raw_chunks:
                continue

            chunks = [CodeChunk.from_dict(c) for c in raw_chunks]
            for chunk in chunks:
                if len(chunk.code.splitlines()) < 2:
                    continue

                features = self.extract_chunk_features(chunk)
                risk_label = self._determine_ground_truth_label(features)

                samples.append(
                    MaintainabilitySample(
                        chunk_id=chunk.chunk_id,
                        repository_id=repo_id,
                        file_path=chunk.file_path,
                        symbol_name=chunk.symbol_name,
                        language=chunk.language,
                        features=features,
                        risk_label=risk_label,
                        numeric_label=label_map[risk_label],
                    )
                )

        class_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        for s in samples:
            class_dist[s.risk_label] += 1

        stats = {
            "total_repositories": len(repository_ids),
            "total_samples": len(samples),
            "class_distribution": class_dist,
            "train_repo_count": len(train_repos),
            "val_repo_count": len(val_repos),
            "test_repo_count": len(test_repos),
        }

        return MaintainabilityDataset(
            version="1.0.0",
            created_at=datetime.now(timezone.utc).isoformat(),
            total_samples=len(samples),
            train_repositories=train_repos,
            val_repositories=val_repos,
            test_repositories=test_repos,
            samples=samples,
            statistics=stats,
        )

    def save_dataset(self, dataset: MaintainabilityDataset, output_path: Optional[Path] = None) -> Path:
        """Saves maintainability dataset to disk."""
        if not output_path:
            output_dir = settings.BASE_DIR / "data" / "datasets"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "maintainability_dataset.json"

        output_path.write_text(dataset.model_dump_json(indent=2), encoding="utf-8")
        return output_path
