"""Post-deploy smoke checks for one exact public v2 release."""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urljoin


CONTRACT_VERSION = "2.0"
ASSESSMENT_VERSION = "india-en-3.0.0"
SCORING_POLICY_VERSION = "readiness-rubric-1.0.0"
MONEY_PATTERN = re.compile(r"(?:\u20b9|Rs\.?|INR)\s*([\d,]+)")
PERCENT_PATTERN = re.compile(r"(\d+)%")
YEAR_PATTERN = re.compile(r"(\d+)\s+year")
MONTH_PATTERN = re.compile(r"(\d+)\s+month")


class SmokeFailure(RuntimeError):
    """A safe, user-facing smoke-check failure without response data."""


@dataclass(frozen=True)
class HttpResult:
    status: int
    payload: dict[str, Any]
    headers: dict[str, str]


def _json_payload(raw: bytes, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SmokeFailure(f"{label}: response was not JSON") from exc
    if not isinstance(payload, dict):
        raise SmokeFailure(f"{label}: response JSON was not an object")
    return payload


def _request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    origin: str | None = None,
) -> HttpResult:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if origin is not None:
        headers["Origin"] = origin
    request = Request(
        f"{base_url}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(
            request, timeout=30, context=ssl.create_default_context()
        ) as response:
            raw = response.read()
            status = response.status
            response_headers = {
                key.lower(): value for key, value in response.headers.items()
            }
    except HTTPError as error:
        raw = error.read()
        status = error.code
        response_headers = {key.lower(): value for key, value in error.headers.items()}
    except (TimeoutError, URLError, OSError) as error:
        raise SmokeFailure(f"{method} {path}: network request failed") from error
    return HttpResult(
        status,
        _json_payload(raw, f"{method} {path}"),
        response_headers,
    )


def _fetch_bytes(url: str, label: str) -> bytes:
    request = Request(url, headers={"Accept": "text/html,application/javascript"})
    try:
        with urlopen(
            request, timeout=30, context=ssl.create_default_context()
        ) as response:
            return response.read()
    except (HTTPError, TimeoutError, URLError, OSError) as error:
        raise SmokeFailure(f"{label}: network request failed") from error


def _require_frontend_release(frontend_url: str, expected_sha: str) -> None:
    if not frontend_url.startswith("https://"):
        raise SmokeFailure("frontend: URL must use HTTPS")
    html = _fetch_bytes(frontend_url.rstrip("/"), "frontend HTML").decode(
        "utf-8", errors="replace"
    )
    sources = [part.split('"', 1)[0] for part in html.split('src="')[1:]]
    if not sources:
        raise SmokeFailure("frontend: no JavaScript assets found")
    fragments = (
        expected_sha.encode("ascii"),
        CONTRACT_VERSION.encode("ascii"),
        ASSESSMENT_VERSION.encode("ascii"),
        SCORING_POLICY_VERSION.encode("ascii"),
    )
    for source in sources:
        asset = _fetch_bytes(
            urljoin(frontend_url.rstrip("/") + "/", source), "frontend asset"
        )
        if all(fragment in asset for fragment in fragments):
            return
    raise SmokeFailure(
        "frontend: deployed bundle does not contain the expected release"
    )


