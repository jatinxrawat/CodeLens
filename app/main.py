"""FastAPI application entrypoint for Local AI Code Intelligence Engine."""

import os

# Prevent OpenMP barrier spinlock and tokenizer fork deadlocks on macOS / multi-worker reload
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.api import api_router

app = FastAPI(
    title="Local AI Code Intelligence Engine API",
    description="Production-grade local code intelligence, hybrid search, and AST dependency engine.",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

import time
import uuid
from fastapi import Request
from app.utils.logger import logger, StructuredLogger

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def trace_requests_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
    if not request.url.path.startswith("/assets"):
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms)"
        )
    return response

# Include API routes
app.include_router(api_router)

# Mount static frontend build if it exists
static_dist = settings.STATIC_DIR
if static_dist.exists() and (static_dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(static_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = static_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(static_dist / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
