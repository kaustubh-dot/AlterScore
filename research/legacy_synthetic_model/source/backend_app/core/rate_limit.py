"""Shared rate limiter configuration for AlterScore backend routes.

A single module-level :class:`Limiter` instance is shared between the app
factory (which toggles it per environment) and the route modules. Rather than
stacking slowapi's decorator on the route — which interferes with FastAPI's
request-body parsing under ``from __future__ import annotations`` — the limit is
enforced explicitly via :func:`enforce_score_rate_limit`, which returns a ready
429 response when the caller has exceeded the configured budget.

The limiter is disabled by default so any app that does not explicitly configure
it (tests, scripts) stays unthrottled.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.app.core.settings import Settings
from backend.app.schemas.common import ErrorResponse

# Mutable holder so the limit string can be driven by per-app settings without
# rebuilding any decorators. slowapi calls a no-argument callable to resolve the
# active limit on each request.
_RATE_LIMIT_CONFIG = {"score": "30/minute"}

limiter = Limiter(key_func=get_remote_address, enabled=False)


def score_rate_limit_value() -> str:
    """Return the currently configured rate limit for the scoring endpoint."""
    return _RATE_LIMIT_CONFIG["score"]


def configure_rate_limiting(settings: Settings) -> None:
    """Apply environment-driven rate limiting settings to the shared limiter."""
    limiter.enabled = settings.rate_limit_enabled
    _RATE_LIMIT_CONFIG["score"] = settings.score_rate_limit


def _score_limit_target(*, request: Request) -> None:
    """Endpoint stand-in so slowapi can attribute the limit to a stable name."""
    return None


# Decorate the stand-in once; slowapi keys the limit by the function's qualified
# name, so re-decorating per request would stack duplicate limits.
_checked_score_limit = limiter.limit(score_rate_limit_value)(_score_limit_target)


def enforce_score_rate_limit(request: Request) -> JSONResponse | None:
    """Check the scoring rate limit for ``request``.

    Returns a 429 :class:`JSONResponse` when the limit is exceeded, or ``None``
    when the request is within budget (or rate limiting is disabled).
    """
    if not limiter.enabled:
        return None

    try:
        _checked_score_limit(request=request)
    except RateLimitExceeded as exc:
        return _rate_limited_response(exc)
    return None


def _rate_limited_response(exc: RateLimitExceeded) -> JSONResponse:
    """Render slowapi rate-limit rejections in the standard error envelope."""
    limit_text = str(getattr(exc, "detail", "")) or "rate limit exceeded"
    payload = ErrorResponse.model_validate(
        {
            "error": {
                "code": "RATE_LIMITED",
                "message": "Too many requests. Please slow down and try again shortly.",
                "details": {"limit": limit_text},
                "request_id": str(uuid4()),
                "timestamp": datetime.now(timezone.utc),
            }
        }
    )
    return JSONResponse(status_code=429, content=payload.model_dump(mode="json"))


__all__ = [
    "configure_rate_limiting",
    "enforce_score_rate_limit",
    "limiter",
    "score_rate_limit_value",
]
