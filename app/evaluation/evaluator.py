"""Benchmark evaluation engine for assessing semantic code retrieval quality."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.models.code_chunk import EvaluationQuery, EvaluationResult
from app.retrieval.search import SearchEngine
from app.evaluation.metrics import compute_recall_at_k, compute_mrr


class CodeRetrievalEvaluator:
    """Evaluates semantic search accuracy against ground truth test cases."""

    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    def load_benchmark_queries(self, dataset_path: Path) -> List[EvaluationQuery]:
        """Loads evaluation test cases from a JSON file."""
        with open(dataset_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return [EvaluationQuery(**item) for item in raw_data]

    def evaluate(self, queries: List[EvaluationQuery], top_k: int = 5) -> EvaluationResult:
        """Runs queries through the search engine and computes Recall@1, Recall@3, Recall@5, and MRR."""
        ranks: List[Optional[int]] = []
        detailed_evaluations: List[Dict[str, Any]] = []

        for q in queries:
            results, latency = self.search_engine.search(q.query, top_k=top_k)

            found_rank: Optional[int] = None
            for r in results:
                # Check if result matches expected file and (if specified) expected symbol
                file_matches = q.expected_file.lower() in r.chunk.file_path.lower()
                symbol_matches = True
                if q.expected_symbol:
                    symbol_matches = bool(
                        r.chunk.symbol_name
                        and q.expected_symbol.lower() in r.chunk.symbol_name.lower()
                    )

                if file_matches and symbol_matches:
                    found_rank = r.rank
                    break

            ranks.append(found_rank)
            detailed_evaluations.append(
                {
                    "query": q.query,
                    "expected_file": q.expected_file,
                    "expected_symbol": q.expected_symbol,
                    "found_rank": found_rank,
                    "latency_ms": round(latency, 2),
                    "top_retrieved": [
                        {
                            "file": res.chunk.file_path,
                            "symbol": res.chunk.symbol_name,
                            "score": round(res.score, 4),
                        }
                        for res in results[:3]
                    ],
                }
            )

        recall_1 = compute_recall_at_k(ranks, 1)
        recall_3 = compute_recall_at_k(ranks, 3)
        recall_5 = compute_recall_at_k(ranks, 5)
        mrr = compute_mrr(ranks)

        return EvaluationResult(
            total_queries=len(queries),
            recall_at_1=round(recall_1, 4),
            recall_at_3=round(recall_3, 4),
            recall_at_5=round(recall_5, 4),
            mean_reciprocal_rank=round(mrr, 4),
            query_evaluations=detailed_evaluations,
        )
