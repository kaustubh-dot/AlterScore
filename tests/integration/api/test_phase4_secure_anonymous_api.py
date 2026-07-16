"""Adversarial integration coverage for the Phase 4 anonymous contract."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
import base64
import json
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.v2.router import router
from backend.app.api.v2.security import (
    V2DomainError,
    canonical_json_bytes,
    sign_projection,
    token_digest,
    utc_now,
)
from backend.app.api.v2.service import AnonymousAssessmentService

TEST_SIGNING_SECRET = base64.urlsafe_b64encode(bytes(range(32))).rstrip(b"=").decode(
    "ascii"
)


@contextmanager
def _app_client(
    *,
    signing_secret: str | None = TEST_SIGNING_SECRET,
    base_url: str = "https://testserver",
    **service_kwargs: Any,
) -> tuple[TestClient, AnonymousAssessmentService]:
    app = FastAPI()
    app.include_router(router, prefix="/api")
    service = AnonymousAssessmentService(
        release_sha="phase4-test-release",
        signing_secret=signing_secret,
        **service_kwargs,
    )
    app.state.anonymous_assessment_service = service

    @app.middleware("http")
    async def privacy_headers(request, call_next):
        is_phase4_route = request.url.path.startswith("/api/v2/") or request.url.path in {
            "/api/live",
            "/api/ready",
        }
        if is_phase4_route:
            request.state.phase4_network_host = (
                request.client.host if request.client is not None else None
            )
            request.scope["client"] = ("redacted", 0)
        response = await call_next(request)
        if is_phase4_route:
            app.state.phase4_last_access_scope_client = request.scope["client"]
            response.headers["Cache-Control"] = "no-store"
            response.headers["Referrer-Policy"] = "no-referrer"
        return response

    client = TestClient(app, base_url=base_url)
    try:
        yield client, service
    finally:
        client.close()


def _issue(client: TestClient) -> dict[str, Any]:
    response = client.get("/api/v2/assessment/form")
    assert response.status_code == 200, response.text
    return response.json()


def _valid_submission(
    form: dict[str, Any], service: AnonymousAssessmentService
) -> dict[str, Any]:
    record = service.attempt_store._records[token_digest(form["attempt_token"])]
    objective_key = record.form.objective_answer_key()
    responses: dict[str, int | str] = {}
    for item in form["items"]:
        public_id = item["presentation_id"]
        if item["item_type"] == "objective":
            responses[public_id] = objective_key[record.public_item_to_internal[public_id]]
        else:
            responses[public_id] = item["options"][0]["option_id"]
    behavior = {
        item["presentation_id"]: item["options"][0]["option_id"]
        for item in form["behavior_profile_items"]
    }
    return {
        "contract_version": "2.0",
        "assessment_version": "india-en-3.0.0",
        "scoring_policy_version": "readiness-rubric-1.0.0",
        "responses": responses,
        "behavior_profile": behavior,
        "narrative": "A short unscored note.",
    }


def _post_score(
    client: TestClient, form: dict[str, Any], submission: dict[str, Any]
):
    return client.post(
        "/api/v2/assessment/score",
        headers={"Authorization": f"Bearer {form['attempt_token']}"},
        json=submission,
    )


def test_form_is_opaque_strict_and_has_frozen_shape() -> None:
    with _app_client() as (client, service):
        form = _issue(client)
        assert form["contract_version"] == "2.0"
        assert form["assessment_version"] == "india-en-3.0.0"
        assert form["scoring_policy_version"] == "readiness-rubric-1.0.0"
        assert form["integrity_status"] == "issued"
        assert len(form["items"]) == 18
        assert len(form["behavior_profile_items"]) == 6
        assert {item["item_type"] for item in form["items"]} == {
            "objective",
            "static_sjt",
            "branching",
        }
        assert len([i for i in form["items"] if i["item_type"] == "objective"]) == 8
        assert len([i for i in form["items"] if i["item_type"] == "static_sjt"]) == 4
        assert len([i for i in form["items"] if i["item_type"] == "branching"]) == 6
        serialized = json.dumps(form)
        assert "correct_answer" not in serialized
        assert "rubric_points" not in serialized
        assert "generation_rule" not in serialized
        assert "objective_01" not in serialized
        assert "static_sjt_01" not in serialized
        assert "scenario_emi_supplier" not in serialized
        assert form["attempt_token"] not in json.dumps(
            service.verification_store._records
        )
        assert client.get("/api/v2/assessment/form").json()["attempt_id"] != form[
            "attempt_id"
        ]


def test_score_is_signed_explained_and_verification_is_redacted() -> None:
    with _app_client() as (client, service):
        form = _issue(client)
        score_response = _post_score(client, form, _valid_submission(form, service))
        assert score_response.status_code == 200, score_response.text
        score = score_response.json()
        assert score["integrity_status"] == "verified_attempt"
        assert score["issued_at"] != form["issued_at"]
        issued = datetime.fromisoformat(score["issued_at"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(score["expires_at"].replace("Z", "+00:00"))
        assert (expires - issued).total_seconds() == 86_400
        assert len(score["behavior_profile"]) == 6
        assert len(score["explanation"]["objective_items"]) == 8
        assert len(score["explanation"]["static_sjt_items"]) == 4
        assert len(score["explanation"]["branching_scenarios"]) == 2
        issued_ids = {
            item["presentation_id"] for item in form["items"]
        }
        explanation_ids = {
            item["presentation_id"]
            for item in score["explanation"]["objective_items"]
        }
        assert explanation_ids <= issued_ids
        assert "objective_01" not in json.dumps(score["explanation"])

        verify_response = client.get(
            f"/api/v2/results/verify/{score['result_id']}"
        )
        assert verify_response.status_code == 200, verify_response.text
        verified = verify_response.json()
        assert set(verified) == {
            "contract_version",
            "assessment_version",
            "scoring_policy_version",
            "request_id",
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
            "result_signature",
        }
        assert "explanation" not in verified
        assert "behavior_profile" not in verified
        assert "narrative" not in verified
        assert "responses" not in verified
        assert "attempt_token" not in verified
        assert verify_response.headers["cache-control"] == "no-store"
        assert verify_response.headers["referrer-policy"] == "no-referrer"


def test_replay_is_atomic_and_cross_attempt_answers_do_not_consume() -> None:
    with _app_client() as (client, service):
        first = _issue(client)
        second = _issue(client)
        second_submission = _valid_submission(second, service)
        cross_attempt = _post_score(client, first, second_submission)
        assert cross_attempt.status_code == 422
        assert cross_attempt.json()["error"]["code"] == "invalid_response"

        valid = _post_score(client, first, _valid_submission(first, service))
        assert valid.status_code == 200, valid.text
        replay = _post_score(client, first, _valid_submission(first, service))
        assert replay.status_code == 409
        assert replay.json()["error"]["code"] == "attempt_consumed"


def test_tampered_and_expired_attempt_tokens_are_recoverable() -> None:
    with _app_client() as (client, service):
        form = _issue(client)
        tampered_token = form["attempt_token"][:-1] + (
            "A" if form["attempt_token"][-1] != "A" else "B"
        )
        tampered = client.post(
            "/api/v2/assessment/score",
            headers={"Authorization": f"Bearer {tampered_token}"},
            json=_valid_submission(form, service),
        )
        assert tampered.status_code == 409
        assert tampered.json()["error"]["code"] == "attempt_stale"

        record = service.attempt_store._records[token_digest(form["attempt_token"])]
        record.expires_at = utc_now()
        expired = _post_score(client, form, _valid_submission(form, service))
        assert expired.status_code == 409
        assert expired.json()["error"]["code"] == "attempt_expired"


def test_bearer_form_and_score_transport_require_https() -> None:
    with _app_client(base_url="http://testserver") as (client, _):
        form = client.get("/api/v2/assessment/form")
        assert form.status_code == 400
        assert form.json()["error"]["code"] == "malformed_request"
        assert form.json()["error"]["details"] == {"fields": ["transport"]}
        assert "attempt_token" not in form.text

        score = client.post(
            "/api/v2/assessment/score",
            headers={"Authorization": "Bearer secret-that-must-not-be-processed"},
            content="{}",
        )
        assert score.status_code == 400
        assert score.json()["error"]["details"] == {"fields": ["transport"]}
        assert "secret-that-must-not-be-processed" not in score.text


def test_phase4_access_scope_is_redacted_after_rate_limit_capture() -> None:
    with _app_client() as (client, service):
        form = _issue(client)
        record = service.attempt_store._records[token_digest(form["attempt_token"])]
        assert record is not None
        assert client.app.state.phase4_last_access_scope_client == ("redacted", 0)
        assert service.rate_limiter._network_hash("testclient") in service.rate_limiter._events
        assert service.rate_limiter._network_hash("redacted") not in service.rate_limiter._events


def test_unknown_option_and_duplicate_json_keys_fail_without_consuming() -> None:
    with _app_client() as (client, service):
        form = _issue(client)
        submission = _valid_submission(form, service)
        choice_id = next(
            item["presentation_id"]
            for item in form["items"]
            if item["item_type"] != "objective"
        )
        submission["responses"][choice_id] = "invented-option"
        unknown = _post_score(client, form, submission)
        assert unknown.status_code == 422
        assert unknown.json()["error"]["code"] == "unknown_option"
        valid = _post_score(client, form, _valid_submission(form, service))
        assert valid.status_code == 200, valid.text

        fresh = _issue(client)
        duplicate_body = (
            '{"contract_version":"2.0",'
            '"assessment_version":"india-en-3.0.0",'
            '"scoring_policy_version":"readiness-rubric-1.0.0",'
            '"responses":{},"responses":{},"behavior_profile":{}}'
        )
        duplicate = client.post(
            "/api/v2/assessment/score",
            headers={"Authorization": f"Bearer {fresh['attempt_token']}"},
            content=duplicate_body,
        )
        assert duplicate.status_code == 400
        assert duplicate.json()["error"]["code"] == "malformed_request"


def test_extra_attempt_fields_and_invalid_types_are_rejected() -> None:
    with _app_client() as (client, service):
        form = _issue(client)
        submission = _valid_submission(form, service)
        submission["attempt_id"] = form["attempt_id"]
        extra = _post_score(client, form, submission)
        assert extra.status_code == 422
        assert extra.json()["error"]["code"] == "invalid_response"
        assert extra.json()["error"]["details"]["fields"] == ["body"]

        invalid = _valid_submission(form, service)
        objective_id = next(
            item["presentation_id"]
            for item in form["items"]
            if item["item_type"] == "objective"
        )
        invalid["responses"][objective_id] = True
        invalid_response = _post_score(client, form, invalid)
        assert invalid_response.status_code == 422


def test_deep_json_is_rejected_without_consuming_the_attempt() -> None:
    with _app_client() as (client, service):
        form = _issue(client)
        deeply_nested = ("[" * 8_000) + ("]" * 8_000)
        rejected = client.post(
            "/api/v2/assessment/score",
            headers={"Authorization": f"Bearer {form['attempt_token']}"},
            content=deeply_nested,
        )
        assert rejected.status_code == 400
        assert rejected.json()["error"] == {
            "code": "malformed_request",
            "message": "The request could not be parsed.",
            "details": {"fields": ["body"]},
            "request_id": rejected.json()["error"]["request_id"],
            "timestamp": rejected.json()["error"]["timestamp"],
        }
        valid = _post_score(client, form, _valid_submission(form, service))
        assert valid.status_code == 200, valid.text


def test_tampered_result_signature_or_digest_never_returns_summary() -> None:
    with _app_client() as (client, service):
        form = _issue(client)
        score = _post_score(client, form, _valid_submission(form, service)).json()
        record = service.verification_store._records[score["result_id"]]
        record.result_signature = "hmac-sha256-v1:" + "A" * 43
        tampered_signature = client.get(
            f"/api/v2/results/verify/{score['result_id']}"
        )
        assert tampered_signature.status_code == 500
        assert tampered_signature.json()["error"]["code"] == "integrity_failed"

        form2 = _issue(client)
        score2 = _post_score(client, form2, _valid_submission(form2, service)).json()
        record2 = service.verification_store._records[score2["result_id"]]
        record2.projection["explanation_digest"] = "sha256:" + "0" * 64
        tampered_digest = client.get(
            f"/api/v2/results/verify/{score2['result_id']}"
        )
        assert tampered_digest.status_code == 500
        assert tampered_digest.json()["error"]["code"] == "integrity_failed"


def test_rate_limit_readiness_and_liveness_boundaries() -> None:
    with _app_client() as (client, _):
        for _ in range(10):
            assert client.get("/api/v2/assessment/form").status_code == 200
        limited = client.get("/api/v2/assessment/form")
        assert limited.status_code == 429
        assert limited.json()["error"]["details"]["retry_after_seconds"] >= 1

    for invalid_secret in (None, "a" * 32, "A" * 43):
        with _app_client(signing_secret=invalid_secret) as (client, _):
            ready = client.get("/api/ready")
            assert ready.status_code == 503
            ready_payload = ready.json()
            assert ready_payload["status"] == "not_ready"
            assert next(
                check for check in ready_payload["checks"] if check["name"] == "signing"
            )["status"] == "fail"
            unavailable = client.get("/api/v2/assessment/form")
            assert unavailable.status_code == 503
            assert unavailable.json()["error"]["code"] == "form_unavailable"
            assert client.get("/api/live").status_code == 200


def test_store_eviction_and_canonical_signing_are_deterministic() -> None:
    with _app_client(result_store_max_entries=1) as (client, service):
        first = _issue(client)
        first_score = _post_score(client, first, _valid_submission(first, service)).json()
        second = _issue(client)
        second_score = _post_score(client, second, _valid_submission(second, service)).json()
        assert client.get(
            f"/api/v2/results/verify/{first_score['result_id']}"
        ).status_code == 404
        assert client.get(
            f"/api/v2/results/verify/{second_score['result_id']}"
        ).status_code == 200

        assert canonical_json_bytes({"b": 1, "a": 2}) == b'{"a":2,"b":1}'
        assert canonical_json_bytes({"x": 1e-6}) == b'{"x":0.000001}'
        assert canonical_json_bytes({"x": 1e-7}) == b'{"x":1e-7}'
        assert canonical_json_bytes({"x": 1e21}) == b'{"x":1e+21}'
        projection = {"z": 0, "a": 100, "nested": [1, 2, 3]}
        assert sign_projection(projection, "same") == sign_projection(
            {"nested": [1, 2, 3], "a": 100, "z": 0}, "same"
        )


def test_attempt_and_verification_process_loss_are_recoverable() -> None:
    with _app_client(attempt_store_max_entries=1) as (client, service):
        evicted = _issue(client)
        evicted_submission = _valid_submission(evicted, service)
        replacement = _issue(client)
        stale = _post_score(client, evicted, evicted_submission)
        assert stale.status_code == 409
        assert stale.json()["error"]["code"] == "attempt_stale"

        recovered = _post_score(
            client, replacement, _valid_submission(replacement, service)
        )
        assert recovered.status_code == 200, recovered.text
        result_id = recovered.json()["result_id"]
        service.verification_store._records.clear()
        assert client.get(f"/api/v2/results/verify/{result_id}").status_code == 404

        lost = _issue(client)
        lost_submission = _valid_submission(lost, service)
        service.attempt_store._records.clear()
        lost_attempt = _post_score(client, lost, lost_submission)
        assert lost_attempt.status_code == 409
        assert lost_attempt.json()["error"]["code"] == "attempt_stale"


def test_result_expiry_and_immediate_retry_are_recoverable() -> None:
    with _app_client() as (client, service):
        first = _issue(client)
        first_score = _post_score(client, first, _valid_submission(first, service))
        assert first_score.status_code == 200, first_score.text
        result_id = first_score.json()["result_id"]
        service.verification_store._records[result_id].expires_at = utc_now()
        assert client.get(f"/api/v2/results/verify/{result_id}").status_code == 404

        retry = _issue(client)
        assert retry["attempt_id"] != first["attempt_id"]
        retry_score = _post_score(client, retry, _valid_submission(retry, service))
        assert retry_score.status_code == 200, retry_score.text


def test_concurrent_duplicate_submission_has_one_winner() -> None:
    with _app_client() as (client, service):
        form = _issue(client)
        submission = _valid_submission(form, service)
        from backend.app.api.v2.models import ScoreSubmission

        parsed = ScoreSubmission.model_validate(submission)

        def submit_once():
            try:
                return service.submit(form["attempt_token"], parsed)
            except V2DomainError as error:
                return error.code

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: submit_once(), range(2)))
        assert sum(result != "attempt_consumed" for result in results) == 1
        assert "attempt_consumed" in results


def test_unknown_result_is_privacy_preserving() -> None:
    with _app_client() as (client, _):
        response = client.get("/api/v2/results/verify/result_does_not_exist")
        assert response.status_code == 404
        assert response.json()["error"] == {
            "code": "result_not_found",
            "message": "The requested result is not available.",
            "details": {},
            "request_id": response.json()["error"]["request_id"],
            "timestamp": response.json()["error"]["timestamp"],
        }


def test_real_create_app_is_independent_of_archived_artifacts() -> None:
    from backend.app import main
    from backend.app.core.settings import load_settings

    settings = load_settings(
        {
            "ALTERSCORE_SIGNING_SECRET": TEST_SIGNING_SECRET,
            "ALTERSCORE_ENV": "local",
        }
    )
    with TestClient(main.create_app(settings), base_url="https://testserver") as client:
        live = client.get("/api/live")
        ready = client.get("/api/ready")
        health = client.get("/api/health")
        assert live.status_code == 200
        assert live.json()["status"] == "ok"
        assert ready.status_code == 200
        assert ready.json()["status"] == "ready"
        assert health.status_code == 200
        assert health.json()["service"] == "public-v2"
