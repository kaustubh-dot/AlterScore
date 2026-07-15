"""FastAPI application entrypoint for AlterScore backend."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_router
from backend.app.api.v2.router import router as api_v2_router
from backend.app.api.v2.service import AnonymousAssessmentService
from backend.app.core.artifact_loader import (
    ArtifactLoadReport,
    LoadedArtifactBundle,
    load_runtime_artifact_bundle,
)
from backend.app.core.rate_limit import configure_rate_limiting
from backend.app.core.settings import Settings, get_settings
from backend.app.services.analytics import AnalyticsService
from backend.app.services.request_logging import RequestLoggingService
from backend.app.services.scoring import ScoringService


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = resolved_settings
        app.state.anonymous_assessment_service = AnonymousAssessmentService(
            resolved_settings
        )
        try:
            artifact_bundle = load_runtime_artifact_bundle(
                resolved_settings, strict=False
            )
        except Exception:
            artifact_bundle = _unavailable_artifact_bundle()
        app.state.artifact_bundle = artifact_bundle
        app.state.request_logging_service = RequestLoggingService(
            resolved_settings.request_log_path,
            artifact_bundle,
        )
        app.state.analytics_service = AnalyticsService(artifact_bundle)
        app.state.scoring_service = _build_scoring_service(artifact_bundle)
        yield

    app = FastAPI(
        title="AlterScore Backend",
        version=resolved_settings.api_version,
        lifespan=lifespan,
    )
    configure_rate_limiting(resolved_settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_origins),
        # Regex allows ephemeral Vercel preview deploys (unique *.vercel.app
        # hostnames per branch/commit) without enumerating every URL. None in
        # local dev, where the static allowlist above is sufficient.
        allow_origin_regex=resolved_settings.cors_origin_regex,
        # The API is stateless and uses no cookies/auth, so credentials are not
        # required. Keeping this False avoids the unsafe combination of
        # credentialed requests with a wildcard/reflected origin.
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api")
    app.include_router(api_v2_router, prefix="/api")

    @app.middleware("http")
    async def add_phase4_privacy_headers(request, call_next):
        is_phase4_route = request.url.path.startswith("/api/v2/") or request.url.path in {
            "/api/live",
            "/api/ready",
        }
        if is_phase4_route:
            # Uvicorn's default access logger reads ``scope['client']`` after
            # the app returns. Keep the temporary source only long enough to
            # derive a salted rate-limit hash, then redact that scope value so
            # no Phase 4 request writes a raw address to access logs.
            request.state.phase4_network_host = (
                request.client.host if request.client is not None else None
            )
            request.scope["client"] = ("redacted", 0)
        response = await call_next(request)
        if is_phase4_route:
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
        return response

    return app


def _build_scoring_service(
    artifact_bundle: LoadedArtifactBundle,
) -> ScoringService | None:
    if not artifact_bundle.report.scoring_ready:
        return None
    if artifact_bundle.model is None or artifact_bundle.preprocessor is None:
        return None
    return ScoringService(artifact_bundle)


def _unavailable_artifact_bundle() -> LoadedArtifactBundle:
    """Keep v2 liveness/readiness available when legacy ML startup degrades."""

    report = ArtifactLoadReport(
        source="candidate",
        runtime_model_name=None,
        runtime_model_type=None,
        manifest_version=None,
        model_version=None,
        runtime_model_path=None,
        manifest_path=None,
        resolved_paths={},
        artifacts_present=(),
        artifacts_loaded=(),
        missing_artifacts=(),
        invalid_artifacts=(),
        artifact_errors={"startup": "legacy artifact initialization unavailable"},
        artifact_warnings={},
        scoring_ready=False,
    )
    return LoadedArtifactBundle(
        report=report,
        model=None,
        preprocessor=None,
        shap_explainer=None,
        dice_explainer=None,
        metrics_payload=None,
        baseline_metrics=None,
        fairness_report=None,
        psi_report=None,
        global_importance=None,
        population_percentiles=None,
        manifest=None,
    )


app = create_app()


__all__ = ["app", "create_app"]
