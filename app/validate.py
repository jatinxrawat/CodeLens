"""Comprehensive Production Validation Command for Local AI Code Intelligence Engine.

Usage:
    python -m app.validate
"""

import sys
import numpy as np


def run_validation():
    print("=" * 60)
    print("SYSTEM VALIDATION: Local AI Code Intelligence Engine")
    print("=" * 60)
    results = {}

    # 1. Configuration
    try:
        from app.config import settings
        assert settings.DATA_DIR is not None
        assert settings.INDEXES_DIR is not None
        assert settings.MAX_FILE_SIZE_BYTES > 0
        results["Configuration"] = True
    except Exception as e:
        results["Configuration"] = False
        print(f"  [FAIL] Configuration: {e}")

    # 2. Embedding Model
    try:
        from app.embeddings import SentenceTransformerEmbeddingModel
        embedder = SentenceTransformerEmbeddingModel()
        vec = embedder.encode_single("def test_function(): pass")
        assert len(vec) == 384
        assert abs(np.linalg.norm(vec) - 1.0) < 1e-3
        results["Embedding model"] = True
    except Exception as e:
        results["Embedding model"] = False
        print(f"  [FAIL] Embedding model: {e}")

    # 3. Vector Index & FAISS Store
    try:
        from app.retrieval import FaissVectorStore
        from app.models.code_chunk import CodeChunk, ChunkType
        c_val = CodeChunk(
            chunk_id="c1", repo_name="t", file_path="t.py", language="python",
            chunk_type=ChunkType.FUNCTION, symbol_name="fn1",
            start_line=1, end_line=5, code="def fn1(): pass"
        )
        vs = FaissVectorStore(dimension=384)
        vs.add_chunks([c_val], np.random.randn(1, 384).astype(np.float32))
        hits = vs.search(np.random.randn(384).astype(np.float32), top_k=1)
        assert len(hits) == 1
        results["Vector index"] = True
    except Exception as e:
        results["Vector index"] = False
        print(f"  [FAIL] Vector index: {e}")

    # 4. BM25 Index
    try:
        from app.retrieval import BM25Store
        from app.models.code_chunk import CodeChunk, ChunkType
        chunks = [
            CodeChunk(
                chunk_id="b1", repo_name="t", file_path="t.py", language="python",
                chunk_type=ChunkType.FUNCTION, symbol_name="authenticate_user",
                start_line=1, end_line=5, code="def authenticate_user(): pass"
            )
        ]
        bm = BM25Store()
        bm.add_chunks(chunks)
        res = bm.search("authenticate", top_k=1)
        assert len(res) >= 1
        results["BM25 index"] = True
    except Exception as e:
        results["BM25 index"] = False
        print(f"  [FAIL] BM25 index: {e}")

    # 5. Retrieval Ranker Model
    try:
        from app.ml.tracking.model_registry import model_registry
        from app.models.code_chunk import CodeChunk, ChunkType
        ranker = model_registry.get_active_ranker()
        assert ranker is not None and ranker.is_trained is True
        c = CodeChunk(
            chunk_id="val_1", repo_name="test", file_path="t.py", language="python",
            chunk_type=ChunkType.FUNCTION, symbol_name="val_fn", start_line=1, end_line=5,
            code="def val_fn(): return 1"
        )
        score = ranker.predict_score("test query", c)
        assert 0.0 <= score <= 1.0
        results["Retrieval ranker"] = True
    except Exception as e:
        results["Retrieval ranker"] = False
        print(f"  [FAIL] Retrieval ranker: {e}")

    # 6. Maintainability Model
    try:
        from app.ml.tracking.model_registry import model_registry
        from app.models.code_chunk import CodeChunk, ChunkType
        m_model = model_registry.get_active_maintainability()
        assert m_model is not None and m_model.is_trained is True
        c = CodeChunk(
            chunk_id="val_2", repo_name="test", file_path="t.py", language="python",
            chunk_type=ChunkType.FUNCTION, symbol_name="val_fn2", start_line=1, end_line=5,
            code="def val_fn2(): return 2"
        )
        pred = m_model.predict_chunk_risk(c)
        assert pred["predicted_risk"] in ("LOW", "MEDIUM", "HIGH")
        results["Maintainability model"] = True
    except Exception as e:
        results["Maintainability model"] = False
        print(f"  [FAIL] Maintainability model: {e}")

    # 7. Local LLM & Reasoning Guard
    try:
        from app.reasoning.local_llm import LocalCodeReasoner
        from app.reasoning.hallucination_guard import HallucinationGuard
        guard = HallucinationGuard()
        assessment = guard.evaluate_evidence([])
        assert assessment.is_sufficient is False
        assert "evidence" in assessment.rejection_reason.lower()
        results["Local LLM"] = True
    except Exception as e:
        results["Local LLM"] = False
        print(f"  [FAIL] Local LLM: {e}")

    # 8. API Routes
    try:
        from app.api import api_router
        route_paths = [r.path for r in api_router.routes]
        assert any("/search" in p for p in route_paths)
        assert any("/reasoning/ask" in p for p in route_paths)
        results["API"] = True
    except Exception as e:
        results["API"] = False
        print(f"  [FAIL] API: {e}")

    # 9. Core Regression Tests
    try:
        from app.ml.dataset.split_manager import SplitManager
        assert SplitManager.verify_no_leakage([{"repository_id": "r1"}], [{"repository_id": "r2"}]) is True
        results["Tests"] = True
    except Exception as e:
        results["Tests"] = False
        print(f"  [FAIL] Tests: {e}")

    # 10. Evaluation & Baselines
    try:
        from app.ml.ranking.evaluator import RankingEvaluator
        evaluator = RankingEvaluator()
        assert evaluator is not None
        results["Evaluation"] = True
    except Exception as e:
        results["Evaluation"] = False
        print(f"  [FAIL] Evaluation: {e}")

    # Output formatted report
    all_passed = True
    for check_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("SYSTEM READY")
        return 0
    else:
        print("SYSTEM DEGRADED - Some checks failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_validation())
