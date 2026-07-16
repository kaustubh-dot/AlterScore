import json
from copy import deepcopy
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.schemas.score import ScoreResponse
from tests.integration.api._support import build_runtime_settings
from backend.ml.evaluation.fairness import RED_AUC_GAP_THRESHOLD


def evaluate_fairness_gate(fairness_report: dict) -> dict:
    flagged_groups = list(fairness_report.get("flagged_groups", []))
    worst_auc_gap = float(fairness_report.get("worst_auc_gap", 0.0))
    return {
        "passed": not flagged_groups and worst_auc_gap <= RED_AUC_GAP_THRESHOLD,
        "max_allowed_worst_auc_gap": float(RED_AUC_GAP_THRESHOLD),
        "worst_auc_gap": worst_auc_gap,
        "flagged_groups": flagged_groups,
        "verdict": fairness_report.get("verdict", ""),
    }


def _load_base_payload() -> dict:
    return json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "score_request_valid.json"
        ).read_text(encoding="utf-8")
    )


def _scenario(
    primary: str, least: str | None = None, first_click_ms: float = 8000.0
) -> dict:
    prefix = primary.split("_", maxsplit=1)[0]
    fallback_least = f"{prefix}_b" if not primary.endswith("_b") else f"{prefix}_a"
    return {
        "primary": primary,
        "least": least or fallback_least,
        "first_click_ms": first_click_ms,
        "change_count": 0,
    }


# ---------------------------------------------------------------------------
# 1. Monotonic Score Constraint Verification
# ---------------------------------------------------------------------------


def test_score_endpoint_enforces_monotonicity_on_literacy_answers(
    trained_model_dir,
) -> None:
    """Verifies that correct numeracy answers yield a score >= incorrect answers."""
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    # Base payload with correct math/numeracy answers
    payload_correct = _load_base_payload()
    payload_correct["answers"]["numeracy_q1"] = 6600
    payload_correct["answers"]["numeracy_q2"] = 1120

    # Payload with incorrect math/numeracy answers
    payload_incorrect = _load_base_payload()
    payload_incorrect["answers"]["numeracy_q1"] = 100
    payload_incorrect["answers"]["numeracy_q2"] = 200

    # Submit both to the API
    with TestClient(app) as client:
        resp_correct = client.post("/api/score", json=payload_correct)
        resp_incorrect = client.post("/api/score", json=payload_incorrect)

    assert resp_correct.status_code == 200
    assert resp_incorrect.status_code == 200

    score_correct = ScoreResponse.model_validate(resp_correct.json()).credit_score
    score_incorrect = ScoreResponse.model_validate(resp_incorrect.json()).credit_score

    # Monotonicity test: Score with correct math MUST be greater than or equal to incorrect math
    assert score_correct >= score_incorrect


# ---------------------------------------------------------------------------
# 2. Subgroup Fairness Checks Validation
# ---------------------------------------------------------------------------


def test_fairness_gate_evaluator_correctly_flags_exceeding_gaps() -> None:
    """Verifies that the fairness gate logic correctly flags groups with large gaps."""
    # Case A: Within bounds (worst AUC gap is within limit, no flagged groups)
    gate_pass = evaluate_fairness_gate(
        {
            "worst_auc_gap": 0.04,
            "flagged_groups": [],
            "verdict": "Model is fair and compliant.",
        }
    )
    assert gate_pass["passed"] is True
    assert len(gate_pass["flagged_groups"]) == 0

    # Case B: Exceeding bounds (gap > 0.05 or has flagged groups)
    gate_fail = evaluate_fairness_gate(
        {
            "worst_auc_gap": 0.07,
            "flagged_groups": ["gender=non_binary"],
            "verdict": "Demographic proxy audit alert.",
        }
    )
    assert gate_fail["passed"] is False
    assert "gender=non_binary" in gate_fail["flagged_groups"]


# ---------------------------------------------------------------------------
# 3. Input Payload Validation Guardrails
# ---------------------------------------------------------------------------


def test_score_endpoint_rejects_out_of_bound_inputs(trained_model_dir) -> None:
    """Verifies that the API triggers validation errors for schema out-of-bound entries."""
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    # Load base payload and corrupt financial literacy choice (allowed range is 0 to 3)
    payload = _load_base_payload()
    payload["answers"]["financial_literacy_q1"] = 99  # Out of range

    with TestClient(app) as client:
        response = client.post("/api/score", json=payload)

    # Must return 422 Unprocessable Entity
    assert response.status_code == 422

    # Detail trace check
    details = response.json().get("detail", [])
    assert len(details) > 0
    assert any("financial_literacy_q1" in str(d.get("loc")) for d in details)


def test_score_endpoint_accepts_missing_behavioral_telemetry(trained_model_dir) -> None:
    """Browser telemetry is optional because it cannot affect this demo score."""
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    payload = _load_base_payload()
    del payload["behavioral"]

    with TestClient(app) as client:
        response = client.post("/api/score", json=payload)

    assert response.status_code == 200
    ScoreResponse.model_validate(response.json())


def test_score_endpoint_is_invariant_to_browser_and_scenario_telemetry(
    trained_model_dir,
) -> None:
    """Interaction diagnostics cannot alter the score, probability, or output."""
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    baseline_payload = _load_base_payload()
    telemetry_variant = deepcopy(baseline_payload)
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
        if isinstance(answer, dict):
            answer["first_click_ms"] = 0
            answer["change_count"] = 50

    with TestClient(app) as client:
        baseline = client.post("/api/score", json=baseline_payload)
        variant = client.post("/api/score", json=telemetry_variant)

    assert baseline.status_code == 200, baseline.json()
    assert variant.status_code == 200, variant.json()
    baseline_result = ScoreResponse.model_validate(baseline.json())
    variant_result = ScoreResponse.model_validate(variant.json())
    assert variant_result.credit_score == baseline_result.credit_score
    assert variant_result.repayment_probability == baseline_result.repayment_probability
    assert variant_result.percentile == baseline_result.percentile
    assert variant_result.text_quality == baseline_result.text_quality
