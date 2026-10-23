from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.repositories import router as repositories_router
from app.api.search import router as search_router
from app.api.stats import router as stats_router
from app.api.files import router as files_router
from app.api.graph import router as graph_router
from app.api.evaluation import router as evaluation_router
from app.api.reasoning import router as reasoning_router
from app.api.analysis import router as analysis_router
from app.api.reports import router as reports_router
from app.api.comparison import router as comparison_router
from app.api.incremental import router as incremental_router
from app.api.ml import router as ml_router
from app.api.explore import router as explore_router
from app.api.contribute import router as contribute_router
from app.api.repos import router as repos_router
from app.api.user import router as user_router
from app.api.auth import router as auth_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(repositories_router, prefix="/repositories", tags=["Repositories"])
api_router.include_router(repos_router, tags=["Repos"])
api_router.include_router(explore_router, tags=["Explore"])
api_router.include_router(contribute_router, tags=["Contribute"])
api_router.include_router(user_router, tags=["User & Contributions"])
api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(search_router, tags=["Search"])
api_router.include_router(stats_router, prefix="/repositories", tags=["Stats"])
api_router.include_router(files_router, prefix="/repositories", tags=["Files"])
api_router.include_router(graph_router, prefix="/repositories", tags=["Graph"])
api_router.include_router(evaluation_router, prefix="/repositories", tags=["Evaluation"])
api_router.include_router(reasoning_router, prefix="/reasoning", tags=["Reasoning"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(reports_router, prefix="/repositories", tags=["Reports"])
api_router.include_router(comparison_router, prefix="/repositories", tags=["Comparison"])
api_router.include_router(incremental_router, prefix="/repositories", tags=["Incremental"])
api_router.include_router(ml_router)
