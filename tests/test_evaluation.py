"""Unit and integration tests for retrieval evaluation metrics and benchmark runner."""

from pathlib import Path
from app.evaluation.metrics import compute_recall_at_k, compute_mrr
from app.evaluation.evaluator import CodeRetrievalEvaluator
from app.retrieval.search import SearchEngine
from app.pipeline import IngestionPipeline
from app.config import settings


def test_metrics_calculation():
    # Case 1: Ground truth found at ranks [1, 2, None, 4]
    ranks = [1, 2, None, 4]

    assert compute_recall_at_k(ranks, 1) == 0.25  # 1/4
    assert compute_recall_at_k(ranks, 2) == 0.50  # 2/4
    assert compute_recall_at_k(ranks, 3) == 0.50  # 2/4
    assert compute_recall_at_k(ranks, 5) == 0.75  # 3/4

    # MRR = (1/1 + 1/2 + 0 + 1/4) / 4 = (1 + 0.5 + 0.25) / 4 = 1.75 / 4 = 0.4375
    assert abs(compute_mrr(ranks) - 0.4375) < 1e-4

    # Edge cases
    assert compute_recall_at_k([], 1) == 0.0
    assert compute_mrr([]) == 0.0


def test_evaluator_on_sample_repo(sample_repo_path: Path):
    pipeline = IngestionPipeline()
    pipeline.run_local(sample_repo_path)

    index_dir = settings.INDEXES_DIR / "sample_repo"
    engine = SearchEngine.from_index_dir(index_dir)
    evaluator = CodeRetrievalEvaluator(engine)

    dataset_path = settings.BASE_DIR / "app" / "evaluation" / "benchmark_dataset.json"
    queries = evaluator.load_benchmark_queries(dataset_path)
    assert len(queries) >= 7

    eval_result = evaluator.evaluate(queries, top_k=5)
    assert eval_result.total_queries == len(queries)
    # With semantic search on sample repo, Recall@3 and Recall@5 should be high (>= 0.7)
    assert eval_result.recall_at_5 >= 0.7
    assert eval_result.mean_reciprocal_rank > 0.5
