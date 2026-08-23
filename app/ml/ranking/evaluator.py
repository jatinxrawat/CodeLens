"""Code Ranking Evaluation Engine.

Computes exact empirical metrics: Recall@K (1, 3, 5, 10), MRR, NDCG@K (5, 10), and search latency.
"""

from typing import List, Dict, Any, Optional
import time
import numpy as np

from app.models.code_chunk import CodeChunk
from app.services.search_service import search_service
from app.ml.ranking.ranker_model import CodeRankerModel
from app.ml.dataset.dataset_schema import RankingDataset


class RankingEvaluator:
    """Evaluates IR and ML re-ranking models against empirical benchmarks."""

    def __init__(
        self,
        ranker_model: Optional[CodeRankerModel] = None,
    ):
        self.ranker_model = ranker_model

    @staticmethod
    def _compute_dcg(relevances: List[int], k: int) -> float:
        """Computes Discounted Cumulative Gain at position K."""
        relevances = relevances[:k]
        if not relevances:
            return 0.0
        return sum((2**rel - 1) / np.log2(idx + 2) for idx, rel in enumerate(relevances))

    @staticmethod
    def _compute_ndcg(retrieved_relevances: List[int], ideal_relevances: List[int], k: int) -> float:
        """Computes Normalized Discounted Cumulative Gain at position K."""
        dcg = RankingEvaluator._compute_dcg(retrieved_relevances, k)
        idcg = RankingEvaluator._compute_dcg(sorted(ideal_relevances, reverse=True), k)
        if idcg == 0.0:
            return 0.0
        return float(dcg / idcg)

    def evaluate_retrieval_method(
        self,
        dataset: RankingDataset,
        method: str = "hybrid",  # "bm25", "vector", "hybrid", "hybrid_ml_ranker"
        alpha: float = 0.60,
        candidate_count: int = 20,
    ) -> Dict[str, Any]:
        """Runs empirical evaluation over the test dataset split."""
        # Filter samples to only test repositories
        test_repos = set(dataset.test_repositories) if dataset.test_repositories else set(dataset.train_repositories)
        test_samples = [s for s in dataset.samples if s.repository_id in test_repos and s.expected_source]

        if not test_samples:
            # Fallback to all positive samples
            test_samples = [s for s in dataset.samples if s.expected_source]

        if not test_samples:
            return {
                "method": method,
                "total_queries": 0,
                "recall_at_1": 0.0,
                "recall_at_3": 0.0,
                "recall_at_5": 0.0,
                "recall_at_10": 0.0,
                "mrr": 0.0,
                "ndcg_at_5": 0.0,
                "ndcg_at_10": 0.0,
                "avg_latency_ms": 0.0,
            }

        recalls = {1: 0, 3: 0, 5: 0, 10: 0}
        reciprocal_ranks = []
        ndcg_5_list = []
        ndcg_10_list = []
        latencies = []

        for sample in test_samples:
            repo_id = sample.repository_id
            query = sample.query
            target_chunk_id = sample.code_chunk_id

            try:
                engine = search_service.get_search_engine(repo_id)
            except Exception:
                continue

            t0 = time.perf_counter()
            if method == "bm25":
                results, lat = engine.search(query=query, top_k=candidate_count, mode="keyword")
            elif method == "vector":
                results, lat = engine.search(query=query, top_k=candidate_count, mode="vector")
            elif method == "hybrid":
                results, lat = engine.search(query=query, top_k=candidate_count, mode="hybrid", alpha=alpha)
            elif method == "hybrid_ml_ranker":
                initial_results, lat = engine.search(query=query, top_k=candidate_count, mode="hybrid", alpha=alpha)
                candidate_chunks = [r.chunk for r in initial_results]
                if self.ranker_model and self.ranker_model.is_trained:
                    reranked = self.ranker_model.rank_candidates(query, candidate_chunks, top_k=candidate_count)
                    results = reranked
                else:
                    results = initial_results
            else:
                results, lat = engine.search(query=query, top_k=candidate_count, mode="hybrid")

            latency_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(latency_ms)

            # Find matching rank
            retrieved_chunk_ids = []
            for r in results:
                c = r["chunk"] if isinstance(r, dict) else r.chunk
                retrieved_chunk_ids.append(c.chunk_id)

            rank = -1
            for idx, cid in enumerate(retrieved_chunk_ids):
                if cid == target_chunk_id:
                    rank = idx + 1
                    break

            # Update recall
            for k in recalls:
                if 0 < rank <= k:
                    recalls[k] += 1

            # Update MRR
            if rank > 0:
                reciprocal_ranks.append(1.0 / rank)
            else:
                reciprocal_ranks.append(0.0)

            # Compute NDCG
            relevances = [3 if cid == target_chunk_id else 0 for cid in retrieved_chunk_ids]
            ideal = [3]
            ndcg_5_list.append(self._compute_ndcg(relevances, ideal, 5))
            ndcg_10_list.append(self._compute_ndcg(relevances, ideal, 10))

        n_total = len(test_samples)
        return {
            "method": method,
            "total_queries": n_total,
            "recall_at_1": round(recalls[1] / n_total, 4),
            "recall_at_3": round(recalls[3] / n_total, 4),
            "recall_at_5": round(recalls[5] / n_total, 4),
            "recall_at_10": round(recalls[10] / n_total, 4),
            "mrr": round(float(np.mean(reciprocal_ranks)), 4),
            "ndcg_at_5": round(float(np.mean(ndcg_5_list)), 4),
            "ndcg_at_10": round(float(np.mean(ndcg_10_list)), 4),
            "avg_latency_ms": round(float(np.mean(latencies)), 2),
        }

    def compare_all_baselines(
        self,
        dataset: RankingDataset,
        alpha: float = 0.60,
    ) -> List[Dict[str, Any]]:
        """Runs comparative evaluation across BM25, Vector, Hybrid, and Hybrid + ML Ranker."""
        methods = ["bm25", "vector", "hybrid"]
        if self.ranker_model and self.ranker_model.is_trained:
            methods.append("hybrid_ml_ranker")

        comparisons = []
        for m in methods:
            metrics = self.evaluate_retrieval_method(dataset, method=m, alpha=alpha)
            comparisons.append(metrics)
        return comparisons
