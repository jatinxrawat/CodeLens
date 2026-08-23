"""Code Ranking Dataset Generator.

Constructs paired (query, code_chunk) samples with ground-truth positive pairs,
hard negative pairs (top-retrieved non-matching chunks), and random negative pairs.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import random
import json

from app.config import settings
from app.models.code_chunk import CodeChunk
from app.ml.dataset.dataset_schema import RankingSample, RankingDataset
from app.ml.dataset.split_manager import SplitManager
from app.retrieval.vector_store import FaissVectorStore
from app.retrieval.bm25_store import BM25Store
from app.services.repository_service import repository_service


class RankingDatasetGenerator:
    """Generates ground-truth code retrieval training and evaluation datasets."""

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        self.split_manager = SplitManager(random_seed=random_seed)

    def _load_benchmark_queries(self) -> List[Dict[str, Any]]:
        """Loads curated benchmark query definitions."""
        bench_path = settings.BASE_DIR / "app" / "evaluation" / "rag_benchmark_dataset.json"
        if bench_path.exists():
            try:
                return json.loads(bench_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def _synthesize_repo_queries(self, chunks: List[CodeChunk]) -> List[Dict[str, Any]]:
        """Generates realistic developer inquiries from AST symbols, docstrings, and function signatures."""
        queries = []
        for chunk in chunks:
            if not chunk.symbol_name or len(chunk.code.splitlines()) < 3:
                continue

            sym = chunk.symbol_name
            clean_sym = sym.replace("_", " ").replace("-", " ")
            file_name = Path(chunk.file_path).name

            # Query Template 1: Intent based on symbol
            q1 = f"Where is {clean_sym} implemented?"
            queries.append({
                "query": q1,
                "target_file": chunk.file_path,
                "target_symbol": sym,
                "target_chunk_id": chunk.chunk_id,
            })

            # Query Template 2: Natural language concept if docstring exists
            if chunk.docstring and len(chunk.docstring.strip()) > 10:
                doc_first_line = chunk.docstring.strip().splitlines()[0]
                q2 = f"How to {doc_first_line.lower().rstrip('.')}?"
                queries.append({
                    "query": q2,
                    "target_file": chunk.file_path,
                    "target_symbol": sym,
                    "target_chunk_id": chunk.chunk_id,
                })
        return queries

    def build_dataset(
        self,
        repository_ids: Optional[List[str]] = None,
        negatives_per_positive: int = 4,
    ) -> RankingDataset:
        """Constructs a comprehensive ranking dataset across specified repositories."""
        if not repository_ids:
            repo_summaries = repository_service.list_repositories()
            repository_ids = [r.repository_id for r in repo_summaries]

        if not repository_ids:
            repository_ids = ["sample_repo"]

        train_repos, val_repos, test_repos = self.split_manager.split_repositories(repository_ids)

        samples: List[RankingSample] = []
        random.seed(self.random_seed)

        for repo_id in repository_ids:
            raw_chunks = repository_service.get_chunks_for_repository(repo_id)
            if not raw_chunks:
                continue

            chunks = [CodeChunk.from_dict(c) for c in raw_chunks]
            chunk_by_id = {c.chunk_id: c for c in chunks}

            # Gather queries
            queries = self._synthesize_repo_queries(chunks)
            benchmark_queries = self._load_benchmark_queries()
            for bq in benchmark_queries:
                for target_f in bq.get("expected_files", []):
                    matching_chunks = [c for c in chunks if target_f in c.file_path]
                    for mc in matching_chunks:
                        queries.append({
                            "query": bq["question"],
                            "target_file": mc.file_path,
                            "target_symbol": mc.symbol_name,
                            "target_chunk_id": mc.chunk_id,
                        })

            for q_info in queries:
                q_text = q_info["query"]
                target_id = q_info["target_chunk_id"]
                target_chunk = chunk_by_id.get(target_id)
                if not target_chunk:
                    continue

                # 1. Positive Sample (Label = 3: Highly Relevant)
                samples.append(
                    RankingSample(
                        query=q_text,
                        code_chunk_id=target_chunk.chunk_id,
                        repository_id=repo_id,
                        file_path=target_chunk.file_path,
                        symbol_name=target_chunk.symbol_name,
                        language=target_chunk.language,
                        code_text=target_chunk.code,
                        label=3,
                        expected_source=True,
                    )
                )

                # 2. Semi-Positive Sample (Label = 1: Weakly relevant - same file or module)
                same_file_chunks = [c for c in chunks if c.file_path == target_chunk.file_path and c.chunk_id != target_chunk.chunk_id]
                if same_file_chunks:
                    sf_chunk = random.choice(same_file_chunks)
                    samples.append(
                        RankingSample(
                            query=q_text,
                            code_chunk_id=sf_chunk.chunk_id,
                            repository_id=repo_id,
                            file_path=sf_chunk.file_path,
                            symbol_name=sf_chunk.symbol_name,
                            language=sf_chunk.language,
                            code_text=sf_chunk.code,
                            label=1,
                            expected_source=False,
                        )
                    )

                # 3. Negative Samples (Label = 0: Irrelevant chunks from other files)
                other_chunks = [c for c in chunks if c.file_path != target_chunk.file_path]
                if other_chunks:
                    neg_count = min(negatives_per_positive, len(other_chunks))
                    chosen_negs = random.sample(other_chunks, neg_count)
                    for neg_c in chosen_negs:
                        samples.append(
                            RankingSample(
                                query=q_text,
                                code_chunk_id=neg_c.chunk_id,
                                repository_id=repo_id,
                                file_path=neg_c.file_path,
                                symbol_name=neg_c.symbol_name,
                                language=neg_c.language,
                                code_text=neg_c.code,
                                label=0,
                                expected_source=False,
                            )
                        )

        # Calculate statistics
        languages = {}
        labels_count = {}
        for s in samples:
            languages[s.language] = languages.get(s.language, 0) + 1
            labels_count[s.label] = labels_count.get(s.label, 0) + 1

        stats = {
            "total_repositories": len(repository_ids),
            "total_queries": len(set(s.query for s in samples)),
            "total_samples": len(samples),
            "positive_samples": labels_count.get(3, 0),
            "weak_samples": labels_count.get(1, 0),
            "negative_samples": labels_count.get(0, 0),
            "languages": languages,
            "train_repo_count": len(train_repos),
            "val_repo_count": len(val_repos),
            "test_repo_count": len(test_repos),
        }

        dataset = RankingDataset(
            version="1.0.0",
            created_at=datetime.now(timezone.utc).isoformat(),
            total_samples=len(samples),
            train_repositories=train_repos,
            val_repositories=val_repos,
            test_repositories=test_repos,
            samples=samples,
            statistics=stats,
        )

        return dataset

    def save_dataset(self, dataset: RankingDataset, output_path: Optional[Path] = None) -> Path:
        """Saves dataset JSON artifact."""
        if not output_path:
            output_dir = settings.BASE_DIR / "data" / "datasets"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "retrieval_ranking_dataset.json"

        output_path.write_text(dataset.model_dump_json(indent=2), encoding="utf-8")
        return output_path
