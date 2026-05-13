"""FastAPI application entrypoint for AlterScore backend."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_router
from backend.app.core.artifact_loader import LoadedArtifactBundle, load_runtime_artifact_bundle
from backend.app.core.settings import Settings, get_settings
from backend.app.services.scoring import ScoringService


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        artifact_bundle = load_runtime_artifact_bundle(resolved_settings, strict=False)
        app.state.settings = resolved_settings
        app.state.artifact_bundle = artifact_bundle
        app.state.scoring_service = _build_scoring_service(artifact_bundle)
        yield

    app = FastAPI(
        title="AlterScore Backend",
        version=resolved_settings.api_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api")
    return app


def _build_scoring_service(
    artifact_bundle: LoadedArtifactBundle,
) -> ScoringService | None:
    if not artifact_bundle.report.scoring_ready:
        return None
    if artifact_bundle.model is None or artifact_bundle.preprocessor is None:
        return None
    return ScoringService(artifact_bundle)


app = create_app()


__all__ = ["app", "create_app"]
