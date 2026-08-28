"""Repository Analysis Reports API router."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from app.services.report_service import report_service

router = APIRouter()


@router.get("/{repository_id}/report")
def get_report_json(repository_id: str, refresh: bool = Query(False, description="Force recompute report")):
    """Returns full structured repository analysis report as JSON."""
    try:
        return report_service.generate_report_data(repository_id, force_refresh=refresh)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")


@router.get("/{repository_id}/report/markdown", response_class=PlainTextResponse)
def get_report_markdown(repository_id: str, refresh: bool = Query(False, description="Force recompute report")):
    """Returns downloadable GitHub-Flavored Markdown report."""
    try:
        return report_service.generate_markdown_report(repository_id, force_refresh=refresh)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate markdown report: {e}")
