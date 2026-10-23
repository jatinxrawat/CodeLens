"""Reasoning & Evidence-Grounded RAG API router."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from app.schemas.reasoning import AskRequest, AskResponse
from app.reasoning.rag_pipeline import rag_pipeline
from app.reasoning.provider.manager import provider_manager
from app.utils.rate_limiter import check_rate_limit

router = APIRouter()


class SetProviderRequest(BaseModel):
    provider: str = Field(..., description="Provider name: 'gemini' or 'local'")


@router.get("/provider")
async def get_provider_status():
    """Returns active LLM provider and available models."""
    return provider_manager.get_provider_status()


@router.post("/provider")
async def set_active_provider(request: SetProviderRequest):
    """Sets the active LLM provider ('gemini' or 'local')."""
    try:
        provider = provider_manager.set_active_provider(request.provider)
        return {
            "status": "success",
            "active_provider": provider.provider_name,
            "message": f"Active provider set to {provider.provider_name}",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ask", response_model=AskResponse, dependencies=[Depends(check_rate_limit)])
async def ask_codebase(request: AskRequest):
    """Processes natural language questions with local/Gemini evidence-based citations and hallucination protection."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Question query cannot be empty.")

    try:
        res = rag_pipeline.ask(
            repo_name=request.repository_id or "",
            query=request.query.strip(),
            top_k=request.top_k,
            alpha=request.alpha,
            mode=request.mode,
            provider_override=request.provider,
            model_tier=request.model_tier,
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
