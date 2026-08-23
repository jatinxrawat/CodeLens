"""Semantic and hybrid code search API router."""

from fastapi import APIRouter, HTTPException
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import search_service

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_codebase(request: SearchRequest):
    """Performs semantic, keyword, or hybrid retrieval across the indexed codebase."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    try:
        return search_service.search(request)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")
