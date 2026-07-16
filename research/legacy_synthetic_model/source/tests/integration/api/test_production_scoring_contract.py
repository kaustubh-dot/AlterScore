"""Regression contracts for the checked-in production scoring bundle.

These tests deliberately load the repository's production manifest instead of a
test-trained fallback model.  They protect product-policy guarantees while
allowing a promoted model name or version to change with the manifest.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.app.core.paths import REPO_ROOT
from backend.app.core.settings import Settings, load_settings
from backend.app.main import create_app
from backend.app.schemas.score import ScoreResponse


RAW_TELEMETRY_FEATURES = {
    "answer_change_rate",
    "avg_response_time_ms",
    "change_count",
    "device_type",
    "dropout_count",
    "first_click_ms",
    "risk_response_speed_ratio",
    "scenario_change_rate",
    "scenario_fast_gaming",
    "scenario_straight_lining_ratio",
    "scroll_hesitation_score",
    "session_duration_sec",
    "time_of_day",
    "typing_speed_wpm",
}
LENDER_DECISION_FIELD_FRAGMENTS = {
    "approval",
    "decision",
    "eligibility",
    "eligible",
    "lender",
    "loan",
}


def _scenario(primary: str, least: str) -> dict[str, Any]:
    return {
        "primary": primary,
        "least": least,
        "first_click_ms": 5_200,
        "change_count": 0,
    }


_PERSONA_ANSWERS: dict[str, dict[str, Any]] = {
    "thoughtful": {
        "numeracy_q1": 6600,
        "numeracy_q2": 1120,
        "financial_literacy_q1": 1,
        "CRT_q1": 5,
        "CRT_q2": 47,
        "scenario_s1": _scenario("s1_c", "s1_a"),
        "scenario_s2": _scenario("s2_b", "s2_d"),
        "scenario_s3": _scenario("s3_c", "s3_d"),
        "scenario_s4": _scenario("s4_d", "s4_a"),
        "scenario_s5": _scenario("s5_d", "s5_a"),
        "scenario_s6": _scenario("s6_d", "s6_a"),
        "honesty_trap_q1": 2,
        "scenario_s8": _scenario("s8_a", "s8_b"),
        "open_response_text": (
            "When income fell, I reduced discretionary spending, planned repayments, "
            "and completed each payment before taking on new costs."
        ),
    },
    "average": {
        "numeracy_q1": 6600,
        "numeracy_q2": 1120,
        "financial_literacy_q1": 1,
        "CRT_q1": 5,
        "CRT_q2": 24,
        "scenario_s1": _scenario("s1_c", "s1_b"),
        "scenario_s2": _scenario("s2_c", "s2_d"),
        "scenario_s3": _scenario("s3_b", "s3_d"),
        "scenario_s4": _scenario("s4_b", "s4_c"),
        "scenario_s5": _scenario("s5_c", "s5_b"),
        "scenario_s6": _scenario("s6_b", "s6_d"),
        "honesty_trap_q1": 3,
        "scenario_s8": _scenario("s8_c", "s8_b"),
        "open_response_text": (
            "When my laptop broke, I planned the repair payments, protected my work, "
            "and reduced other spending until the bill was paid."
        ),
    },
    "impulsive": {
        "numeracy_q1": 6000,
        "numeracy_q2": 100,
        "financial_literacy_q1": 0,
        "CRT_q1": 100,
        "CRT_q2": 10,
        "scenario_s1": _scenario("s1_d", "s1_b"),
        "scenario_s2": _scenario("s2_d", "s2_b"),
        "scenario_s3": _scenario("s3_d", "s3_b"),
        "scenario_s4": _scenario("s4_d", "s4_b"),
        "scenario_s5": _scenario("s5_a", "s5_c"),
        "scenario_s6": _scenario("s6_d", "s6_b"),
        "honesty_trap_q1": 3,
        "scenario_s8": _scenario("s8_d", "s8_b"),
        "open_response_text": (
            "I spent first, then asked for help and made a smaller repayment plan "
            "after the emergency became urgent."
        ),
    },
    "gamed": {
        "numeracy_q1": 6600,
        "numeracy_q2": 1120,
        "financial_literacy_q1": 1,
        "CRT_q1": 5,
        "CRT_q2": 47,
        "scenario_s1": _scenario("s1_a", "s1_b"),
        "scenario_s2": _scenario("s2_a", "s2_b"),
        "scenario_s3": _scenario("s3_a", "s3_b"),
        "scenario_s4": _scenario("s4_a", "s4_b"),
        "scenario_s5": _scenario("s5_a", "s5_b"),
        "scenario_s6": _scenario("s6_a", "s6_b"),
        "honesty_trap_q1": 5,
        "scenario_s8": _scenario("s8_b", "s8_a"),
        "open_response_text": (
            "Everything was perfectly fine. I solved every financial difficulty "
            "instantly and never needed to change any decision or plan."
        ),
    },
}
_DEFAULT_BEHAVIORAL_PAYLOAD = {
    "avg_response_time_ms": 5_200.0,
    "answer_change_rate": 0.02,
    "session_duration_sec": 360.0,
    "dropout_count": 0,
    "scroll_hesitation_score": 0.05,
    "risk_response_speed_ratio": 1.0,
    "time_of_day": "afternoon",
    "device_type": "desktop",
    "typing_speed_wpm": 42.0,
}


def _production_settings(tmp_path_factory) -> Settings:
    log_dir = tmp_path_factory.mktemp("production-scoring-contract")
    return load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(REPO_ROOT),
            "ALTERSCORE_REQUEST_LOG_PATH": str(log_dir / "requests.jsonl"),
            "ALTERSCORE_ENABLE_DEBUG_SCORE": "true",
            "ALTERSCORE_ENV": "local",
        }
    )


@pytest.fixture(scope="module")
def production_client(tmp_path_factory):
    """Serve requests through the checked-in manifest and artifact bundle."""

    app = create_app(_production_settings(tmp_path_factory))
    with TestClient(app) as client:
        yield client


def _persona_payload(name: str) -> dict[str, Any]:
    return {
        "session_id": f"production-contract-{name}",
        "answers": deepcopy(_PERSONA_ANSWERS[name]),
        "behavioral": deepcopy(_DEFAULT_BEHAVIORAL_PAYLOAD),
    }


def _current_frontend_payload(name: str) -> dict[str, Any]:
    """Build the answer-only payload emitted by the checked-in assessment UI."""

    answers = deepcopy(_PERSONA_ANSWERS[name])
    answers.pop("scenario_s8")
    for answer in answers.values():
        if isinstance(answer, dict):
            answer.pop("first_click_ms", None)
            answer.pop("change_count", None)
    return {"session_id": f"frontend-contract-{name}", "answers": answers}


def _score(client: TestClient, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post("/api/score", json=payload)
    assert response.status_code == 200, response.json()
    result = response.json()
    ScoreResponse.model_validate(result)
    return result


def _debug_score(client: TestClient, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post("/api/debug-score", json=payload)
    assert response.status_code == 200, response.json()
    return response.json()


def _nested_mapping_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            key for nested in value.values() for key in _nested_mapping_keys(nested)
        }
    if isinstance(value, list):
        return {key for nested in value for key in _nested_mapping_keys(nested)}
    return set()


def test_production_bundle_identity_is_derived_from_its_manifest(
    production_client: TestClient,
) -> None:
    """A promotion may change identity, but runtime must match its manifest."""

    bundle = production_client.app.state.artifact_bundle
    manifest = bundle.manifest

    assert bundle.report.source == "manifest"
    assert bundle.report.scoring_ready is True
    assert manifest is not None
    assert bundle.report.runtime_model_name == manifest["runtime_model_name"]
    assert bundle.report.runtime_model_type == manifest["runtime_model_type"]
    assert bundle.report.model_version == manifest["model_version"]
    assert bundle.report.manifest_version == manifest["manifest_version"]
    assert "runtime_model" in bundle.report.artifacts_loaded
    assert "preprocessor" in bundle.report.artifacts_loaded


def test_current_frontend_payload_is_accepted_without_telemetry_or_s8(
    production_client: TestClient,
) -> None:
    """The checked-in answer-only frontend must match the serving contract."""

    result = _score(production_client, _current_frontend_payload("thoughtful"))
    assert result["session_id"] == "frontend-contract-thoughtful"
    assert result["text_quality"]["status"] == "substantive"


def test_production_personas_preserve_relative_score_ordering(
    production_client: TestClient,
) -> None:
    """Answer quality—not browser behavior—must drive stable policy ordering."""

    results = {
        name: _score(production_client, _persona_payload(name))
        for name in ("thoughtful", "average", "impulsive", "gamed")
    }

    assert (
        results["thoughtful"]["credit_score"]
        > results["average"]["credit_score"]
        > results["impulsive"]["credit_score"]
    )
    assert (
        results["thoughtful"]["repayment_probability"]
        > results["average"]["repayment_probability"]
        > results["impulsive"]["repayment_probability"]
    )
    assert results["gamed"]["credit_score"] <= results["thoughtful"][
        "credit_score"
    ]
    assert results["gamed"]["repayment_probability"] <= results["thoughtful"][
        "repayment_probability"
    ]


def test_production_score_is_invariant_to_raw_browser_telemetry(
    production_client: TestClient,
) -> None:
    """Changing raw device, time, and interaction data cannot change the score."""

    baseline_payload = _persona_payload("thoughtful")
    telemetry_variant = deepcopy(baseline_payload)
    telemetry_variant["session_id"] = "production-contract-telemetry-variant"
    telemetry_variant["behavioral"] = {
        "avg_response_time_ms": 100.0,
        "answer_change_rate": 1.0,
        "session_duration_sec": 0.0,
        "dropout_count": 20,
        "scroll_hesitation_score": 1.0,
        "risk_response_speed_ratio": 5.0,
        "time_of_day": "night",
        "device_type": "tablet",
        "typing_speed_wpm": 200.0,
    }
    for answer in telemetry_variant["answers"].values():
        if isinstance(answer, dict) and "first_click_ms" in answer:
            answer["first_click_ms"] = 0
            answer["change_count"] = 50

    baseline = _score(production_client, baseline_payload)
    variant = _score(production_client, telemetry_variant)

    for field_name in (
        "credit_score",
        "repayment_probability",
        "percentile",
        "text_quality",
    ):
        assert variant[field_name] == baseline[field_name]

    for collection_name in ("explanation", "counterfactual_actions"):
        for item in baseline[collection_name]:
            assert item["feature"] not in RAW_TELEMETRY_FEATURES


@pytest.mark.parametrize(
    ("case_name", "open_response_text", "expected_status", "expected_adjustment"),
    [
        ("limited", "I made a plan.", "limited", -6),
        ("empty", "", "limited", -6),
        (
            "gibberish",
            "plan plan plan plan plan plan plan plan plan plan plan plan",
            "gibberish",
            -12,
        ),
    ],
)
def test_production_text_quality_is_accepted_bounded_and_explained(
    production_client: TestClient,
    case_name: str,
    open_response_text: str,
    expected_status: str,
    expected_adjustment: int,
) -> None:
    """Weak text is usable, with only the declared bounded adjustment."""

    substantive_payload = _persona_payload("thoughtful")
    degraded_payload = deepcopy(substantive_payload)
    degraded_payload["session_id"] = f"production-contract-text-{case_name}"
    degraded_payload["answers"]["open_response_text"] = open_response_text

    substantive = _score(production_client, substantive_payload)
    degraded = _score(production_client, degraded_payload)
    debug_trace = _debug_score(production_client, degraded_payload)

    quality = degraded["text_quality"]
    assert quality["status"] == expected_status
    assert quality["score_adjustment_points"] == expected_adjustment
    assert quality["max_penalty_points"] == 12
    assert -quality["max_penalty_points"] <= quality["score_adjustment_points"] <= 0
    assert quality["reason"].strip()
    assert degraded["credit_score"] - substantive["credit_score"] == expected_adjustment

    debug_quality = debug_trace["text_quality_adjustment"]
    assert debug_quality["status"] == expected_status
    assert debug_quality["score_adjustment_points"] == expected_adjustment
    assert debug_quality["max_penalty_points"] == 12
    assert debug_quality["base_credit_score"] + expected_adjustment == debug_quality[
        "final_credit_score"
    ]
    assert debug_quality["final_credit_score"] == degraded["credit_score"]


def test_score_outputs_are_backend_sourced_and_lender_decision_free(
    production_client: TestClient,
) -> None:
    """Clients cannot inject score outputs, and the API makes no lender decision."""

    forged_payload = _persona_payload("thoughtful")
    forged_payload.update(
        {
            "credit_score": 850,
            "risk_band": "excellent",
            "repayment_probability": 1.0,
            "percentile": 100,
            "loan_eligibility": {"approved": True},
        }
    )
    forged_response = production_client.post("/api/score", json=forged_payload)
    assert forged_response.status_code == 422

    result = _score(production_client, _persona_payload("thoughtful"))
    assert result["session_id"] == "production-contract-thoughtful"
    assert not any(
        fragment in key.lower()
        for key in _nested_mapping_keys(result)
        for fragment in LENDER_DECISION_FIELD_FRAGMENTS
    ), result