def _require_metadata(payload: dict[str, Any], expected_sha: str, label: str) -> None:
    expected = {
        "contract_version": CONTRACT_VERSION,
        "assessment_version": ASSESSMENT_VERSION,
        "scoring_policy_version": SCORING_POLICY_VERSION,
        "release_sha": expected_sha,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise SmokeFailure(f"{label}: release metadata mismatch for {key}")


def _require_cors(result: HttpResult, origin: str, label: str) -> None:
    if result.headers.get("access-control-allow-origin") != origin:
        raise SmokeFailure(f"{label}: configured frontend origin was not allowed")


def _require_status(result: HttpResult, expected: int, label: str) -> dict[str, Any]:
    if result.status != expected:
        code = result.payload.get("error", {}).get("code")
        suffix = f" ({code})" if isinstance(code, str) else ""
        raise SmokeFailure(
            f"{label}: expected HTTP {expected}, received {result.status}{suffix}"
        )
    return result.payload


def _money_values(prompt: str, label: str) -> list[int]:
    values = [int(raw.replace(",", "")) for raw in MONEY_PATTERN.findall(prompt)]
    if not values:
        raise SmokeFailure(
            f"{label}: objective prompt contained no public money values"
        )
    return values


def _objective_answer(prompt: str, label: str) -> int:
    lowered = prompt.lower()
    amounts = _money_values(prompt, label)
    rates = [int(value) for value in PERCENT_PATTERN.findall(prompt)]
    years = [int(value) for value in YEAR_PATTERN.findall(prompt)]
    months = [int(value) for value in MONTH_PATTERN.findall(prompt)]

    if "starts the month" in lowered:
        return amounts[0] + amounts[1] - amounts[2]
    if "principal of" in lowered and "simple interest" in lowered:
        return amounts[0] * rates[0] * years[0] // 100
    if "offer a charges" in lowered:
        return (
            amounts[0] * (rates[1] - rates[0]) * years[0] // 100
            + amounts[2]
            - amounts[1]
        )
    if "marked at" in lowered and "discount" in lowered:
        return amounts[0] * (100 - rates[0]) // 100
    if "price rises" in lowered:
        return amounts[0] * (100 + rates[0]) // 100
    if "is due" in lowered and "set aside" in lowered:
        return amounts[0] - amounts[1]
    if "loan charges" in lowered:
        return amounts[0] + amounts[0] * rates[0] * years[0] // 100 + amounts[1]
    if "emergency buffer" in lowered:
        return amounts[0] * months[0]
    raise SmokeFailure(f"{label}: unsupported public objective prompt")


def _build_submission(form: dict[str, Any]) -> dict[str, Any]:
    responses: dict[str, int | str] = {}
    for item in form.get("items", []):
        if not isinstance(item, dict):
            raise SmokeFailure("form: item was not an object")
        item_id = item.get("presentation_id")
        if not isinstance(item_id, str):
            raise SmokeFailure("form: item ID was missing")
        if item.get("item_type") == "objective":
            prompt = item.get("prompt")
            if not isinstance(prompt, str):
                raise SmokeFailure("form: objective prompt was missing")
            responses[item_id] = _objective_answer(prompt, item_id)
        else:
            options = item.get("options")
            if not isinstance(options, list) or not options:
                raise SmokeFailure("form: choice options were missing")
            option_id = options[0].get("option_id")
            if not isinstance(option_id, str):
                raise SmokeFailure("form: option ID was missing")
            responses[item_id] = option_id

    behavior: dict[str, str] = {}
    for item in form.get("behavior_profile_items", []):
        item_id = item.get("presentation_id")
        options = item.get("options")
        if not isinstance(item_id, str) or not isinstance(options, list) or not options:
            raise SmokeFailure("form: behavior item was malformed")
        option_id = options[0].get("option_id")
        if not isinstance(option_id, str):
            raise SmokeFailure("form: behavior option ID was missing")
        behavior[item_id] = option_id

    return {
        "contract_version": CONTRACT_VERSION,
        "assessment_version": ASSESSMENT_VERSION,
        "scoring_policy_version": SCORING_POLICY_VERSION,
        "responses": responses,
        "behavior_profile": behavior,
    }


def require_signing_preflight(base_url: str) -> None:
    """Require an already configured provider to expose signing readiness.

    The signing secret stays in the hosting provider's secret store and is
    intentionally never accepted by this script.  This preflight prevents a
    package push from being the first discovery that provider configuration is
    absent or unusable.
    """

    ready_result = _request(base_url, "/api/ready")
    if ready_result.status not in {200, 503}:
        raise SmokeFailure(
            f"readiness: expected HTTP 200 or 503, received {ready_result.status}"
        )
    ready = ready_result.payload
    checks = ready.get("checks")
    if not isinstance(checks, list):
        raise SmokeFailure("readiness: signing check was unavailable")
    signing = next(
        (
            check
            for check in checks
            if isinstance(check, dict) and check.get("name") == "signing"
        ),
        None,
    )
    if not isinstance(signing, dict) or signing.get("status") != "pass":
        raise SmokeFailure("readiness: signing configuration is not ready")


def run(base_url: str, expected_sha: str, frontend_url: str | None = None) -> None:
    origin = frontend_url.rstrip("/") if frontend_url is not None else None
    live_result = _request(base_url, "/api/live", origin=origin)
    if origin is not None:
        _require_cors(live_result, origin, "liveness")
    live = _require_status(live_result, 200, "liveness")
    _require_metadata(live, expected_sha, "liveness")
    if frontend_url is not None:
        _require_frontend_release(frontend_url, expected_sha)

    ready_result = _request(base_url, "/api/ready", origin=origin)
    if origin is not None:
        _require_cors(ready_result, origin, "readiness")
    ready = _require_status(ready_result, 200, "readiness")
    _require_metadata(ready, expected_sha, "readiness")
    checks = ready.get("checks", [])
    expected_checks = (
        "instrument",
        "scorer",
        "signing",
        "attempt_store",
        "verification_store",
        "rate_limits",
    )
    if (
        ready.get("status") != "ready"
        or tuple(check.get("name") for check in checks) != expected_checks
        or any(check.get("status") != "pass" for check in checks)
    ):
        raise SmokeFailure("readiness: not all serving checks passed")

    form_result = _request(base_url, "/api/v2/assessment/form", origin=origin)
    if origin is not None:
        _require_cors(form_result, origin, "form")
    form = _require_status(form_result, 200, "form")
    _require_metadata(form, expected_sha, "form")
    if (
        len(form.get("items", [])) != 18
        or len(form.get("behavior_profile_items", [])) != 6
    ):
        raise SmokeFailure("form: frozen item cardinality mismatch")
    token = form.get("attempt_token")
    if not isinstance(token, str):
        raise SmokeFailure("form: attempt token was missing")
    submission = _build_submission(form)

    wrong_version = dict(submission)
    wrong_version["contract_version"] = "9.9"
    version_error = _request(
        base_url,
        "/api/v2/assessment/score",
        method="POST",
        payload=wrong_version,
        token=token,
        origin=origin,
    )
    if origin is not None:
        _require_cors(version_error, origin, "version rejection")
    version_payload = _require_status(version_error, 422, "version rejection")
    if version_payload.get("error", {}).get("code") != "unsupported_version":
        raise SmokeFailure("version rejection: wrong error code")

    score_result = _request(
        base_url,
        "/api/v2/assessment/score",
        method="POST",
        payload=submission,
        token=token,
        origin=origin,
    )
    if origin is not None:
        _require_cors(score_result, origin, "score")
    score = _require_status(score_result, 200, "score")
    _require_metadata(score, expected_sha, "score")
    result_id = score.get("result_id")
    if not isinstance(result_id, str) or "attempt_token" in score:
        raise SmokeFailure("score: result contract or token boundary failed")

    verification_result = _request(
        base_url, f"/api/v2/results/verify/{result_id}", origin=origin
    )
    if origin is not None:
        _require_cors(verification_result, origin, "verification")
    verification = _require_status(verification_result, 200, "verification")
    _require_metadata(verification, expected_sha, "verification")
    if "explanation" in verification or "behavior_profile" in verification:
        raise SmokeFailure("verification: redacted boundary failed")

    replay = _request(
        base_url,
        "/api/v2/assessment/score",
        method="POST",
        payload=submission,
        token=token,
        origin=origin,
    )
    if origin is not None:
        _require_cors(replay, origin, "replay rejection")
    replay_payload = _require_status(replay, 409, "replay rejection")
    if replay_payload.get("error", {}).get("code") != "attempt_consumed":
        raise SmokeFailure("replay rejection: wrong error code")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", required=True, help="HTTPS origin without the /api suffix"
    )
    parser.add_argument("--expected-release-sha")
    parser.add_argument("--frontend-url", help="HTTPS frontend origin to inspect")
    parser.add_argument(
        "--preflight-signing",
        action="store_true",
        help="require the provider's existing signing readiness before publication",
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    if not base_url.startswith("https://"):
        parser.error("--base-url must use HTTPS")
    if args.frontend_url is not None and not args.frontend_url.startswith("https://"):
        parser.error("--frontend-url must use HTTPS")
    if args.preflight_signing and args.expected_release_sha is not None:
        parser.error(
            "--preflight-signing cannot be combined with --expected-release-sha"
        )
    if not args.preflight_signing and not re.fullmatch(
        r"[0-9a-f]{40}", args.expected_release_sha or ""
    ):
        parser.error("--expected-release-sha must be a 40-character lowercase Git SHA")
    try:
        if args.preflight_signing:
            require_signing_preflight(base_url)
        else:
            run(base_url, args.expected_release_sha, args.frontend_url)
    except SmokeFailure as error:
        print(f"release smoke failed: {error}", file=sys.stderr)
        return 1
    print(f"release smoke passed for {args.expected_release_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
