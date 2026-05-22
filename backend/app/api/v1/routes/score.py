"""Score routes for AlterScore backend."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from time import perf_counter
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from backend.app.schemas.common import ErrorResponse
from backend.app.schemas.score import ScoreRequest, ScoreResponse


router = APIRouter(tags=["score"])
logger = logging.getLogger(__name__)


@router.post(
    "/score",
    response_model=ScoreResponse,
    responses={
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def score_request(request: Request, payload: ScoreRequest) -> ScoreResponse | JSONResponse:
    scoring_service = request.app.state.scoring_service
    request_logging_service = request.app.state.request_logging_service
    request_id = payload.session_id
    started_at = perf_counter()

    if scoring_service is None:
        response = _error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="ARTIFACTS_NOT_READY",
            message=(
                "Scoring artifacts are not ready yet. "
                "Load a runtime model and preprocessor bundle first."
            ),
            request_id=request_id,
            details={
                "missing_artifacts": list(request.app.state.artifact_bundle.report.missing_artifacts),
                "invalid_artifacts": list(request.app.state.artifact_bundle.report.invalid_artifacts),
                "artifact_errors": dict(
                    request.app.state.artifact_bundle.report.artifact_errors
                ),
            },
        )
        _log_failure(
            request_logging_service=request_logging_service,
            request_id=request_id,
            session_id=payload.session_id,
            status_code=response.status_code,
            error_code="ARTIFACTS_NOT_READY",
            error_message="Scoring artifacts are not ready.",
            details=response.body,
            started_at=started_at,
        )
        return response

    try:
        response = scoring_service.score_request(payload)
        _log_success(
            request_logging_service=request_logging_service,
            request_id=request_id,
            session_id=response.session_id,
            response=response,
            started_at=started_at,
        )
        return response
    except Exception as exc:
        logger.exception("Scoring failed for request %s.", request_id)
        response = _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="SCORING_FAILED",
            message="Scoring failed for the supplied request.",
            request_id=request_id,
            details={"error_type": type(exc).__name__},
        )
        _log_failure(
            request_logging_service=request_logging_service,
            request_id=request_id,
            session_id=payload.session_id,
            status_code=response.status_code,
            error_code="SCORING_FAILED",
            error_message=str(exc),
            details={"error_type": type(exc).__name__},
            started_at=started_at,
        )
        return response


@router.post(
    "/debug-score",
    response_model=None,
    responses={
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def debug_score_request(request: Request, payload: ScoreRequest) -> dict[str, Any] | JSONResponse:
    settings = request.app.state.settings
    if settings.environment != "local":
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="DEBUG_NOT_AVAILABLE",
            message="Debug scoring is only available in the local development environment.",
            request_id=f"{payload.session_id}:debug",
        )

    scoring_service = request.app.state.scoring_service
    request_id = f"{payload.session_id}:debug"

    if scoring_service is None:
        return _error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="ARTIFACTS_NOT_READY",
            message=(
                "Scoring artifacts are not ready yet. "
                "Load a runtime model and preprocessor bundle first."
            ),
            request_id=request_id,
            details={
                "missing_artifacts": list(request.app.state.artifact_bundle.report.missing_artifacts),
                "invalid_artifacts": list(request.app.state.artifact_bundle.report.invalid_artifacts),
                "artifact_errors": dict(
                    request.app.state.artifact_bundle.report.artifact_errors
                ),
            },
        )

    try:
        return scoring_service.score_request_debug(payload)
    except Exception as exc:
        logger.exception("Debug scoring failed for request %s.", request_id)
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="SCORING_DEBUG_FAILED",
            message="Debug scoring failed for the supplied request.",
            request_id=request_id,
            details={"error_type": type(exc).__name__},
        )



def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = ErrorResponse.model_validate(
        {
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc),
            }
        }
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def _log_success(
    *,
    request_logging_service: Any,
    request_id: str,
    session_id: str,
    response: ScoreResponse,
    started_at: float,
) -> None:
    if request_logging_service is None:
        return

    try:
        request_logging_service.log_score_success(
            request_id=request_id,
            session_id=session_id,
            latency_ms=(perf_counter() - started_at) * 1000.0,
            response=response,
        )
    except Exception:
        logger.exception("Failed to append success request log for %s.", request_id)


def _log_failure(
    *,
    request_logging_service: Any,
    request_id: str,
    session_id: str,
    status_code: int,
    error_code: str,
    error_message: str,
    details: Any,
    started_at: float,
) -> None:
    if request_logging_service is None:
        return

    try:
        parsed_details = details
        if isinstance(details, bytes):
            parsed_details = ErrorResponse.model_validate_json(details).error.details
        request_logging_service.log_score_failure(
            request_id=request_id,
            session_id=session_id,
            latency_ms=(perf_counter() - started_at) * 1000.0,
            status_code=status_code,
            error_code=error_code,
            error_message=error_message,
            details=parsed_details if isinstance(parsed_details, dict) else None,
        )
    except Exception:
        logger.exception("Failed to append failure request log for %s.", request_id)


__all__ = ["router"]
