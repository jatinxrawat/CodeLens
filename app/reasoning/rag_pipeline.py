"""End-to-End Local and Cloud (Gemini) Evidence-Based RAG Pipeline.

Orchestrates query classification, hybrid retrieval, hallucination guarding,
LLM answer synthesis (Gemini Flash/Pro default with Local fallback),
file+line range citations, caching, and student-focused explanation modes.
"""

import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

from app.config import settings
from app.retrieval.hybrid_search import HybridSearchEngine
from app.models.code_chunk import SearchResult
from app.reasoning.query_classifier import QueryClassifier, QueryClassification
from app.reasoning.hallucination_guard import HallucinationGuard, EvidenceAssessment
from app.reasoning.local_llm import LocalCodeReasoner
from app.reasoning.explainability import ExplainabilityEngine, DecisionFactor
from app.reasoning.provider.manager import provider_manager, get_llm_provider
from app.services.cache_service import cache_service
from app.utils.logger import logger


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
    """Coordinates evidence-based question answering with Gemini and Local LLM support."""

    def __init__(self):
        self.classifier = QueryClassifier()
        self.guard = HallucinationGuard()
        self.local_reasoner = LocalCodeReasoner()
        self.explainability = ExplainabilityEngine()

    def _get_repo_commit_or_hash(self, repo_name: str, index_dir: Path) -> str:
        meta_file = index_dir / "metadata.json"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    return meta.get("indexed_at", "v1")
            except Exception:
                pass
        return "v1"

    def ask(
        self,
        repo_name: str,
        query: str,
        top_k: int = 5,
        alpha: float = 0.6,
        mode: str = "beginner",
        provider_override: Optional[str] = None,
        model_tier: str = "flash",
    ) -> RAGAnswerResponse:
        """Processes user question through the complete evidence-based RAG pipeline."""
        start_time = time.time()
        classification: QueryClassification = self.classifier.classify(query)

        # Determine index location
        has_index = False
        index_dir = None
        if repo_name and repo_name.strip() and repo_name != "general":
            candidate_dir = settings.INDEXES_DIR / repo_name
            if candidate_dir.exists() and (candidate_dir / "index.faiss").exists():
                has_index = True
                index_dir = candidate_dir

        repo_commit = self._get_repo_commit_or_hash(repo_name, index_dir) if index_dir else "general"

        # Check Answer Cache
        cache_key = cache_service.make_answer_key(
            repo_id=repo_name or "general",
            commit_or_hash=repo_commit,
            query=query,
            mode=f"{mode}:{provider_override or provider_manager.active_provider_name}:{model_tier}",
        )
        cached_result = cache_service.get_cached_answer(cache_key)
        if cached_result:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return RAGAnswerResponse(
                query=query,
                repository_id=repo_name or "general",
                category=classification.category,
                confidence_level="HIGH" if cached_result["confidence_score"] >= 0.75 else "MEDIUM",
                confidence_score=cached_result["confidence_score"],
                answer=cached_result["answer"],
                sources=[CitationSource(**s) for s in cached_result["sources"]],
                reasoning_evidence=[DecisionFactor(**d) for d in cached_result["reasoning_evidence"]],
                latency_ms=latency_ms,
                is_sufficient_evidence=True,
            )

        provider = provider_manager.get_provider(provider_override)

        # 1. General Mode (No Repository Attached)
        if not has_index:
            answer_text = self._synthesize_general_ai(
                provider=provider,
                query=query,
                category=classification.category,
                mode=mode,
                model_tier=model_tier,
            )
            latency_ms = round((time.time() - start_time) * 1000, 2)
            res = RAGAnswerResponse(
                query=query,
                repository_id=repo_name or "general",
                category="GENERAL_INTELLIGENCE",
                confidence_level="HIGH",
                confidence_score=0.95,
                answer=answer_text,
                sources=[],
                reasoning_evidence=[],
                latency_ms=latency_ms,
                is_sufficient_evidence=True,
            )
            cache_service.set_cached_answer(
                cache_key=cache_key,
                answer=res.answer,
                sources=[],
                reasoning_evidence=[],
                confidence_score=res.confidence_score,
                latency_ms=res.latency_ms,
            )
            return res

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

        # 4. Hallucination Guard Verification & Confidence Threshold
        assessment: EvidenceAssessment = self.guard.evaluate_evidence(evidence_results)

        top_similarity = evidence_results[0].score if evidence_results else 0.0

        # Format sources
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
            for r in evidence_results
        ]

        # Check for low confidence / Not Found in codebase
        # If top similarity is very low and evidence is insufficient, answer "not found in this codebase"
        if not evidence_results or top_similarity < 0.22 or (not assessment.is_sufficient and top_similarity < 0.28):
            answer_text = (
                f"**Not found in this codebase.**\n\n"
                f"The query `\"{query}\"` did not match any relevant functions, classes, or symbols in repository `{repo_name}` with sufficient confidence (top similarity: {top_similarity:.2f}).\n\n"
                f"**Suggestions:**\n"
                f"- Check for typos in symbol or function names.\n"
                f"- Verify if the code is in an unsupported extension or excluded directory (`.git`, `node_modules`, etc.).\n"
                f"- Switch to **Search only** mode to scan for exact substring matches across all files."
            )
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return RAGAnswerResponse(
                query=query,
                repository_id=repo_name,
                category=classification.category,
                confidence_level="LOW",
                confidence_score=round(top_similarity, 2),
                answer=answer_text,
                sources=sources[:2] if sources else [],
                reasoning_evidence=[],
                latency_ms=latency_ms,
                is_sufficient_evidence=False,
            )

        # 5. Synthesize Grounded Answer with Citations
        answer_text = self._synthesize_grounded_answer(
            provider=provider,
            query=query,
            repo_name=repo_name,
            evidence_results=evidence_results,
            category=classification.category,
            mode=mode,
            model_tier=model_tier,
        )

        # 6. Extract Explainability Decision Factors
        top_res = evidence_results[0]
        decision_factors = self.explainability.extract_decision_factors(
            query=query,
            result=top_res,
            in_degree=len(evidence_results),
            layer_name=None,
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        rag_resp = RAGAnswerResponse(
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

        # Store in persistent SQLite cache
        cache_service.set_cached_answer(
            cache_key=cache_key,
            answer=rag_resp.answer,
            sources=[s.dict() for s in rag_resp.sources],
            reasoning_evidence=[d.dict() for d in rag_resp.reasoning_evidence],
            confidence_score=rag_resp.confidence_score,
            latency_ms=rag_resp.latency_ms,
        )

        return rag_resp

    def _synthesize_grounded_answer(
        self,
        provider,
        query: str,
        repo_name: str,
        evidence_results: List[SearchResult],
        category: str,
        mode: str,
        model_tier: str,
    ) -> str:
        """Synthesizes answer using active LLM provider (Gemini or Local) with strict file:line citations."""
        # If provider is Local or Gemini is unavailable, use local synthesizer
        if provider.provider_name == "local":
            return self.local_reasoner.synthesize_answer(
                query=query,
                category=category,
                evidence_results=evidence_results,
            )

        # Build context prompt with precise file paths and line ranges
        context_parts = []
        for i, res in enumerate(evidence_results, 1):
            c = res.chunk
            header = f"--- Source {i}: [{c.file_path}:L{c.start_line}-L{c.end_line}] (Type: {c.chunk_type.value}, Symbol: {c.symbol_name or 'N/A'}) ---"
            context_parts.append(f"{header}\n```{c.language}\n{c.code}\n```")

        context_str = "\n\n".join(context_parts)

        # Style customization based on mode
        if mode == "beginner":
            style_instruction = (
                "You are an empathetic, encouraging computer science mentor for college students.\n"
                "- Explain how the code works step by step using simple, approachable language.\n"
                "- Define any tricky jargon, design patterns, or framework concepts when they appear.\n"
                "- Highlight key functions, imports, and variables.\n"
                "- Add a brief 'Student Tip' box at the end with advice on how to explore or test this code."
            )
        else:
            style_instruction = (
                "You are a principal software architect.\n"
                "- Provide a concise, high-density technical analysis.\n"
                "- Detail invariants, architectural layers, data mutations, and algorithmic complexity.\n"
                "- Be precise and to the point."
            )

        system_prompt = (
            f"You are CodeLens AI, an intelligent code analysis engine.\n"
            f"You are answering questions about repository '{repo_name}'.\n\n"
            f"{style_instruction}\n\n"
            "MANDATORY CITATION RULES:\n"
            "1. You MUST cite file path and line numbers whenever referencing any code, e.g. `[src/auth/service.py:L45-80]`.\n"
            "2. Ground every single claim strictly on the provided sources below.\n"
            "3. If the answer cannot be determined from the provided sources, explicitly state: 'not found in this codebase'. Never hallucinate missing implementation details."
        )

        user_prompt = f"Context Code from Repository `{repo_name}`:\n\n{context_str}\n\nQuestion: {query}\n\nAnswer:"

        try:
            return provider.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model_tier=model_tier,
                temperature=0.2,
                max_tokens=1500,
            )
        except Exception as e:
            logger.warning(f"Gemini generation failed: {e}. Falling back to local reasoning engine.")
            return self.local_reasoner.synthesize_answer(
                query=query,
                category=category,
                evidence_results=evidence_results,
            )

    def _synthesize_general_ai(
        self,
        provider,
        query: str,
        category: str,
        mode: str,
        model_tier: str,
    ) -> str:
        """General AI coding assistant mode when no repository is attached."""
        if provider.provider_name == "local":
            return self.local_reasoner.synthesize_general_answer(query, category=category)

        if mode == "beginner":
            system_prompt = (
                "You are CodeLens AI, a friendly coding tutor for college students.\n"
                "Explain computer science, programming, algorithms, and web/systems concepts clearly.\n"
                "Provide clean code examples, step-by-step breakdowns, and practical tips."
            )
        else:
            system_prompt = (
                "You are CodeLens AI, an advanced AI software engineering assistant.\n"
                "Provide deep technical solutions, production best practices, and clean code examples."
            )

        try:
            return provider.generate(
                prompt=query,
                system_prompt=system_prompt,
                model_tier=model_tier,
                temperature=0.3,
                max_tokens=1200,
            )
        except Exception as e:
            logger.warning(f"Gemini general AI call failed: {e}. Falling back to local synthesizer.")
            return self.local_reasoner.synthesize_general_answer(query, category=category)


rag_pipeline = CodeRAGPipeline()
