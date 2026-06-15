"""Health routes for AlterScore backend."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request

from backend.app.schemas.analytics import HealthResponse
from backend.ml.registry.promotion_gates import (
    evaluate_promotion_gates,
    load_promotion_gate_policy,
)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    artifact_bundle = request.app.state.artifact_bundle
    report = artifact_bundle.report
    promotion_gate = None
    if artifact_bundle.manifest is not None:
        promotion_policy = load_promotion_gate_policy(repo_root=settings.repo_root)
        promotion_gate = evaluate_promotion_gates(
            manifest=artifact_bundle.manifest,
            metrics_payload=artifact_bundle.metrics_payload,
            fairness_report=artifact_bundle.fairness_report,
            psi_report=artifact_bundle.psi_report,
            population_percentiles=artifact_bundle.population_percentiles,
            policy=promotion_policy,
        )
    promotion_gate_failed = (
        isinstance(promotion_gate, dict) and promotion_gate.get("status") == "failed"
    )

    if (
        report.scoring_ready
        and not report.missing_artifacts
        and not report.invalid_artifacts
        and not report.artifact_warnings
        and not promotion_gate_failed
    ):
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
        artifact_warnings=dict(report.artifact_warnings),
        promotion_gate=promotion_gate,
        timestamp=datetime.now(timezone.utc),
    )


__all__ = ["router"]
