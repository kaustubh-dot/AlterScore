"""Score route stubs for AlterScore backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from backend.app.schemas.common import ErrorResponse
from backend.app.schemas.score import ScoreRequest, ScoreResponse


router = APIRouter(tags=["score"])


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
    request_id = payload.session_id or str(uuid4())

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
            },
        )

    try:
        return scoring_service.score_request(payload)
    except Exception as exc:
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="SCORING_FAILED",
            message="Scoring failed for the supplied request.",
            request_id=request_id,
            details={"error": str(exc)},
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


__all__ = ["router"]
