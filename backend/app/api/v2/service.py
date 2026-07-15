"""Phase 4 issue, translate, score, sign, and verify service."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
import base64
import secrets
from typing import Any

from backend.app.api.v2.models import (
    ASSESSMENT_VERSION,
    CONTRACT_VERSION,
    SCORING_POLICY_VERSION,
    FormResponse,
    ReadyCheck,
    ReadyResponse,
    ScoreResponse,
    ScoreSubmission,
    VerificationResponse,
)
from backend.app.api.v2.security import (
    AttemptRecord,
    AttemptStore,
    NetworkRateLimiter,
    V2DomainError,
    VerificationRecord,
    VerificationStore,
    constant_time_signature_matches,
    explanation_digest,
    fields_error,
    format_timestamp,
    new_opaque_id,
    issue_signed_attempt_token,
    sign_projection,
    token_digest,
    unsupported_version_error,
    utc_now,
    verify_signed_attempt_token,
)
from backend.app.instrument import (
    CanonicalInstrumentForm,
    InvalidResponse,
    UnknownCanonicalId,
    generate_form,
)
from backend.app.unified_scoring import (
    Explanation,
    UnifiedScoringError,
    build_unified_presentation,
    quantize_fraction_half_up,
    score_unified_assessment,
)


_EXPECTED_PROJECTION_KEYS = frozenset(
    {
        "contract_version",
        "assessment_version",
        "scoring_policy_version",
        "release_sha",
        "result_id",
        "attempt_id",
        "issued_at",
        "expires_at",
        "integrity_status",
        "financial_decision_index",
        "legacy_demo_score",
        "objective_score",
        "judgment_score",
        "limitations",
        "explanation_digest",
    }
)
ATTEMPT_TTL_SECONDS = 2700
ATTEMPT_STORE_MAX_ENTRIES = 10_000
RESULT_TTL_SECONDS = 86_400
RESULT_STORE_MAX_ENTRIES = 10_000
MIN_SIGNING_SECRET_BYTES = 32
MIN_SIGNING_SECRET_DISTINCT_BYTES = 16


class AnonymousAssessmentService:
    """The Phase 4 stateful boundary around the pure Phase 3 scorer."""

    def __init__(
        self,
        settings: Any | None = None,
        *,
        release_sha: str | None = None,
        signing_secret: str | None = None,
        attempt_ttl_seconds: int = 2700,
        attempt_store_max_entries: int = 10_000,
        result_ttl_seconds: int = 86_400,
        result_store_max_entries: int = 10_000,
        rate_limits_enabled: bool = True,
    ) -> None:
        if settings is not None:
            release_sha = getattr(settings, "release_sha", release_sha)
            signing_secret = getattr(settings, "signing_secret", signing_secret)
            # These are frozen public-contract values. Settings may expose the
            # names for deployment inventory, but cannot silently alter v2 TTLs.
            attempt_ttl_seconds = ATTEMPT_TTL_SECONDS
            attempt_store_max_entries = ATTEMPT_STORE_MAX_ENTRIES
            result_ttl_seconds = RESULT_TTL_SECONDS
            result_store_max_entries = RESULT_STORE_MAX_ENTRIES
        self.release_sha = release_sha or "local"
        self.signing_secret = signing_secret
        self.attempt_store = AttemptStore(
            ttl_seconds=attempt_ttl_seconds,
            max_entries=attempt_store_max_entries,
        )
        self.verification_store = VerificationStore(
            ttl_seconds=result_ttl_seconds,
            max_entries=result_store_max_entries,
        )
        # Phase 4's public contract applies these limits in every environment.
        # The legacy v1 limiter remains independently configured.
        self.rate_limiter = NetworkRateLimiter(enabled=rate_limits_enabled)

    def _metadata(self, request_id: str) -> dict[str, str]:
        return {
            "contract_version": CONTRACT_VERSION,
            "assessment_version": ASSESSMENT_VERSION,
            "scoring_policy_version": SCORING_POLICY_VERSION,
            "request_id": request_id,
            "release_sha": self.release_sha,
        }

    def _signing_ready(self) -> bool:
        """Accept only a sufficiently diverse base64url-encoded 256-bit key.

        A human-readable passphrase cannot safely serve as the result-signing
        key.  Deployment must supply a secret generated with
        ``secrets.token_urlsafe(32)`` (or an equivalent base64url encoding of
        at least 32 random bytes).  The diversity check deliberately rejects
        obvious placeholder values such as repeated characters or zero bytes;
        it is a fail-closed configuration guard, not a substitute for proper
        secret generation and management.
        """

        if not isinstance(self.signing_secret, str) or not self.signing_secret:
            return False
        if any(
            character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
            for character in self.signing_secret
        ):
            return False
        try:
            padded = self.signing_secret + "=" * (-len(self.signing_secret) % 4)
            key_material = base64.urlsafe_b64decode(padded.encode("ascii"))
        except (UnicodeEncodeError, ValueError):
            return False
        return (
            len(key_material) >= MIN_SIGNING_SECRET_BYTES
            and len(set(key_material)) >= MIN_SIGNING_SECRET_DISTINCT_BYTES
        )

    def rate_limit(self, bucket: str, client_host: str | None) -> int | None:
        return self.rate_limiter.check(bucket, client_host)

    def readiness_checks(self) -> list[ReadyCheck]:
        checks: list[ReadyCheck] = []
        try:
            form = generate_form(0)
            build_unified_presentation(form)
            instrument_status = ("pass", "canonical instrument available")
        except Exception:
            instrument_status = ("fail", "canonical instrument unavailable")
        checks.append(ReadyCheck(name="instrument", status=instrument_status[0], message=instrument_status[1]))

        scorer_status = (
            ("pass", "deterministic scorer available")
            if callable(score_unified_assessment)
            else ("fail", "deterministic scorer unavailable")
        )
        checks.append(ReadyCheck(name="scorer", status=scorer_status[0], message=scorer_status[1]))

        signing_status = (
            ("pass", "result signing configured")
            if self._signing_ready()
            else ("fail", "result signing configuration missing")
        )
        checks.append(ReadyCheck(name="signing", status=signing_status[0], message=signing_status[1]))

        attempt_status = (
            ("pass", "in-memory attempt store available")
            if self.attempt_store.healthy()
            else ("fail", "in-memory attempt store unavailable")
        )
        checks.append(ReadyCheck(name="attempt_store", status=attempt_status[0], message=attempt_status[1]))

        verification_status = (
            ("pass", "in-memory verification store available")
            if self.verification_store.healthy()
            else ("fail", "in-memory verification store unavailable")
        )
        checks.append(ReadyCheck(name="verification_store", status=verification_status[0], message=verification_status[1]))

        rate_status = (
            ("pass", "network rate limits available")
            if self.rate_limiter.healthy()
            else ("fail", "network rate limits unavailable")
        )
        checks.append(ReadyCheck(name="rate_limits", status=rate_status[0], message=rate_status[1]))
        return checks

    def readiness(self, request_id: str | None = None) -> ReadyResponse:
        checks = self.readiness_checks()
        if any(check.status == "fail" for check in checks):
            status = "not_ready"
        elif any(check.status == "warn" for check in checks):
            status = "degraded"
        else:
            status = "ready"
        return ReadyResponse(
            **self._metadata(request_id or new_opaque_id("req")),
            status=status,
            timestamp=format_timestamp(utc_now()),
            checks=checks,
        )

    def live(self, request_id: str | None = None) -> dict[str, Any]:
        return {
            **self._metadata(request_id or new_opaque_id("req")),
            "status": "ok",
            "timestamp": format_timestamp(utc_now()),
        }

    def issue_form(self, request_id: str | None = None) -> FormResponse:
        if not self._signing_ready():
            raise V2DomainError("form_unavailable", 503, {"failed_checks": ["signing"]})
        issued_at = utc_now()
        seed = secrets.randbits(64)
        try:
            form = generate_form(seed)
            presentation = build_unified_presentation(form)
            attempt_id = new_opaque_id("attempt")
            expires_at = issued_at + timedelta(seconds=self.attempt_store.ttl_seconds)
            token = issue_signed_attempt_token(
                attempt_id, issued_at, expires_at, self.signing_secret
            )
            record = self._build_attempt_record(
                form, presentation, attempt_id, token, issued_at, expires_at
            )
            self.attempt_store.put(record)
        except (InvalidResponse, UnknownCanonicalId, UnifiedScoringError, ValueError):
            raise V2DomainError("form_unavailable", 503, {"failed_checks": ["instrument"]})
        except Exception:
            raise V2DomainError("form_unavailable", 503, {"failed_checks": ["instrument"]})

        return FormResponse(
            **self._metadata(request_id or new_opaque_id("req")),
            attempt_id=record.attempt_id,
            attempt_token=token,
            issued_at=format_timestamp(record.issued_at),
            expires_at=format_timestamp(record.expires_at),
            integrity_status="issued",
            items=record.public_items,
            behavior_profile_items=record.public_behavior_items,
            narrative=presentation.narrative.model_dump(mode="json"),
        )

    def submit(
        self,
        token: str,
        submission: ScoreSubmission,
        request_id: str | None = None,
    ) -> ScoreResponse:
        self._check_versions(submission)
        if not self._signing_ready():
            raise V2DomainError("not_ready", 503, {"failed_checks": ["signing"]})

        token_claim = verify_signed_attempt_token(token, self.signing_secret)
        if token_claim is None:
            raise V2DomainError(
                "attempt_stale", 409, {"retryable": True, "new_form_required": True}
            )
        claimed_attempt_id, claimed_expires_at = token_claim
        if claimed_expires_at <= utc_now():
            raise V2DomainError(
                "attempt_expired", 409, {"retryable": True, "new_form_required": True}
            )

        record = self.attempt_store.get(token_digest(token))
        if record.attempt_id != claimed_attempt_id:
            raise V2DomainError(
                "attempt_stale", 409, {"retryable": True, "new_form_required": True}
            )
        internal_responses, internal_behavior = self._translate_submission(
            record, submission
        )
        try:
            scored = score_unified_assessment(
                record.form,
                internal_responses,
                internal_behavior,
                submission.narrative,
            )
        except (InvalidResponse, UnknownCanonicalId, UnifiedScoringError, ValueError):
            raise fields_error("invalid_response", ["responses", "behavior_profile"])

        # The lock-protected consume is intentionally after complete validation
        # and pure scoring. Exactly one concurrent valid submission can pass it.
        record = self.attempt_store.consume(token_digest(token), record.attempt_id)
        result_id = new_opaque_id("result")
        result_issued_at = utc_now()
        if result_issued_at <= record.issued_at:
            result_issued_at = record.issued_at + timedelta(seconds=1)
        result_expires_at = result_issued_at + timedelta(
            seconds=self.verification_store.ttl_seconds
        )

        explanation_payload = self._public_explanation(
            scored.explanation.model_dump(mode="json"), record
        )
        explanation = Explanation.model_validate(explanation_payload)
        explanation_payload = explanation.model_dump(mode="json")
        digest = explanation_digest(explanation_payload)
        objective_display = quantize_fraction_half_up(scored.objective_score, 2)
        judgment_display = quantize_fraction_half_up(scored.judgment_score, 2)
        projection = {
            "contract_version": CONTRACT_VERSION,
            "assessment_version": ASSESSMENT_VERSION,
            "scoring_policy_version": SCORING_POLICY_VERSION,
            "release_sha": self.release_sha,
            "result_id": result_id,
            "attempt_id": record.attempt_id,
            "issued_at": format_timestamp(result_issued_at),
            "expires_at": format_timestamp(result_expires_at),
            "integrity_status": "verified_attempt",
            "financial_decision_index": scored.financial_decision_index,
            "legacy_demo_score": scored.legacy_demo_score,
            "objective_score": int(objective_display * Decimal(100)),
            "judgment_score": int(judgment_display * Decimal(100)),
            "limitations": list(scored.limitations),
            "explanation_digest": digest,
        }
        signature = sign_projection(projection, self.signing_secret)
        self.verification_store.put(
            VerificationRecord(
                result_id=result_id,
                issued_at=result_issued_at,
                expires_at=result_expires_at,
                projection=projection,
                result_signature=signature,
            )
        )
        behavior_profile = [
            {
                "presentation_id": record.internal_behavior_to_public[
                    selection.presentation_id
                ],
                "selected_value": selection.selected_value,
            }
            for selection in scored.behavior_profile
        ]
        return ScoreResponse(
            **self._metadata(request_id or new_opaque_id("req")),
            result_id=result_id,
            attempt_id=record.attempt_id,
            issued_at=projection["issued_at"],
            expires_at=projection["expires_at"],
            integrity_status="verified_attempt",
            financial_decision_index=scored.financial_decision_index,
            legacy_demo_score=scored.legacy_demo_score,
            objective_score=objective_display,
            judgment_score=judgment_display,
            behavior_profile=behavior_profile,
            limitations=list(scored.limitations),
            result_signature=signature,
            explanation_digest=digest,
            explanation=explanation,
        )

    def verify(
        self, result_id: str, request_id: str | None = None
    ) -> VerificationResponse:
        record = self.verification_store.get(result_id)
        if record is None:
            raise V2DomainError("result_not_found", 404, {})
        if not self._signing_ready():
            raise V2DomainError("not_ready", 503, {"failed_checks": ["signing"]})
        if not isinstance(record.projection, dict) or not isinstance(
            record.issued_at, datetime
        ) or not isinstance(record.expires_at, datetime):
            raise V2DomainError("integrity_failed", 500, {})
        try:
            signature_matches = constant_time_signature_matches(
                record.projection, record.result_signature, self.signing_secret
            )
        except (TypeError, ValueError):
            signature_matches = False
        if not signature_matches:
            raise V2DomainError("integrity_failed", 500, {})
        if (
            frozenset(record.projection) != _EXPECTED_PROJECTION_KEYS
            or record.projection.get("result_id") != result_id
            or record.projection.get("integrity_status") != "verified_attempt"
            or record.projection.get("issued_at") != format_timestamp(record.issued_at)
            or record.projection.get("expires_at") != format_timestamp(record.expires_at)
        ):
            raise V2DomainError("integrity_failed", 500, {})
        try:
            response_payload = dict(record.projection)
            response_payload["request_id"] = request_id or new_opaque_id("req")
            response_payload["result_signature"] = record.result_signature
            return VerificationResponse(
                **response_payload,
            )
        except (TypeError, ValueError):
            raise V2DomainError("integrity_failed", 500, {})

    @staticmethod
    def _check_versions(submission: ScoreSubmission) -> None:
        if (
            submission.contract_version != CONTRACT_VERSION
            or submission.assessment_version != ASSESSMENT_VERSION
            or submission.scoring_policy_version != SCORING_POLICY_VERSION
        ):
            raise unsupported_version_error()

    @staticmethod
    def _build_attempt_record(
        form: CanonicalInstrumentForm,
        presentation: Any,
        attempt_id: str,
        token: str,
        issued_at: Any,
        expires_at: Any,
    ) -> AttemptRecord:
        public_items: list[dict[str, Any]] = []
        public_behavior_items: list[dict[str, Any]] = []
        public_item_to_internal: dict[str, str] = {}
        public_item_kinds: dict[str, str] = {}
        public_option_to_internal: dict[str, dict[str, str]] = {}
        public_behavior_to_internal: dict[str, str] = {}
        public_behavior_option_to_internal: dict[str, dict[str, str]] = {}
        public_scenario_to_internal: dict[str, str] = {}
        internal_item_to_public: dict[str, str] = {}
        internal_option_to_public: dict[str, dict[str, str]] = {}
        internal_behavior_to_public: dict[str, str] = {}
        internal_scenario_to_public: dict[str, str] = {}
        randomizer = secrets.SystemRandom()

        for internal_item in presentation.items:
            internal_item_id = internal_item.presentation_id
            public_item_id = new_opaque_id("item")
            internal_item_to_public[internal_item_id] = public_item_id
            public_item_to_internal[public_item_id] = internal_item_id
            item_payload = internal_item.model_dump(mode="json")
            item_payload["presentation_id"] = public_item_id
            item_type = item_payload["item_type"]
            if item_type == "objective":
                public_item_kinds[public_item_id] = "objective"
                public_items.append(item_payload)
                continue

            public_item_kinds[public_item_id] = "choice"
            option_map: dict[str, str] = {}
            reverse_option_map: dict[str, str] = {}
            public_options: list[dict[str, str]] = []
            for option in internal_item.options:
                internal_option_id = option.option_id
                public_option_id = new_opaque_id("option")
                option_map[public_option_id] = internal_option_id
                reverse_option_map[internal_option_id] = public_option_id
                public_options.append(
                    {"option_id": public_option_id, "label": option.label}
                )
            randomizer.shuffle(public_options)
            item_payload["options"] = public_options
            public_option_to_internal[public_item_id] = option_map
            internal_option_to_public[internal_item_id] = reverse_option_map
            if item_type == "branching":
                internal_scenario_id = item_payload["scenario_presentation_id"]
                public_scenario_id = internal_scenario_to_public.get(internal_scenario_id)
                if public_scenario_id is None:
                    public_scenario_id = new_opaque_id("scenario")
                    internal_scenario_to_public[internal_scenario_id] = public_scenario_id
                    public_scenario_to_internal[public_scenario_id] = internal_scenario_id
                item_payload["scenario_presentation_id"] = public_scenario_id
            public_items.append(item_payload)

        for internal_item in presentation.behavior_profile_items:
            internal_item_id = internal_item.presentation_id
            public_item_id = new_opaque_id("behavior")
            internal_behavior_to_public[internal_item_id] = public_item_id
            public_behavior_to_internal[public_item_id] = internal_item_id
            item_payload = internal_item.model_dump(mode="json")
            item_payload["presentation_id"] = public_item_id
            option_map: dict[str, str] = {}
            public_options = []
            for option in internal_item.options:
                internal_option_id = option.option_id
                public_option_id = new_opaque_id("behavior_option")
                option_map[public_option_id] = internal_option_id
                public_options.append(
                    {"option_id": public_option_id, "label": option.label}
                )
            randomizer.shuffle(public_options)
            item_payload["options"] = public_options
            public_behavior_option_to_internal[public_item_id] = option_map
            public_behavior_items.append(item_payload)

        record = AttemptRecord(
            attempt_id=attempt_id,
            token_hash=token_digest(token),
            issued_at=issued_at,
            expires_at=expires_at,
            form=form,
            public_items=public_items,
            public_behavior_items=public_behavior_items,
            public_item_to_internal=public_item_to_internal,
            public_item_kinds=public_item_kinds,
            public_option_to_internal=public_option_to_internal,
            public_behavior_to_internal=public_behavior_to_internal,
            public_behavior_option_to_internal=public_behavior_option_to_internal,
            public_scenario_to_internal=public_scenario_to_internal,
            internal_item_to_public=internal_item_to_public,
            internal_option_to_public=internal_option_to_public,
            internal_behavior_to_public=internal_behavior_to_public,
            internal_scenario_to_public=internal_scenario_to_public,
        )
        return record

    def _translate_submission(
        self, record: AttemptRecord, submission: ScoreSubmission
    ) -> tuple[dict[str, int | str], dict[str, str]]:
        expected_items = set(record.public_item_to_internal)
        actual_items = set(submission.responses)
        if actual_items != expected_items:
            raise fields_error("invalid_response", ["responses"])
        internal_responses: dict[str, int | str] = {}
        for public_item_id, raw_value in submission.responses.items():
            internal_item_id = record.public_item_to_internal[public_item_id]
            kind = record.public_item_kinds[public_item_id]
            if kind == "objective":
                if isinstance(raw_value, bool) or not isinstance(raw_value, int):
                    raise fields_error("invalid_response", ["responses"])
                internal_responses[internal_item_id] = raw_value
                continue
            if not isinstance(raw_value, str):
                raise fields_error("invalid_response", ["responses"])
            option_map = record.public_option_to_internal[public_item_id]
            if raw_value not in option_map:
                raise fields_error("unknown_option", ["responses"])
            internal_responses[internal_item_id] = option_map[raw_value]

        expected_behavior = set(record.public_behavior_to_internal)
        actual_behavior = set(submission.behavior_profile)
        if actual_behavior != expected_behavior:
            raise fields_error("invalid_response", ["behavior_profile"])
        internal_behavior: dict[str, str] = {}
        for public_item_id, raw_option_id in submission.behavior_profile.items():
            if not isinstance(raw_option_id, str):
                raise fields_error("invalid_response", ["behavior_profile"])
            option_map = record.public_behavior_option_to_internal[public_item_id]
            if raw_option_id not in option_map:
                raise fields_error("unknown_option", ["behavior_profile"])
            internal_behavior[record.public_behavior_to_internal[public_item_id]] = (
                option_map[raw_option_id]
            )
        return internal_responses, internal_behavior

    @staticmethod
    def _public_explanation(
        payload: dict[str, Any], record: AttemptRecord
    ) -> dict[str, Any]:
        for item in payload["objective_items"]:
            item["presentation_id"] = record.internal_item_to_public[
                item["presentation_id"]
            ]
        for item in payload["static_sjt_items"]:
            item["presentation_id"] = record.internal_item_to_public[
                item["presentation_id"]
            ]
        for scenario in payload["branching_scenarios"]:
            scenario["scenario_presentation_id"] = record.internal_scenario_to_public[
                scenario["scenario_presentation_id"]
            ]
            for timeline in scenario["timeline"]:
                timeline["presentation_id"] = record.internal_item_to_public[
                    timeline["presentation_id"]
                ]
        for recommendation in payload["recommendations"]:
            if recommendation["evidence_type"] == "objective":
                recommendation["evidence_ids"] = [
                    record.internal_item_to_public[item_id]
                    for item_id in recommendation["evidence_ids"]
                ]
            elif recommendation["evidence_type"] == "branching":
                recommendation["evidence_ids"] = [
                    record.internal_scenario_to_public[item_id]
                    for item_id in recommendation["evidence_ids"]
                ]
        return payload


__all__ = ["AnonymousAssessmentService"]
