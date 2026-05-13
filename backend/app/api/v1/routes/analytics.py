"""Analytics route stubs for AlterScore backend."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from backend.app.schemas.analytics import (
    BaselineComparisonResponse,
    ModelStatsResponse,
    ScoreDistributionResponse,
)
from backend.app.schemas.common import ErrorResponse
from backend.app.services.analytics import (
    AnalyticsArtifactMissingError,
    AnalyticsPayloadError,
)


router = APIRouter(tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get(
    "/model-stats",
    response_model=ModelStatsResponse,
    responses={
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def get_model_stats(request: Request) -> ModelStatsResponse | JSONResponse:
    analytics_service = request.app.state.analytics_service

    try:
        return analytics_service.get_model_stats()
    except AnalyticsArtifactMissingError as exc:
        return _analytics_missing_response(
            code="ARTIFACTS_NOT_READY",
            message=(
                "Model stats are not ready yet. Generate and save metrics.json first."
            ),
            details={
                "missing_artifacts": [exc.artifact_key],
                "artifact_path": None if exc.artifact_path is None else str(exc.artifact_path),
            },
        )
    except AnalyticsPayloadError as exc:
        logger.exception("Invalid model stats payload.")
        return _analytics_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ANALYTICS_PAYLOAD_INVALID",
            message="Saved analytics payload is invalid for the requested endpoint.",
            details={"artifact": exc.artifact_key},
        )


@router.get(
    "/baseline-comparison",
    response_model=BaselineComparisonResponse,
    responses={
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def get_baseline_comparison(request: Request) -> BaselineComparisonResponse | JSONResponse:
    analytics_service = request.app.state.analytics_service

    try:
        return analytics_service.get_baseline_comparison()
    except AnalyticsArtifactMissingError as exc:
        return _analytics_missing_response(
            code="ARTIFACTS_NOT_READY",
            message=(
                "Baseline comparison is not ready yet. Generate and save "
                "baseline_metrics.json first."
            ),
            details={
                "missing_artifacts": [exc.artifact_key],
                "artifact_path": None if exc.artifact_path is None else str(exc.artifact_path),
            },
        )
    except AnalyticsPayloadError as exc:
        logger.exception("Invalid baseline comparison payload.")
        return _analytics_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ANALYTICS_PAYLOAD_INVALID",
            message="Saved analytics payload is invalid for the requested endpoint.",
            details={"artifact": exc.artifact_key},
        )


@router.get(
    "/score-distribution",
    response_model=ScoreDistributionResponse,
    responses={
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def get_score_distribution(request: Request) -> ScoreDistributionResponse | JSONResponse:
    analytics_service = request.app.state.analytics_service

    try:
        return analytics_service.get_score_distribution()
    except AnalyticsArtifactMissingError as exc:
        return _analytics_missing_response(
            code="ARTIFACTS_NOT_READY",
            message=(
                "Score distribution is not ready yet. Generate and save "
                "population_percentiles.json first."
            ),
            details={
                "missing_artifacts": [exc.artifact_key],
                "artifact_path": None if exc.artifact_path is None else str(exc.artifact_path),
            },
        )
    except AnalyticsPayloadError as exc:
        logger.exception("Invalid score distribution payload.")
        return _analytics_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="ANALYTICS_PAYLOAD_INVALID",
            message="Saved analytics payload is invalid for the requested endpoint.",
            details={"artifact": exc.artifact_key},
        )


def _analytics_missing_response(
    *,
    code: str,
    message: str,
    details: dict[str, Any],
) -> JSONResponse:
    return _analytics_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code=code,
        message=message,
        details=details,
    )


def _analytics_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = ErrorResponse.model_validate(
        {
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc),
            }
        }
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


__all__ = ["router"]
