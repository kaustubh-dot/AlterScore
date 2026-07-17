"""FastAPI routes for the secure anonymous Phase 4 contract."""

from __future__ import annotations

from datetime import datetime, timezone
from ipaddress import ip_address

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.app.api.v2.models import (
    ASSESSMENT_VERSION,
    CONTRACT_VERSION,
    ErrorResponse,
    FormResponse,
    LiveResponse,
    ReadyResponse,
    ReadyCheck,
    SCORING_POLICY_VERSION,
    ScoreResponse,
    VerificationResponse,
)
from backend.app.api.v2.security import (
    V2DomainError,
    extract_bearer_token,
    format_timestamp,
    new_opaque_id,
    parse_json_object_without_duplicates,
    public_error_message,
)
from backend.app.api.v2.service import AnonymousAssessmentService


router = APIRouter(tags=["assessment-v2"])
MAX_SCORE_BODY_BYTES = 256 * 1024


def _request_id() -> str:
    return new_opaque_id("req")


def _service(request: Request) -> AnonymousAssessmentService:
    service = getattr(request.app.state, "anonymous_assessment_service", None)
    if not isinstance(service, AnonymousAssessmentService):
        raise V2DomainError("not_ready", 503, {"failed_checks": ["scorer"]})
    return service


_LOCAL_ENVIRONMENTS = frozenset({"local", "test", "development"})


def _is_loopback_host(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.casefold() == "localhost":
        return True
    try:
        return ip_address(value).is_loopback
    except ValueError:
        return False


def _require_secure_transport(
    request: Request, service: AnonymousAssessmentService
) -> None:
    """Keep issued and submitted bearer tokens off plaintext connections.

    The ASGI server or an explicitly configured, trusted TLS proxy must set
    the request scheme to ``https``.  We intentionally do not trust a
    client-supplied forwarded header here.
    """

    if request.url.scheme.lower() == "https":
        return

    # Hugging Face terminates TLS in a local sidecar before forwarding to
    # Uvicorn. Trust its forwarded scheme only when the immediate peer is
    # loopback; arbitrary remote clients cannot make plaintext requests look
    # secure by supplying this header.
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",", 1)[0]
    peer_host = getattr(request.state, "phase4_network_host", None)
    if forwarded_proto.strip().lower() == "https" and _is_loopback_host(peer_host):
        return

    # Ordinary local development runs Vite and Uvicorn on the loopback
    # interface. Permit that narrow non-production case so the documented
    # startup commands form a usable end-to-end environment. Remote and every
    # production-like plaintext request still fail closed.
    network_host = getattr(request.state, "phase4_network_host", None)
    if service.environment in _LOCAL_ENVIRONMENTS and _is_loopback_host(network_host):
        return
    raise V2DomainError("malformed_request", 400, {"fields": ["transport"]})


def _error_response(
    error: V2DomainError, request_id: str | None = None
) -> JSONResponse:
    response = ErrorResponse(
        contract_version=CONTRACT_VERSION,
        assessment_version=ASSESSMENT_VERSION,
        scoring_policy_version=SCORING_POLICY_VERSION,
        error={
            "code": error.code,
            "message": public_error_message(error.code),
            "details": error.details,
            "request_id": request_id or _request_id(),
            "timestamp": format_timestamp(datetime.now(timezone.utc)),
        },
    )
    return JSONResponse(
        status_code=error.status_code, content=response.model_dump(mode="json")
    )


def _validation_fields(error: ValidationError) -> list[str]:
    """Reduce Pydantic locations to allow-listed top-level field names."""

    allowed = {
        "contract_version",
        "assessment_version",
        "scoring_policy_version",
        "responses",
        "behavior_profile",
        "narrative",
        "body",
    }
    fields: set[str] = set()
    for item in error.errors(include_url=False):
        location = item.get("loc", ())
        first = location[0] if location else "body"
        fields.add(first if first in allowed else "body")
    return sorted(fields or {"body"})


def _rate_limit_response(
    service: AnonymousAssessmentService, bucket: str, request: Request
) -> JSONResponse | None:
    host = getattr(request.state, "phase4_network_host", None)
    if not isinstance(host, str):
        host = request.client.host if request.client is not None else None
    retry_after = service.rate_limit(bucket, host)
    if retry_after is None:
        return None
    return _error_response(
        V2DomainError("rate_limited", 429, {"retry_after_seconds": retry_after})
    )


async def _read_score_body(request: Request) -> bytes:
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > MAX_SCORE_BODY_BYTES:
            raise V2DomainError("malformed_request", 400, {"fields": ["body"]})
        chunks.append(chunk)
    return b"".join(chunks)


