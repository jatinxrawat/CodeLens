"""Repository Analysis Reports API router."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from app.services.report_service import report_service

router = APIRouter()


@router.get("/{repository_id}/report")
async def get_report_json(repository_id: str):
    """Returns full structured repository analysis report as JSON."""
    try:
        return report_service.generate_report_data(repository_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")


@router.get("/{repository_id}/report/markdown", response_class=PlainTextResponse)
async def get_report_markdown(repository_id: str):
    """Returns downloadable GitHub-Flavored Markdown report."""
    try:
        return report_service.generate_markdown_report(repository_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate markdown report: {e}")
