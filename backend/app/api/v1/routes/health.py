"""Health route stubs for AlterScore backend."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from backend.app.schemas.analytics import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    artifact_bundle = request.app.state.artifact_bundle
    report = artifact_bundle.report

    if report.scoring_ready and not report.missing_artifacts and not report.invalid_artifacts:
        status = "ok"
    elif report.scoring_ready:
        status = "degraded"
    else:
        status = "error"

    return HealthResponse(
        status=status,
        version=settings.api_version,
        model_loaded=artifact_bundle.model is not None,
        artifact_source=report.source,
        manifest_backed=report.source == "manifest",
        manifest_version=report.manifest_version,
        model_version=report.model_version,
        artifacts_loaded=list(report.artifacts_loaded),
        missing_artifacts=list(report.missing_artifacts),
        invalid_artifacts=list(report.invalid_artifacts),
        timestamp=datetime.now(timezone.utc),
    )


__all__ = ["router"]
