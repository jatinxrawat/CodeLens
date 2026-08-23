"""End-to-End Local Evidence-Based RAG Pipeline.

Orchestrates query classification, hybrid retrieval, hallucination guarding,
local answer synthesis, citation formatting, and explainability reasoning.
"""

import time
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from app.config import settings
from app.retrieval.hybrid_search import HybridSearchEngine
from app.models.code_chunk import SearchResult
from app.reasoning.query_classifier import QueryClassifier, QueryClassification
from app.reasoning.hallucination_guard import HallucinationGuard, EvidenceAssessment
from app.reasoning.local_llm import LocalCodeReasoner
from app.reasoning.explainability import ExplainabilityEngine, DecisionFactor


class CitationSource(BaseModel):
    file_path: str
    symbol_name: Optional[str] = None
    chunk_type: str
    start_line: int
    end_line: int
    similarity: float
    code_preview: str
    rank: int


class RAGAnswerResponse(BaseModel):
    query: str
    repository_id: str
    category: str
    confidence_level: str
    confidence_score: float
    answer: str
    sources: List[CitationSource]
    reasoning_evidence: List[DecisionFactor]
    latency_ms: float
    is_sufficient_evidence: bool


class CodeRAGPipeline:
    """Coordinates local evidence-based question answering with hallucination protection."""

    def __init__(self):
        self.classifier = QueryClassifier()
        self.guard = HallucinationGuard()
        self.reasoner = LocalCodeReasoner()
        self.explainability = ExplainabilityEngine()

    def ask(
        self,
        repo_name: str,
        query: str,
        top_k: int = 5,
        alpha: float = 0.6,
    ) -> RAGAnswerResponse:
        """Processes user question through the complete evidence-based RAG pipeline."""
        start_time = time.time()
        index_dir = settings.INDEXES_DIR / repo_name
        if not index_dir.exists() or not (index_dir / "index.faiss").exists():
            raise FileNotFoundError(f"Repository index '{repo_name}' not found.")

        # 1. Classify Query
        classification: QueryClassification = self.classifier.classify(query)

        # 2. Retrieve Candidate Chunks via Hybrid Search Engine
        engine = HybridSearchEngine.from_index_dir(index_dir)
        candidate_count = max(top_k * 3, 15)
        raw_results, search_lat = engine.search(
            query=query,
            top_k=candidate_count,
            mode="hybrid",
            alpha=alpha,
        )

        # 3. Apply Trained ML Ranker if Active
        from app.ml.tracking.model_registry import model_registry
        active_ranker = model_registry.get_active_ranker()
        if active_ranker and active_ranker.is_trained and raw_results:
            candidate_chunks = [r.chunk for r in raw_results]
            reranked = active_ranker.rank_candidates(query, candidate_chunks, top_k=top_k)
            # Reconstruct SearchResult list with ML scores
            evidence_results = []
            for item in reranked:
                c = item["chunk"]
                score = item["relevance_score"]
                evidence_results.append(
                    SearchResult(
                        chunk=c,
                        score=score,
                        dense_score=score,
                        bm25_score=0.0,
                        rank=len(evidence_results) + 1,
                    )
                )
        else:
            evidence_results = raw_results[:top_k]

        # 4. Hallucination Guard Verification
        assessment: EvidenceAssessment = self.guard.evaluate_evidence(evidence_results)

        if not assessment.is_sufficient:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return RAGAnswerResponse(
                query=query,
                repository_id=repo_name,
                category=classification.category,
                confidence_level="INSUFFICIENT",
                confidence_score=assessment.confidence_score,
                answer=assessment.rejection_reason or "I don't have enough evidence in the repository to answer this confidently.",
                sources=[],
                reasoning_evidence=[],
                latency_ms=latency_ms,
                is_sufficient_evidence=False,
            )

        # 5. Synthesize Answer
        answer_text = self.reasoner.synthesize_answer(
            query=query,
            category=classification.category,
            evidence_results=evidence_results,
        )

        # 5. Format Sources & Citations
        sources = [
            CitationSource(
                file_path=r.chunk.file_path,
                symbol_name=r.chunk.symbol_name,
                chunk_type=r.chunk.chunk_type.value,
                start_line=r.chunk.start_line,
                end_line=r.chunk.end_line,
                similarity=round(r.score, 4),
                code_preview=r.chunk.code[:200] + ("..." if len(r.chunk.code) > 200 else ""),
                rank=r.rank,
            )
            for r in raw_results
        ]

        # 6. Extract Explainability Decision Factors
        top_res = raw_results[0]
        decision_factors = self.explainability.extract_decision_factors(
            query=query,
            result=top_res,
            in_degree=len(raw_results),
            layer_name=None,
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return RAGAnswerResponse(
            query=query,
            repository_id=repo_name,
            category=classification.category,
            confidence_level=assessment.confidence_level,
            confidence_score=assessment.confidence_score,
            answer=answer_text,
            sources=sources,
            reasoning_evidence=decision_factors,
            latency_ms=latency_ms,
            is_sufficient_evidence=True,
        )


rag_pipeline = CodeRAGPipeline()
