"""Unit tests for local query classification, hallucination protection, and RAG pipeline."""

from pathlib import Path
from app.reasoning.query_classifier import QueryClassifier
from app.reasoning.hallucination_guard import HallucinationGuard
from app.reasoning.rag_pipeline import CodeRAGPipeline
from app.pipeline import IngestionPipeline


def test_query_classifier():
    classifier = QueryClassifier()

    q1 = classifier.classify("What is the architecture of the system?")
    assert q1.category == "Architecture"

    q2 = classifier.classify("Where is the UserService class defined?")
    assert q2.category == "Symbol Search"

    q3 = classifier.classify("Are there any security vulnerabilities or SQL injection risks?")
    assert q3.category == "Security"


def test_rag_pipeline_sample_repo(sample_repo_path: Path):
    pipeline = IngestionPipeline()
    pipeline.run_local(sample_repo_path)

    rag = CodeRAGPipeline()
    res = rag.ask("sample_repo", "How is user login and password authentication handled?", top_k=3)

    assert res.repository_id == "sample_repo"
    assert res.is_sufficient_evidence is True
    assert res.confidence_level in ("HIGH", "MEDIUM", "LOW")
    assert len(res.sources) >= 1
    assert "auth.py" in res.sources[0].file_path
    assert len(res.reasoning_evidence) >= 1
