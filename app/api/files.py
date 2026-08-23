"""File tree and source code viewer API router."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from app.services.repository_service import repository_service

router = APIRouter()


@router.get("/{repository_id}/files")
async def get_repository_files(repository_id: str):
    """Returns the file tree and symbol overview for a repository."""
    try:
        return repository_service.get_file_tree(repository_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load file tree: {e}")


@router.get("/{repository_id}/file-content")
async def get_file_content(repository_id: str, path: str = Query(..., description="Relative file path")):
    """Returns raw source code, line counts, and metadata for inspection in the Code Viewer."""
    try:
        return repository_service.get_file_content(repository_id, path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file content: {e}")
