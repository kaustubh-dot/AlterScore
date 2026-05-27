"""API router composition for AlterScore backend."""

from fastapi import APIRouter

from backend.app.api.v1.routes.analytics import router as analytics_router
from backend.app.api.v1.routes.health import router as health_router
from backend.app.api.v1.routes.score import router as score_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(score_router)
api_router.include_router(analytics_router)


__all__ = ["api_router"]
