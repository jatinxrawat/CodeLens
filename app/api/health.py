"""Health check API router."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.2.0"
    service: str = "Local AI Code Intelligence Engine"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns the operational status of the service."""
    return HealthResponse(status="ok")
