"""FastAPI application entrypoint for the public v2 assessment service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_router
from backend.app.api.v2.router import router as api_v2_router
from backend.app.api.v2.service import AnonymousAssessmentService
from backend.app.core.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the public app without loading archived research artifacts."""

    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = resolved_settings
        app.state.anonymous_assessment_service = AnonymousAssessmentService(
            resolved_settings
        )
        yield

    app = FastAPI(
        title="AlterScore Public Assessment API",
        version=resolved_settings.api_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_origins),
        allow_origin_regex=resolved_settings.cors_origin_regex,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(api_router, prefix="/api")
    app.include_router(api_v2_router, prefix="/api")

    @app.middleware("http")
    async def add_public_privacy_headers(request, call_next):
        is_public_route = request.url.path.startswith("/api/v2/") or request.url.path in {
            "/api/live",
            "/api/ready",
            "/api/score",
            "/api/debug-score",
        }
        if is_public_route:
            # Keep the source address only long enough for the v2 limiter to
            # derive its salted hash, then redact it before access logging.
            request.state.phase4_network_host = (
                request.client.host if request.client is not None else None
            )
            request.scope["client"] = ("redacted", 0)
        response = await call_next(request)
        if is_public_route:
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
        return response

    return app


app = create_app()


__all__ = ["app", "create_app"]