@router.get("/v2/assessment/form", response_model=FormResponse)
def get_form(request: Request) -> JSONResponse:
    request_id = _request_id()
    try:
        service = _service(request)
        _require_secure_transport(request, service)
        limited = _rate_limit_response(service, "form", request)
        if limited is not None:
            return limited
        response = service.issue_form(request_id)
        return JSONResponse(content=response.model_dump(mode="json"))
    except V2DomainError as error:
        return _error_response(error, request_id)
    except Exception:
        return _error_response(V2DomainError("internal_error", 500, {}), request_id)


@router.post("/v2/assessment/score", response_model=ScoreResponse)
async def post_score(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    request_id = _request_id()
    try:
        service = _service(request)
        _require_secure_transport(request, service)
        limited = _rate_limit_response(service, "score", request)
        if limited is not None:
            return limited
        token = extract_bearer_token(authorization)
        body = await _read_score_body(request)
        try:
            payload = parse_json_object_without_duplicates(body)
        except ValueError:
            raise V2DomainError("malformed_request", 400, {"fields": ["body"]})
        try:
            from backend.app.api.v2.models import ScoreSubmission

            submission = ScoreSubmission.model_validate(payload)
        except ValidationError as error:
            raise V2DomainError(
                "invalid_response", 422, {"fields": _validation_fields(error)}
            )
        response = service.submit(token, submission, request_id)
        return JSONResponse(content=response.model_dump(mode="json"))
    except V2DomainError as error:
        return _error_response(error, request_id)
    except Exception:
        return _error_response(V2DomainError("internal_error", 500, {}), request_id)


@router.get("/v2/results/verify/{result_id}", response_model=VerificationResponse)
def verify_result(request: Request, result_id: str) -> JSONResponse:
    request_id = _request_id()
    try:
        service = _service(request)
        _require_secure_transport(request, service)
        limited = _rate_limit_response(service, "verification", request)
        if limited is not None:
            return limited
        response = service.verify(result_id, request_id)
        return JSONResponse(content=response.model_dump(mode="json"))
    except V2DomainError as error:
        return _error_response(error, request_id)
    except Exception:
        return _error_response(V2DomainError("internal_error", 500, {}), request_id)


@router.get("/live", response_model=LiveResponse)
def live(request: Request) -> JSONResponse:
    request_id = _request_id()
    try:
        settings = getattr(request.app.state, "settings", None)
        response = LiveResponse(
            contract_version=CONTRACT_VERSION,
            assessment_version=ASSESSMENT_VERSION,
            scoring_policy_version=SCORING_POLICY_VERSION,
            request_id=request_id,
            release_sha=getattr(settings, "release_sha", "local"),
            status="ok",
            timestamp=format_timestamp(datetime.now(timezone.utc)),
        )
        return JSONResponse(content=response.model_dump(mode="json"))
    except V2DomainError as error:
        return _error_response(error, request_id)
    except Exception:
        return _error_response(V2DomainError("internal_error", 500, {}), request_id)


@router.get("/ready", response_model=ReadyResponse)
def ready(request: Request) -> JSONResponse:
    request_id = _request_id()
    try:
        service = getattr(request.app.state, "anonymous_assessment_service", None)
        if isinstance(service, AnonymousAssessmentService):
            response = service.readiness(request_id)
        else:
            settings = getattr(request.app.state, "settings", None)
            response = ReadyResponse(
                contract_version=CONTRACT_VERSION,
                assessment_version=ASSESSMENT_VERSION,
                scoring_policy_version=SCORING_POLICY_VERSION,
                request_id=request_id,
                release_sha=getattr(settings, "release_sha", "local"),
                status="not_ready",
                timestamp=format_timestamp(datetime.now(timezone.utc)),
                checks=[
                    ReadyCheck(
                        name="instrument",
                        status="fail",
                        message="canonical instrument unavailable",
                    ),
                    ReadyCheck(
                        name="scorer",
                        status="fail",
                        message="deterministic scorer unavailable",
                    ),
                    ReadyCheck(
                        name="signing",
                        status="fail",
                        message="result signing configuration missing",
                    ),
                    ReadyCheck(
                        name="attempt_store",
                        status="fail",
                        message="in-memory attempt store unavailable",
                    ),
                    ReadyCheck(
                        name="verification_store",
                        status="fail",
                        message="in-memory verification store unavailable",
                    ),
                    ReadyCheck(
                        name="rate_limits",
                        status="fail",
                        message="network rate limits unavailable",
                    ),
                ],
            )
        status_code = 200 if response.status != "not_ready" else 503
        return JSONResponse(
            status_code=status_code, content=response.model_dump(mode="json")
        )
    except V2DomainError as error:
        return _error_response(error, request_id)
    except Exception:
        return _error_response(V2DomainError("internal_error", 500, {}), request_id)


__all__ = ["router"]
