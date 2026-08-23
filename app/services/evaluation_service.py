"""Service layer for running comparative retrieval evaluations (BM25 vs Vector vs Hybrid)."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models.code_chunk import EvaluationQuery
from app.retrieval.hybrid_search import HybridSearchEngine
from app.evaluation.metrics import compute_recall_at_k, compute_mrr
from app.schemas.evaluation import EvaluationResponse, ModelComparisonResult


class EvaluationService:
    """Runs benchmark evaluation comparing retrieval modes against ground truth."""

    def __init__(self):
        pass

    def run_evaluation(
        self,
        repo_name: str,
        custom_dataset_path: Optional[str] = None,
        top_k: int = 5,
    ) -> EvaluationResponse:
        """Evaluates BM25, Vector Search, and Hybrid Search on the specified repository."""
        index_dir = settings.INDEXES_DIR / repo_name
        if not index_dir.exists() or not (index_dir / "index.faiss").exists():
            raise FileNotFoundError(f"Repository '{repo_name}' is not indexed.")

        engine = HybridSearchEngine.from_index_dir(index_dir)

        # Load queries
        ds_path = Path(custom_dataset_path) if custom_dataset_path else (settings.BASE_DIR / "app" / "evaluation" / "benchmark_dataset.json")
        if not ds_path.exists():
            raise FileNotFoundError(f"Benchmark dataset not found at {ds_path}")

        with open(ds_path, "r", encoding="utf-8") as f:
            raw_queries = json.load(f)
        queries = [EvaluationQuery(**item) for item in raw_queries]

        configs = [
            {"name": "BM25 (Keyword)", "mode": "keyword", "alpha": 0.0},
            {"name": "Dense Vector (FAISS)", "mode": "vector", "alpha": 1.0},
            {"name": "Hybrid Search (α=0.5)", "mode": "hybrid", "alpha": 0.5},
            {"name": "Hybrid Search (α=0.7)", "mode": "hybrid", "alpha": 0.7},
        ]

        comparisons: List[ModelComparisonResult] = []
        detailed_breakdown: List[Dict[str, Any]] = []

        for cfg in configs:
            ranks: List[Optional[int]] = []
            latencies: List[float] = []

            for q in queries:
                results, latency = engine.search(
                    query=q.query,
                    top_k=top_k,
                    mode=cfg["mode"],
                    alpha=cfg["alpha"],
                )
                latencies.append(latency)

                found_rank: Optional[int] = None
                for r in results:
                    file_matches = q.expected_file.lower() in r.chunk.file_path.lower()
                    symbol_matches = True
                    if q.expected_symbol:
                        symbol_matches = bool(
                            r.chunk.symbol_name and q.expected_symbol.lower() in r.chunk.symbol_name.lower()
                        )
                    if file_matches and symbol_matches:
                        found_rank = r.rank
                        break
                ranks.append(found_rank)

            rec_1 = compute_recall_at_k(ranks, 1)
            rec_3 = compute_recall_at_k(ranks, 3)
            rec_5 = compute_recall_at_k(ranks, 5)
            mrr_val = compute_mrr(ranks)
            avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

            comparisons.append(
                ModelComparisonResult(
                    mode=cfg["name"],
                    alpha=cfg["alpha"],
                    recall_at_1=round(rec_1, 4),
                    recall_at_3=round(rec_3, 4),
                    recall_at_5=round(rec_5, 4),
                    mean_reciprocal_rank=round(mrr_val, 4),
                    avg_latency_ms=round(avg_lat, 2),
                )
            )

        # Single query breakdown for hybrid alpha=0.7
        for q in queries:
            results, lat = engine.search(query=q.query, top_k=3, mode="hybrid", alpha=0.7)
            found_rank = None
            for r in results:
                if q.expected_file.lower() in r.chunk.file_path.lower():
                    found_rank = r.rank
                    break
            detailed_breakdown.append({
                "query": q.query,
                "expected_file": q.expected_file,
                "expected_symbol": q.expected_symbol,
                "found_rank": found_rank,
                "latency_ms": round(lat, 2),
                "top_result": results[0].chunk.file_path if results else "none",
            })

        return EvaluationResponse(
            repository_id=repo_name,
            total_queries=len(queries),
            comparisons=comparisons,
            query_breakdown=detailed_breakdown,
        )


evaluation_service = EvaluationService()
