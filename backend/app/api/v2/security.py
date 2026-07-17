"""Security and bounded in-memory state for the Phase 4 API."""

from __future__ import annotations

from collections import OrderedDict, deque
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import hashlib
import hmac
import json
import math
import secrets
from threading import RLock
import time
from typing import Any, Mapping

from backend.app.instrument import (
    ASSESSMENT_VERSION,
    CONTRACT_VERSION,
    SCORING_POLICY_VERSION,
    CanonicalInstrumentForm,
)


SUPPORTED_VERSIONS = {
    "supported_contract_version": CONTRACT_VERSION,
    "supported_assessment_version": ASSESSMENT_VERSION,
    "supported_scoring_policy_version": SCORING_POLICY_VERSION,
}
MAX_JSON_NESTING = 64


def utc_now() -> datetime:
    """Return a timezone-aware UTC time at the contract's second precision."""

    return datetime.now(timezone.utc).replace(microsecond=0)


def format_timestamp(value: datetime) -> str:
    """Format a UTC timestamp in the exact public representation."""

    return value.astimezone(timezone.utc).replace(microsecond=0).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def new_opaque_id(prefix: str) -> str:
    """Create an opaque identifier with substantially more than 128 random bits."""

    return f"{prefix}_{secrets.token_urlsafe(24)}"


def _attempt_token_key(secret: str) -> bytes:
    """Derive a domain-separated bearer-token signing key."""

    return hashlib.sha256(
        b"alterscore-attempt-token-v1:" + secret.encode("utf-8")
    ).digest()


def issue_signed_attempt_token(
    attempt_id: str,
    issued_at: datetime,
    expires_at: datetime,
    secret: str,
) -> str:
    """Create a signed bearer token whose payload is not client-controlled."""

    if not secret:
        raise ValueError("a signing secret is required")
    payload = {
        "attempt_id": attempt_id,
        "expires_at": format_timestamp(expires_at),
        "issued_at": format_timestamp(issued_at),
        "nonce": secrets.token_urlsafe(24),
        "token_version": "attempt-token-v1",
    }
    encoded_payload = base64.urlsafe_b64encode(
        canonical_json_bytes(payload)
    ).rstrip(b"=").decode("ascii")
    unsigned = f"at1.{encoded_payload}"
    signature = base64.urlsafe_b64encode(
        hmac.new(_attempt_token_key(secret), unsigned.encode("ascii"), hashlib.sha256).digest()
    ).rstrip(b"=").decode("ascii")
    return f"{unsigned}.{signature}"


def verify_signed_attempt_token(
    token: str, secret: str
) -> tuple[str, datetime] | None:
    """Return the signed attempt claim, or ``None`` for any tampering."""

    if not secret or not isinstance(token, str):
        return None
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "at1" or not parts[1] or not parts[2]:
        return None
    if any(
        character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
        for character in parts[1] + parts[2]
    ):
        return None
    unsigned = f"at1.{parts[1]}"
    expected = base64.urlsafe_b64encode(
        hmac.new(_attempt_token_key(secret), unsigned.encode("ascii"), hashlib.sha256).digest()
    ).rstrip(b"=").decode("ascii")
    if not hmac.compare_digest(expected, parts[2]):
        return None
    try:
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        if not isinstance(payload, dict) or set(payload) != {
            "attempt_id",
            "expires_at",
            "issued_at",
            "nonce",
            "token_version",
        }:
            return None
        if (
            not isinstance(payload["attempt_id"], str)
            or not isinstance(payload["expires_at"], str)
            or not isinstance(payload["issued_at"], str)
            or not isinstance(payload["nonce"], str)
            or len(payload["nonce"]) < 32
            or payload["token_version"] != "attempt-token-v1"
        ):
            return None
        expires_at = datetime.fromisoformat(payload["expires_at"][:-1] + "+00:00")
        issued_at = datetime.fromisoformat(payload["issued_at"][:-1] + "+00:00")
        if (
            expires_at.tzinfo != timezone.utc
            or issued_at.tzinfo != timezone.utc
            or format_timestamp(expires_at) != payload["expires_at"]
            or format_timestamp(issued_at) != payload["issued_at"]
            or expires_at <= issued_at
        ):
            return None
        return payload["attempt_id"], expires_at
    except (UnicodeDecodeError, ValueError, TypeError, json.JSONDecodeError):
        return None


