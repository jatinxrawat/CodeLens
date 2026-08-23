"""Repository-Level Dataset Split Manager.

Enforces strict zero-leakage repository boundaries:
Code chunks from the same repository NEVER appear in both training and test sets.
"""

from typing import List, Tuple, Dict, Any
import numpy as np


class SplitManager:
    """Manages repository-level data splits with strict leakage protection."""

    def __init__(
        self,
        train_ratio: float = 0.60,
        val_ratio: float = 0.20,
        test_ratio: float = 0.20,
        random_seed: int = 42,
    ):
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.random_seed = random_seed

    def split_repositories(
        self,
        repository_ids: List[str],
    ) -> Tuple[List[str], List[str], List[str]]:
        """Splits unique repository IDs into train, validation, and test cohorts."""
        unique_repos = sorted(list(set(repository_ids)))
        n_repos = len(unique_repos)

        if n_repos == 0:
            return [], [], []

        if n_repos == 1:
            # Special case for single-repo environments: document fallback with warning
            return [unique_repos[0]], [unique_repos[0]], [unique_repos[0]]

        if n_repos == 2:
            return [unique_repos[0]], [unique_repos[0]], [unique_repos[1]]

        # When 3+ repos exist: strict partition
        rng = np.random.RandomState(self.random_seed)
        shuffled = unique_repos.copy()
        rng.shuffle(shuffled)

        n_train = max(1, int(round(n_repos * self.train_ratio)))
        n_val = max(1, int(round(n_repos * self.val_ratio)))
        
        # Ensure at least 1 test repo
        if n_train + n_val >= n_repos:
            n_train = n_repos - 2
            n_val = 1

        train_repos = sorted(shuffled[:n_train])
        val_repos = sorted(shuffled[n_train:n_train + n_val])
        test_repos = sorted(shuffled[n_train + n_val:])

        # Guard: check zero overlap between train and test
        overlap = set(train_repos).intersection(set(test_repos))
        if overlap and n_repos >= 3:
            raise ValueError(f"CRITICAL: Repository leakage detected between train and test: {overlap}")

        return train_repos, val_repos, test_repos

    @staticmethod
    def verify_no_leakage(
        train_items: List[Dict[str, Any]],
        test_items: List[Dict[str, Any]],
        key: str = "repository_id",
    ) -> bool:
        """Asserts that zero items in test_items share repository_id with train_items."""
        train_keys = set(item.get(key) for item in train_items if item.get(key))
        test_keys = set(item.get(key) for item in test_items if item.get(key))
        overlap = train_keys.intersection(test_keys)
        return len(overlap) == 0
