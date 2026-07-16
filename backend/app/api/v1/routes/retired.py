"""Explicit 410 responses for the retired model-backed scorer."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["retired"])


@router.get("/health", include_in_schema=False)
def compatibility_health() -> JSONResponse:
    """Keep existing process probes alive without loading research artifacts."""

    return JSONResponse(
        content={
            "status": "ok",
            "service": "public-v2",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    )


def _retired_response() -> JSONResponse:
    return JSONResponse(
        status_code=410,
        headers={"Cache-Control": "no-store"},
        content={
            "error": {
                "code": "legacy_route_retired",
                "message": "The legacy model-backed scoring route has been retired.",
                "details": {},
            }
        },
    )


@router.post("/score", include_in_schema=False)
def retired_score() -> JSONResponse:
    """Reject the former public scorer without invoking research code."""

    return _retired_response()


@router.post("/debug-score", include_in_schema=False)
def retired_debug_score() -> JSONResponse:
    """Reject the former local debug scorer without invoking research code."""

    return _retired_response()


__all__ = ["router"]
