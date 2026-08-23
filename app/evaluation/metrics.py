"""Evaluation metrics for information retrieval: Recall@K and Mean Reciprocal Rank (MRR)."""

from typing import List, Optional


def compute_recall_at_k(ranks: List[Optional[int]], k: int) -> float:
    """Computes Recall@K: proportion of queries where the relevant item was retrieved in top K.

    Args:
        ranks: List of 1-indexed ranks where the ground truth appeared, or None if not in retrieved results.
        k: Cutoff rank.
    """
    if not ranks:
        return 0.0
    hits = sum(1 for r in ranks if r is not None and 1 <= r <= k)
    return hits / len(ranks)


def compute_mrr(ranks: List[Optional[int]]) -> float:
    """Computes Mean Reciprocal Rank (MRR): average of reciprocal ranks (1/rank) for ground truth items.

    Args:
        ranks: List of 1-indexed ranks where the ground truth appeared, or None if not found.
    """
    if not ranks:
        return 0.0
    reciprocal_sum = sum((1.0 / r) for r in ranks if r is not None and r > 0)
    return reciprocal_sum / len(ranks)
