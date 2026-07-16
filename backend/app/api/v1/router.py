"""Retirement boundary for the removed v1 scoring surface."""

from fastapi import APIRouter

from backend.app.api.v1.routes.retired import router as retired_router

api_router = APIRouter()
api_router.include_router(retired_router)


__all__ = ["api_router"]
