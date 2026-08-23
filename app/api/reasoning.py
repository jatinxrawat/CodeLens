"""Reasoning & Evidence-Grounded RAG API router."""

from fastapi import APIRouter, HTTPException
from app.schemas.reasoning import AskRequest, AskResponse
from app.reasoning.rag_pipeline import rag_pipeline

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask_codebase(request: AskRequest):
    """Processes natural language questions with local evidence-based citations and hallucination protection."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Question query cannot be empty.")

    try:
        res = rag_pipeline.ask(
            repo_name=request.repository_id,
            query=request.query.strip(),
            top_k=request.top_k,
            alpha=request.alpha,
        )
        return AskResponse(
            query=res.query,
            repository_id=res.repository_id,
            category=res.category,
            confidence_level=res.confidence_level,
            confidence_score=res.confidence_score,
            answer=res.answer,
            sources=res.sources,
            reasoning_evidence=res.reasoning_evidence,
            latency_ms=res.latency_ms,
            is_sufficient_evidence=res.is_sufficient_evidence,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {e}")
