"""Strict public transport models for the Phase 4 anonymous API.

The Phase 3 models remain an internal scoring boundary.  These models are the
smaller public allowlist: they deliberately contain opaque identifiers and
never contain answer keys, rubrics, generation metadata, or signing material.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal, TypeAlias, Union

from pydantic import Field, StrictInt, StrictStr, field_validator, model_validator

from backend.app.instrument import (
    ASSESSMENT_VERSION,
    CONTRACT_VERSION,
    SCORING_POLICY_VERSION,
)
from backend.app.schemas.common import SchemaModel
from backend.app.unified_scoring import Decimal2, Explanation

Timestamp: TypeAlias = Annotated[StrictStr, Field(min_length=20, max_length=20)]
NonEmptyString: TypeAlias = Annotated[StrictStr, Field(min_length=1)]
RequestId: TypeAlias = Annotated[
    StrictStr, Field(pattern=r"^req_[A-Za-z0-9_-]{32,}$")
]
AttemptId: TypeAlias = Annotated[
    StrictStr, Field(pattern=r"^attempt_[A-Za-z0-9_-]{32,}$")
]
ResultId: TypeAlias = Annotated[
    StrictStr, Field(pattern=r"^result_[A-Za-z0-9_-]{32,}$")
]
ItemId: TypeAlias = Annotated[
    StrictStr, Field(pattern=r"^item_[A-Za-z0-9_-]{32,}$")
]
BehaviorId: TypeAlias = Annotated[
    StrictStr, Field(pattern=r"^behavior_[A-Za-z0-9_-]{32,}$")
]
ScenarioId: TypeAlias = Annotated[
    StrictStr, Field(pattern=r"^scenario_[A-Za-z0-9_-]{32,}$")
]
OptionId: TypeAlias = Annotated[
    StrictStr,
    Field(pattern=r"^(?:option|behavior_option)_[A-Za-z0-9_-]{32,}$"),
]
AttemptToken: TypeAlias = Annotated[
    StrictStr,
    Field(
        min_length=80,
        max_length=500,
        pattern=r"^at1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{43}$",
    ),
]
BehaviorValue: TypeAlias = Literal[
    "Never",
    "Rarely",
    "Sometimes",
    "Often",
    "Always",
    "Not applicable",
]


def _validate_utc_timestamp(value: str) -> str:
    """Require second-precision UTC timestamps with the frozen ``Z`` form."""

    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamps must be UTC strings ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("timestamps must be ISO-8601 UTC strings") from exc
    if parsed.tzinfo != timezone.utc or parsed.microsecond:
        raise ValueError("timestamps must use UTC and second precision")
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ValueError("timestamps must use the canonical UTC representation")
    return value


class V2Model(SchemaModel):
    """Phase 4 models reject undocumented transport fields."""


def _require_true(value: object) -> bool:
    if value is not True:
        raise ValueError("required must be true")
    return True


class V2OptionPresentation(V2Model):
    option_id: OptionId
    label: NonEmptyString


class V2ObjectivePresentation(V2Model):
    presentation_id: ItemId
    item_type: Literal["objective"]
    prompt: NonEmptyString
    response_kind: Literal["integer"]
    required: Literal[True]

    _required_is_true = field_validator("required", mode="before")(_require_true)


class V2StaticSjtPresentation(V2Model):
    presentation_id: ItemId
    item_type: Literal["static_sjt"]
    prompt: NonEmptyString
    response_kind: Literal["single_choice"]
    required: Literal[True]
    options: list[V2OptionPresentation] = Field(..., min_length=4, max_length=4)

    _required_is_true = field_validator("required", mode="before")(_require_true)


class V2BranchingPresentation(V2Model):
    presentation_id: ItemId
    item_type: Literal["branching"]
    scenario_presentation_id: ScenarioId
    stage_index: StrictInt = Field(..., ge=1, le=3)
    prompt: NonEmptyString
    response_kind: Literal["single_choice"]
    required: Literal[True]
    options: list[V2OptionPresentation] = Field(..., min_length=3, max_length=3)

    _required_is_true = field_validator("required", mode="before")(_require_true)


class V2BehaviorProfilePresentation(V2Model):
    presentation_id: BehaviorId
    item_type: Literal["behavior_profile"]
    prompt: NonEmptyString
    response_kind: Literal["single_choice"]
    required: Literal[True]
    options: list[V2OptionPresentation] = Field(..., min_length=6, max_length=6)

    _required_is_true = field_validator("required", mode="before")(_require_true)


class V2NarrativeConfig(V2Model):
    enabled: bool
    prompt: NonEmptyString
    max_length: StrictInt

    @field_validator("enabled", mode="before")
    @classmethod
    def _strict_enabled(cls, value: object) -> bool:
        if not isinstance(value, bool):
            raise ValueError("enabled must be a boolean")
        return value

    @field_validator("max_length", mode="before")
    @classmethod
    def _frozen_max_length(cls, value: object) -> int:
        if value != 1000 or isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("max_length must be 1000")
        return value


FormItem: TypeAlias = Annotated[
    Union[V2ObjectivePresentation, V2StaticSjtPresentation, V2BranchingPresentation],
    Field(discriminator="item_type"),
]


class PublicMetadata(V2Model):
    """Version and request metadata safe for public responses."""

    contract_version: Literal[CONTRACT_VERSION]
    assessment_version: Literal[ASSESSMENT_VERSION]
    scoring_policy_version: Literal[SCORING_POLICY_VERSION]
    request_id: RequestId
    release_sha: StrictStr = Field(..., min_length=1, max_length=200)


class FormResponse(PublicMetadata):
    """One issued, single-use anonymous assessment form."""

    attempt_id: AttemptId
    attempt_token: AttemptToken
    issued_at: Timestamp
    expires_at: Timestamp
    integrity_status: Literal["issued"]
    items: list[FormItem] = Field(..., min_length=18, max_length=18)
    behavior_profile_items: list[V2BehaviorProfilePresentation] = Field(
        ..., min_length=6, max_length=6
    )
    narrative: V2NarrativeConfig

    _timestamps = field_validator("issued_at", "expires_at")(_validate_utc_timestamp)

    @model_validator(mode="after")
    def _shape_and_lifecycle(self) -> "FormResponse":
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be later than issued_at")
        item_ids = [item.presentation_id for item in self.items]
        if len(set(item_ids)) != len(item_ids):
            raise ValueError("scored presentation IDs must be unique")
        behavior_ids = [item.presentation_id for item in self.behavior_profile_items]
        if len(set(behavior_ids)) != len(behavior_ids):
            raise ValueError("behavior presentation IDs must be unique")
        if set(item_ids) & set(behavior_ids):
            raise ValueError("scored and behavior presentation IDs must be disjoint")
        counts = {
            "objective": sum(item.item_type == "objective" for item in self.items),
            "static_sjt": sum(item.item_type == "static_sjt" for item in self.items),
            "branching": sum(item.item_type == "branching" for item in self.items),
        }
        if counts != {"objective": 8, "static_sjt": 4, "branching": 6}:
            raise ValueError("form must contain the frozen scored item counts")
        return self


class ScoreSubmission(V2Model):
    """The only JSON fields accepted by the scoring endpoint."""

    contract_version: StrictStr
    assessment_version: StrictStr
    scoring_policy_version: StrictStr
    responses: dict[StrictStr, StrictInt | StrictStr] = Field(
        ..., min_length=18, max_length=18
    )
    behavior_profile: dict[StrictStr, StrictStr] = Field(
        ..., min_length=6, max_length=6
    )
    narrative: StrictStr | None = Field(default=None, max_length=1000)


class BehaviorProfileResponse(V2Model):
    presentation_id: BehaviorId
    selected_value: BehaviorValue


_HMAC_SIGNATURE_PATTERN = r"^hmac-sha256-v1:[A-Za-z0-9_-]{43}$"
_DIGEST_PATTERN = r"^sha256:[0-9a-f]{64}$"


class ScoreResponse(PublicMetadata):
    """Detailed score returned once, including the unsigned explanation."""

    result_id: ResultId
    attempt_id: AttemptId
    issued_at: Timestamp
    expires_at: Timestamp
    integrity_status: Literal["verified_attempt"]
    financial_decision_index: StrictInt = Field(..., ge=0, le=100)
    legacy_demo_score: StrictInt = Field(..., ge=300, le=850)
    objective_score: Decimal2
    judgment_score: Decimal2
    behavior_profile: list[BehaviorProfileResponse] = Field(
        ..., min_length=6, max_length=6
    )
    limitations: list[NonEmptyString] = Field(..., min_length=1)
    result_signature: StrictStr = Field(..., pattern=_HMAC_SIGNATURE_PATTERN)
    explanation_digest: StrictStr = Field(..., pattern=_DIGEST_PATTERN)
    explanation: Explanation

    _timestamps = field_validator("issued_at", "expires_at")(_validate_utc_timestamp)

    @model_validator(mode="after")
    def _result_lifecycle(self) -> "ScoreResponse":
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be later than issued_at")
        if len({item.presentation_id for item in self.behavior_profile}) != 6:
            raise ValueError("behavior presentation IDs must be unique")
        if len(set(self.limitations)) != len(self.limitations):
            raise ValueError("limitations must be unique")
        return self


class VerificationResponse(PublicMetadata):
    """The signed, redacted projection retained by the verification store.

    ``objective_score`` and ``judgment_score`` are integer hundredths here.
    This is the representation used by the signing projection, so equivalent
    decimal spellings cannot produce different signatures.
    """

    result_id: ResultId
    attempt_id: AttemptId
    issued_at: Timestamp
    expires_at: Timestamp
    integrity_status: Literal["verified_attempt"]
    financial_decision_index: StrictInt = Field(..., ge=0, le=100)
    legacy_demo_score: StrictInt = Field(..., ge=300, le=850)
    objective_score: StrictInt = Field(..., ge=0, le=10_000)
    judgment_score: StrictInt = Field(..., ge=0, le=10_000)
    limitations: list[NonEmptyString] = Field(..., min_length=1)
    explanation_digest: StrictStr = Field(..., pattern=_DIGEST_PATTERN)
    result_signature: StrictStr = Field(..., pattern=_HMAC_SIGNATURE_PATTERN)

    _timestamps = field_validator("issued_at", "expires_at")(_validate_utc_timestamp)

    @model_validator(mode="after")
    def _verification_lifecycle(self) -> "VerificationResponse":
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be later than issued_at")
        if len(set(self.limitations)) != len(self.limitations):
            raise ValueError("limitations must be unique")
        return self


class LiveResponse(PublicMetadata):
    status: Literal["ok"]
    timestamp: Timestamp

    _timestamp = field_validator("timestamp")(_validate_utc_timestamp)


ReadyCheckName: TypeAlias = Literal[
    "instrument",
    "scorer",
    "signing",
    "attempt_store",
    "verification_store",
    "rate_limits",
]
ReadyCheckStatus: TypeAlias = Literal["pass", "warn", "fail"]


class ReadyCheck(V2Model):
    name: ReadyCheckName
    status: ReadyCheckStatus
    message: Literal[
        "canonical instrument available",
        "canonical instrument unavailable",
        "deterministic scorer available",
        "deterministic scorer unavailable",
        "release metadata unavailable",
        "result signing configured",
        "result signing configuration missing",
        "in-memory attempt store available",
        "in-memory attempt store unavailable",
        "in-memory verification store available",
        "in-memory verification store unavailable",
        "network rate limits available",
        "network rate limits unavailable",
    ]


class ReadyResponse(PublicMetadata):
    status: Literal["ready", "degraded", "not_ready"]
    timestamp: Timestamp
    checks: list[ReadyCheck] = Field(..., min_length=6, max_length=6)

    _timestamp = field_validator("timestamp")(_validate_utc_timestamp)

    @model_validator(mode="after")
    def _check_order(self) -> "ReadyResponse":
        expected = (
            "instrument",
            "scorer",
            "signing",
            "attempt_store",
            "verification_store",
            "rate_limits",
        )
        if tuple(check.name for check in self.checks) != expected:
            raise ValueError("readiness checks must use the frozen order")
        return self


ErrorCode: TypeAlias = Literal[
    "malformed_request",
    "unsupported_version",
    "attempt_expired",
    "attempt_consumed",
    "attempt_stale",
    "unknown_option",
    "invalid_response",
    "form_unavailable",
    "result_not_found",
    "integrity_failed",
    "rate_limited",
    "not_ready",
    "internal_error",
]


class ErrorDetail(V2Model):
    code: ErrorCode
    message: StrictStr = Field(..., min_length=1, max_length=200)
    details: dict[str, object]
    request_id: RequestId
    timestamp: Timestamp

    _timestamp = field_validator("timestamp")(_validate_utc_timestamp)

    @model_validator(mode="after")
    def _allowlisted_error(self) -> "ErrorDetail":
        expected_messages = {
            "malformed_request": "The request could not be parsed.",
            "unsupported_version": "The requested contract version is not supported.",
            "attempt_expired": "The assessment attempt has expired.",
            "attempt_consumed": "The assessment attempt has already been used.",
            "attempt_stale": "The assessment attempt is no longer available.",
            "unknown_option": "The request contains an option that was not issued.",
            "invalid_response": "The submitted response shape is invalid.",
            "form_unavailable": "A new assessment form is temporarily unavailable.",
            "result_not_found": "The requested result is not available.",
            "integrity_failed": "The requested result failed integrity verification.",
            "rate_limited": "Too many requests were received.",
            "not_ready": "The scoring service is not ready.",
            "internal_error": "The request could not be completed.",
        }
        if self.message != expected_messages[self.code]:
            raise ValueError("error message is not allow-listed")
        if self.code in {"malformed_request", "invalid_response", "unknown_option"}:
            if set(self.details) != {"fields"} or not isinstance(
                self.details.get("fields"), list
            ) or not all(
                isinstance(field, str) and field for field in self.details["fields"]
            ):
                raise ValueError("error fields details are invalid")
        elif self.code == "unsupported_version":
            if self.details != {
                "supported_contract_version": CONTRACT_VERSION,
                "supported_assessment_version": ASSESSMENT_VERSION,
                "supported_scoring_policy_version": SCORING_POLICY_VERSION,
            }:
                raise ValueError("supported version details are invalid")
        elif self.code in {"attempt_expired", "attempt_consumed", "attempt_stale"}:
            if self.details != {"retryable": True, "new_form_required": True}:
                raise ValueError("attempt lifecycle details are invalid")
        elif self.code == "rate_limited":
            retry_after = self.details.get("retry_after_seconds")
            if set(self.details) != {"retry_after_seconds"} or isinstance(
                retry_after, bool
            ) or not isinstance(retry_after, int) or retry_after < 1:
                raise ValueError("rate limit details are invalid")
        elif self.code in {"not_ready", "form_unavailable"}:
            checks = self.details.get("failed_checks")
            if set(self.details) != {"failed_checks"} or not isinstance(
                checks, list
            ) or not all(isinstance(check, str) and check for check in checks):
                raise ValueError("readiness details are invalid")
        elif self.details:
            raise ValueError("empty error details are required")
        return self


class ErrorResponse(V2Model):
    contract_version: Literal[CONTRACT_VERSION]
    assessment_version: Literal[ASSESSMENT_VERSION]
    scoring_policy_version: Literal[SCORING_POLICY_VERSION]
    error: ErrorDetail


__all__ = [
    "ASSESSMENT_VERSION",
    "CONTRACT_VERSION",
    "ErrorCode",
    "ErrorDetail",
    "ErrorResponse",
    "FormItem",
    "FormResponse",
    "LiveResponse",
    "PublicMetadata",
    "ReadyCheck",
    "ReadyResponse",
    "SCORING_POLICY_VERSION",
    "ScoreResponse",
    "ScoreSubmission",
    "Timestamp",
    "VerificationResponse",
]
