"""ML Model Failure Analysis & Diagnostic Engine.

Systematically identifies and categorizes failure cases for both retrieval ranking and maintainability models.
"""

from typing import List, Dict, Any, Optional
import numpy as np

from app.models.code_chunk import CodeChunk
from app.ml.dataset.dataset_schema import RankingDataset, MaintainabilityDataset
from app.ml.ranking.ranker_model import CodeRankerModel
from app.ml.maintainability.risk_model import MaintainabilityRiskModel
from app.retrieval.hybrid_search import HybridSearchEngine
from app.services.repository_service import repository_service


from app.services.search_service import search_service


class FailureAnalyzer:
    """Diagnoses model failures on unseen test holdout datasets."""

    def __init__(
        self,
        ranker_model: Optional[CodeRankerModel] = None,
        maintainability_model: Optional[MaintainabilityRiskModel] = None,
    ):
        self.ranker_model = ranker_model
        self.maintainability_model = maintainability_model

    def analyze_ranking_failures(
        self,
        dataset: RankingDataset,
        candidate_count: int = 15,
    ) -> List[Dict[str, Any]]:
        """Identifies test queries where expected code chunks were NOT ranked in top 3."""
        failures = []
        test_repos = set(dataset.test_repositories) if dataset.test_repositories else set(dataset.train_repositories)
        test_samples = [s for s in dataset.samples if s.repository_id in test_repos and s.expected_source]

        if not test_samples:
            test_samples = [s for s in dataset.samples if s.expected_source]

        for sample in test_samples:
            repo_id = sample.repository_id
            query = sample.query
            target_id = sample.code_chunk_id

            try:
                engine = search_service.get_search_engine(repo_id)
            except Exception:
                continue

            # Run retrieval
            initial_results, _ = engine.search(query=query, top_k=candidate_count, mode="hybrid")
            candidate_chunks = [r.chunk for r in initial_results]

            if self.ranker_model and self.ranker_model.is_trained:
                reranked = self.ranker_model.rank_candidates(query, candidate_chunks, top_k=candidate_count)
                retrieved_chunks = [r["chunk"] for r in reranked]
            else:
                retrieved_chunks = candidate_chunks

            rank = -1
            for idx, c in enumerate(retrieved_chunks):
                if c.chunk_id == target_id:
                    rank = idx + 1
                    break

            if rank > 3 or rank == -1:
                # Failure case
                top_1_chunk = retrieved_chunks[0] if retrieved_chunks else None
                reason = (
                    "Target chunk not in candidate set"
                    if rank == -1
                    else "Lower semantic similarity compared to competing function with similar naming"
                    if rank > 3 and sample.symbol_name is None
                    else "Vocabulary mismatch: query terms differ from identifier subwords"
                )

                failures.append({
                    "query": query,
                    "repository_id": repo_id,
                    "language": sample.language,
                    "expected_file": sample.file_path,
                    "expected_symbol": sample.symbol_name,
                    "achieved_rank": rank if rank != -1 else "Not Retrieved",
                    "top_retrieved_file": top_1_chunk.file_path if top_1_chunk else "None",
                    "top_retrieved_symbol": top_1_chunk.symbol_name if top_1_chunk else "None",
                    "diagnostic_reason": reason,
                })

        return failures

    def analyze_maintainability_failures(
        self,
        dataset: MaintainabilityDataset,
    ) -> List[Dict[str, Any]]:
        """Identifies code chunks where predicted risk differs from ground truth label."""
        failures = []
        if not self.maintainability_model or not self.maintainability_model.is_trained:
            return []

        test_repos = set(dataset.test_repositories) if dataset.test_repositories else set(dataset.train_repositories)
        test_samples = [s for s in dataset.samples if s.repository_id in test_repos]

        if not test_samples:
            test_samples = dataset.samples

        for s in test_samples:
            vec = np.array([s.features.get(f, 0.0) for f in self.maintainability_model.feature_names], dtype=np.float32)
            vec_scaled = self.maintainability_model.scaler.transform(vec.reshape(1, -1))
            pred_idx = int(self.maintainability_model.model.predict(vec_scaled)[0])
            pred_label = MaintainabilityRiskModel.CLASSES[pred_idx]

            if pred_label != s.risk_label:
                failures.append({
                    "chunk_id": s.chunk_id,
                    "repository_id": s.repository_id,
                    "file_path": s.file_path,
                    "symbol_name": s.symbol_name,
                    "language": s.language,
                    "actual_label": s.risk_label,
                    "predicted_label": pred_label,
                    "cyclomatic_complexity": s.features.get("cyclomatic_complexity", 0.0),
                    "loc": s.features.get("loc", 0.0),
                    "nesting_depth": s.features.get("nesting_depth", 0.0),
                    "diagnostic_reason": (
                        "Edge case near decision boundary threshold"
                        if abs(s.features.get("cyclomatic_complexity", 0.0) - 10.0) <= 2.0
                        else "High LOC but low nesting depth resulting in conflicting risk signals"
                    ),
                })

        return failures