def token_digest(token: str) -> str:
    """Hash a bearer secret before it enters bounded process memory."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def extract_bearer_token(authorization: str | None) -> str:
    """Parse one strict bearer header without exposing the secret in errors."""

    if not isinstance(authorization, str):
        raise V2DomainError(
            "malformed_request", 400, {"fields": ["authorization"]}
        )
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise V2DomainError(
            "malformed_request", 400, {"fields": ["authorization"]}
        )
    token = parts[1]
    if any(character.isspace() for character in token) or len(token) > 500:
        raise V2DomainError(
            "malformed_request", 400, {"fields": ["authorization"]}
        )
    return token


class V2DomainError(Exception):
    """A deliberately allow-listed public API failure."""

    def __init__(
        self,
        code: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(code)


_MESSAGES = {
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


def public_error_message(code: str) -> str:
    return _MESSAGES.get(code, _MESSAGES["internal_error"])


def unsupported_version_error() -> V2DomainError:
    return V2DomainError("unsupported_version", 422, dict(SUPPORTED_VERSIONS))


def fields_error(code: str, fields: list[str], status_code: int = 422) -> V2DomainError:
    return V2DomainError(code, status_code, {"fields": sorted(set(fields))})


@dataclass(slots=True)
class AttemptRecord:
    """Private issued attempt state; no public object should expose this class."""

    attempt_id: str
    token_hash: str
    issued_at: datetime
    expires_at: datetime
    form: CanonicalInstrumentForm
    public_items: list[dict[str, Any]]
    public_behavior_items: list[dict[str, Any]]
    public_item_to_internal: dict[str, str]
    public_item_kinds: dict[str, str]
    public_option_to_internal: dict[str, dict[str, str]]
    public_behavior_to_internal: dict[str, str]
    public_behavior_option_to_internal: dict[str, dict[str, str]]
    public_scenario_to_internal: dict[str, str]
    internal_item_to_public: dict[str, str]
    internal_option_to_public: dict[str, dict[str, str]]
    internal_behavior_to_public: dict[str, str]
    internal_scenario_to_public: dict[str, str]
    status: str = "active"


class AttemptStore:
    """Bounded single-use attempt store with serialized lifecycle operations."""

    def __init__(self, *, ttl_seconds: int = 2700, max_entries: int = 10_000) -> None:
        if ttl_seconds <= 0 or max_entries <= 0:
            raise ValueError("attempt store limits must be positive")
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._records: dict[str, AttemptRecord] = {}
        self._lock = RLock()

    def _prune_expired_locked(self, now: datetime) -> None:
        expired = [
            key for key, record in self._records.items() if record.expires_at <= now
        ]
        for key in expired:
            del self._records[key]

    def put(self, record: AttemptRecord) -> None:
        with self._lock:
            self._prune_expired_locked(utc_now())
            while len(self._records) >= self.max_entries:
                evict_key = min(
                    self._records,
                    key=lambda key: (
                        self._records[key].expires_at,
                        self._records[key].issued_at,
                        self._records[key].attempt_id,
                    ),
                )
                del self._records[evict_key]
            self._records[record.token_hash] = record

    def get(self, token_hash: str) -> AttemptRecord:
        now = utc_now()
        with self._lock:
            record = self._records.get(token_hash)
            if record is None:
                raise V2DomainError(
                    "attempt_stale", 409, {"retryable": True, "new_form_required": True}
                )
            if record.expires_at <= now:
                del self._records[token_hash]
                raise V2DomainError(
                    "attempt_expired", 409, {"retryable": True, "new_form_required": True}
                )
            if record.status == "consumed":
                raise V2DomainError(
                    "attempt_consumed", 409, {"retryable": True, "new_form_required": True}
                )
            self._prune_expired_locked(now)
            return record

    def consume(self, token_hash: str, attempt_id: str) -> AttemptRecord:
        now = utc_now()
        with self._lock:
            record = self._records.get(token_hash)
            if record is None or record.attempt_id != attempt_id:
                raise V2DomainError(
                    "attempt_stale", 409, {"retryable": True, "new_form_required": True}
                )
            if record.expires_at <= now:
                del self._records[token_hash]
                raise V2DomainError(
                    "attempt_expired", 409, {"retryable": True, "new_form_required": True}
                )
            if record.status == "consumed":
                raise V2DomainError(
                    "attempt_consumed", 409, {"retryable": True, "new_form_required": True}
                )
            record.status = "consumed"
            self._prune_expired_locked(now)
            return record

    def healthy(self) -> bool:
        with self._lock:
            return self.max_entries > 0 and self.ttl_seconds > 0

    def size(self) -> int:
        with self._lock:
            self._prune_expired_locked(utc_now())
            return len(self._records)


@dataclass(slots=True)
class VerificationRecord:
    """Only the redacted signed projection is retained after scoring."""

    result_id: str
    issued_at: datetime
    expires_at: datetime
    projection: dict[str, Any]
    result_signature: str


class VerificationStore:
    """Bounded result store with TTL and deterministic earliest-entry eviction."""

    def __init__(self, *, ttl_seconds: int = 86_400, max_entries: int = 10_000) -> None:
        if ttl_seconds <= 0 or max_entries <= 0:
            raise ValueError("verification store limits must be positive")
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._records: dict[str, VerificationRecord] = {}
        self._lock = RLock()

    def _prune_expired_locked(self, now: datetime) -> None:
        expired = [
            key for key, record in self._records.items() if record.expires_at <= now
        ]
        for key in expired:
            del self._records[key]

    def put(self, record: VerificationRecord) -> None:
        with self._lock:
            self._prune_expired_locked(utc_now())
            while len(self._records) >= self.max_entries:
                evict_key = min(
                    self._records,
                    key=lambda key: (
                        self._records[key].expires_at,
                        self._records[key].issued_at,
                        self._records[key].result_id,
                    ),
                )
                del self._records[evict_key]
            self._records[record.result_id] = VerificationRecord(
                result_id=record.result_id,
                issued_at=record.issued_at,
                expires_at=record.expires_at,
                projection=deepcopy(record.projection),
                result_signature=record.result_signature,
            )

    def get(self, result_id: str) -> VerificationRecord | None:
        now = utc_now()
        with self._lock:
            record = self._records.get(result_id)
            if record is None:
                self._prune_expired_locked(now)
                return None
            if not isinstance(record.expires_at, datetime) or record.expires_at.tzinfo != timezone.utc:
                return record
            if record.expires_at <= now:
                del self._records[result_id]
                return None
            self._prune_expired_locked(now)
            return record

    def healthy(self) -> bool:
        with self._lock:
            return self.max_entries > 0 and self.ttl_seconds > 0

    def size(self) -> int:
        with self._lock:
            self._prune_expired_locked(utc_now())
            return len(self._records)


class NetworkRateLimiter:
    """Short-lived salted network-hash rate limiter with independent buckets."""

    _WINDOWS = (("burst", 60.0, 10), ("sustained", 3600.0, 30))

    def __init__(
        self,
        *,
        enabled: bool = True,
        salt: bytes | None = None,
        max_networks: int = 10_000,
    ) -> None:
        if max_networks <= 0:
            raise ValueError("max_networks must be positive")
        self.enabled = enabled
        self._salt = salt or secrets.token_bytes(32)
        self._salt_created_at = time.monotonic()
        self.max_networks = max_networks
        self._events: OrderedDict[str, dict[str, deque[float]]] = OrderedDict()
        self._lock = RLock()

    def _network_hash(self, client_host: str | None) -> str:
        host = client_host if isinstance(client_host, str) and client_host else "unknown"
        return hashlib.sha256(self._salt + host.encode("utf-8", "replace")).hexdigest()

    def check(self, bucket: str, client_host: str | None) -> int | None:
        """Return retry seconds when rejected, otherwise ``None``."""

        if not self.enabled:
            return None
        now = time.monotonic()
        network_hash = self._network_hash(client_host)
        with self._lock:
            if now - self._salt_created_at >= 3600.0:
                self._salt = secrets.token_bytes(32)
                self._salt_created_at = now
                self._events.clear()
            buckets = self._events.get(network_hash)
            if buckets is None:
                if len(self._events) >= self.max_networks:
                    self._events.popitem(last=False)
                buckets = {}
                self._events[network_hash] = buckets
            else:
                self._events.move_to_end(network_hash)
            retry_after: float | None = None
            for name, window, limit in self._WINDOWS:
                events = buckets.setdefault(f"{bucket}:{name}", deque())
                while events and now - events[0] >= window:
                    events.popleft()
                if len(events) >= limit:
                    retry = window - (now - events[0])
                    retry_after = max(retry_after or 0.0, retry)
            if retry_after is not None:
                return max(1, math.ceil(retry_after))
            for name, _, _ in self._WINDOWS:
                buckets[f"{bucket}:{name}"].append(now)
            return None

    def healthy(self) -> bool:
        return self.enabled and isinstance(self._salt, bytes) and len(self._salt) >= 16


def _utf16_sort_key(value: str) -> bytes:
    return value.encode("utf-16-be", "surrogatepass")


def _canonicalize_number(value: int | float) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if not math.isfinite(value):
        raise ValueError("non-finite numbers are not valid JCS values")
    if value == 0:
        return "0"
    if value.is_integer() and abs(value) < 1e21:
        return str(int(value))
    # Python's repr supplies the shortest round-trippable significant digits.
    # Convert its exponent form to the ECMAScript/JCS fixed or exponent form.
    encoded = repr(value).lower()
    if "e" not in encoded:
        return encoded
    mantissa, exponent_text = encoded.split("e", 1)
    exponent = int(exponent_text)
    sign = ""
    if mantissa.startswith("-"):
        sign, mantissa = "-", mantissa[1:]
    digits = mantissa.replace(".", "")
    decimal_position = (mantissa.index(".") if "." in mantissa else len(mantissa)) + exponent
    if 1e-6 <= abs(value) < 1e21:
        if decimal_position <= 0:
            return sign + "0." + ("0" * -decimal_position) + digits
        if decimal_position >= len(digits):
            return sign + digits + ("0" * (decimal_position - len(digits)))
        return sign + digits[:decimal_position] + "." + digits[decimal_position:]
    normalized = digits[0]
    if len(digits) > 1:
        normalized += "." + digits[1:]
    exponent = decimal_position - 1
    return f"{sign}{normalized}e{'+' if exponent >= 0 else ''}{exponent}"


def _canonicalize(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _canonicalize_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_canonicalize(item) for item in value) + "]"
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("JCS object keys must be strings")
        entries = sorted(value.items(), key=lambda item: _utf16_sort_key(item[0]))
        return "{" + ",".join(
            _canonicalize(key) + ":" + _canonicalize(item) for key, item in entries
        ) + "}"
    raise TypeError(f"unsupported JCS value type: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return the UTF-8 RFC 8785-compatible representation for domain values."""

    return _canonicalize(value).encode("utf-8")


