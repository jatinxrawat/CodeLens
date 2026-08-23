"""Dependency and import graph API router."""

from fastapi import APIRouter, HTTPException
from app.schemas.graph import GraphResponse
from app.services.graph_service import graph_service

router = APIRouter()


@router.get("/{repository_id}/graph", response_model=GraphResponse)
async def get_repository_graph(repository_id: str):
    """Returns the static import and module dependency network graph."""
    try:
        return graph_service.get_repository_graph(repository_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dependency graph: {e}")
