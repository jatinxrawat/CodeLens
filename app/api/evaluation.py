"""Retrieval evaluation and benchmark comparison API router."""

from fastapi import APIRouter, HTTPException, Query
from app.schemas.evaluation import EvaluateRequest, EvaluationResponse
from app.services.evaluation_service import evaluation_service

router = APIRouter()


@router.post("/{repository_id}/evaluate", response_model=EvaluationResponse)
def evaluate_retrieval_performance(
    repository_id: str,
    request: EvaluateRequest,
    refresh: bool = Query(False, description="Force re-run benchmark evaluation"),
):
    """Runs IR benchmark evaluation comparing BM25 vs Vector Search vs Hybrid Search."""
    try:
        return evaluation_service.run_evaluation(
            repo_name=repository_id,
            custom_dataset_path=request.dataset_path,
            top_k=request.top_k,
            force_refresh=refresh,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")