def explanation_digest(explanation: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(explanation)).hexdigest()


def sign_projection(projection: Mapping[str, Any], secret: str) -> str:
    if not secret:
        raise ValueError("a signing secret is required")
    digest = hmac.new(
        secret.encode("utf-8"), canonical_json_bytes(projection), hashlib.sha256
    ).digest()
    return "hmac-sha256-v1:" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def constant_time_signature_matches(
    projection: Mapping[str, Any], signature: str, secret: str
) -> bool:
    if not isinstance(signature, str):
        return False
    try:
        expected = sign_projection(projection, secret)
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(expected, signature)


class DuplicateJSONKey(ValueError):
    """Raised before Pydantic validation when a JSON object repeats a key."""


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey(key)
        result[key] = value
    return result


def parse_json_object_without_duplicates(body: bytes) -> Any:
    """Decode JSON while rejecting duplicate keys and non-standard constants."""

    def reject_constant(value: str) -> None:
        raise ValueError(value)

    def enforce_nesting_limit(text: str) -> None:
        """Reject deeply nested payloads before a decoder can exhaust recursion."""

        depth = 0
        in_string = False
        escaped = False
        for character in text:
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue
            if character == '"':
                in_string = True
            elif character in "[{":
                depth += 1
                if depth > MAX_JSON_NESTING:
                    raise ValueError("JSON nesting limit exceeded")
            elif character in "]}":
                depth -= 1

    try:
        text = body.decode("utf-8")
        enforce_nesting_limit(text)
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=reject_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        DuplicateJSONKey,
        RecursionError,
        ValueError,
    ) as exc:
        raise ValueError("malformed JSON") from exc


__all__ = [
    "AttemptRecord",
    "AttemptStore",
    "DuplicateJSONKey",
    "NetworkRateLimiter",
    "SUPPORTED_VERSIONS",
    "MAX_JSON_NESTING",
    "V2DomainError",
    "VerificationRecord",
    "VerificationStore",
    "canonical_json_bytes",
    "constant_time_signature_matches",
    "explanation_digest",
    "extract_bearer_token",
    "fields_error",
    "format_timestamp",
    "new_opaque_id",
    "parse_json_object_without_duplicates",
    "public_error_message",
    "issue_signed_attempt_token",
    "sign_projection",
    "token_digest",
    "unsupported_version_error",
    "utc_now",
    "verify_signed_attempt_token",
]
