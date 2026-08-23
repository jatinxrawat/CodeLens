"""Code Relevance Ranker Trainer.

Extracts feature matrices from training repository splits and trains the GBDT ranker model.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import numpy as np

from app.models.code_chunk import CodeChunk
from app.ml.dataset.dataset_schema import RankingDataset
from app.ml.ranking.ranker_model import CodeRankerModel
from app.ml.ranking.feature_extractor import RankingFeatureExtractor
from app.ml.ranking.evaluator import RankingEvaluator
from app.services.repository_service import repository_service


class RankerTrainer:
    """Trains and validates the Code Ranker Model."""

    def __init__(
        self,
        model_type: str = "hist_gbdt",
        n_estimators: int = 100,
        learning_rate: float = 0.05,
        max_depth: int = 4,
        random_seed: int = 42,
    ):
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_seed = random_seed
        self.feature_extractor = RankingFeatureExtractor()

    def _prepare_feature_matrix(
        self,
        dataset: RankingDataset,
        target_repositories: Optional[list] = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Extracts X (feature matrix) and y (relevance labels) from dataset samples."""
        allowed_repos = set(target_repositories) if target_repositories else None
        selected_samples = [
            s for s in dataset.samples
            if allowed_repos is None or s.repository_id in allowed_repos
        ]

        if not selected_samples:
            selected_samples = dataset.samples

        # Cache chunks by (repo_id, chunk_id)
        chunk_cache = {}
        for repo_id in set(s.repository_id for s in selected_samples):
            raw = repository_service.get_chunks_for_repository(repo_id)
            for r in raw:
                c = CodeChunk.from_dict(r)
                chunk_cache[(repo_id, c.chunk_id)] = c

        # Pre-encode unique queries in batch
        unique_queries = list(set(s.query for s in selected_samples))
        query_embeddings = {}
        if unique_queries:
            q_vecs = self.feature_extractor.embedding_model.encode(unique_queries, batch_size=64)
            for q, v in zip(unique_queries, q_vecs):
                query_embeddings[q] = v

        # Pre-encode unique chunks in batch
        unique_chunk_keys = list(set((s.repository_id, s.code_chunk_id) for s in selected_samples))
        chunk_embeddings = {}
        chunks_to_encode = []
        for k in unique_chunk_keys:
            c = chunk_cache.get(k)
            if c:
                chunks_to_encode.append((k, c.get_embeddable_text()))
        if chunks_to_encode:
            c_texts = [text for _, text in chunks_to_encode]
            c_vecs = self.feature_extractor.embedding_model.encode(c_texts, batch_size=64)
            for (k, _), v in zip(chunks_to_encode, c_vecs):
                chunk_embeddings[k] = v

        X_list = []
        y_list = []

        for s in selected_samples:
            chunk = chunk_cache.get((s.repository_id, s.code_chunk_id))
            if not chunk:
                chunk = CodeChunk(
                    chunk_id=s.code_chunk_id,
                    repo_name=s.repository_id,
                    file_path=s.file_path,
                    language=s.language,
                    symbol_name=s.symbol_name,
                    start_line=1,
                    end_line=len(s.code_text.splitlines()),
                    code=s.code_text,
                )

            q_emb = query_embeddings.get(s.query)
            c_emb = chunk_embeddings.get((s.repository_id, s.code_chunk_id))

            feats = self.feature_extractor.extract_features(
                s.query, chunk, query_embedding=q_emb, chunk_embedding=c_emb
            )
            vec = np.array([feats[name] for name in self.feature_extractor.FEATURE_NAMES], dtype=np.float32)
            X_list.append(vec)
            y_list.append(s.label)

        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list, dtype=np.int32)
        return X, y

    def train(
        self,
        dataset: RankingDataset,
    ) -> tuple[CodeRankerModel, Dict[str, Any]]:
        """Trains the Code Ranker Model using train_repositories and evaluates on val_repositories."""
        train_repos = dataset.train_repositories if dataset.train_repositories else None
        val_repos = dataset.val_repositories if dataset.val_repositories else None

        X_train, y_train = self._prepare_feature_matrix(dataset, train_repos)
        
        ranker = CodeRankerModel(
            model_type=self.model_type,
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            random_seed=self.random_seed,
        )
        ranker.fit(X_train, y_train)

        # Evaluate on validation split
        evaluator = RankingEvaluator(ranker_model=ranker)
        val_metrics = evaluator.evaluate_retrieval_method(dataset, method="hybrid_ml_ranker")

        return ranker, val_metrics
