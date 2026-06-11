import json
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


def test_score_endpoint_rejects_missing_behavioral_telemetry(trained_model_dir) -> None:
    """Verifies that missing the behavioral telemetry group fails validation."""
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    payload = _load_base_payload()
    del payload["behavioral"]  # Delete telemetry block

    with TestClient(app) as client:
        response = client.post("/api/score", json=payload)

    assert response.status_code == 422
    details = response.json().get("detail", [])
    assert any("behavioral" in str(d.get("loc")) for d in details)


def test_score_endpoint_detects_straight_lining(
    trained_model_dir,
) -> None:
    """Verifies that straight-lining triggers a penalty unconditionally."""
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    # Straight-lining payload
    payload_gaming = _load_base_payload()
    # Choose option suffix 'a' for all scenario questions (100% straight-lining)
    for q_key in [
        "scenario_s1",
        "scenario_s2",
        "scenario_s3",
        "scenario_s4",
        "scenario_s5",
        "scenario_s6",
        "scenario_s8",
    ]:
        payload_gaming["answers"][q_key] = {
            "primary": f"{q_key.replace('scenario_', '')}_a"
        }
    payload_gaming["behavioral"]["avg_response_time_ms"] = 1500.0  # Fast pacing

    with TestClient(app) as client:
        resp_gaming = client.post("/api/debug-score", json=payload_gaming)

    assert resp_gaming.status_code == 200

    gaming_trace = resp_gaming.json()
    gaming_mult = gaming_trace["governance_adjustments"]["governance_multiplier"]
    reasons_gaming = gaming_trace["governance_adjustments"]["applied_realism_reasons"]

    # Gaming payload must get a straight-lining penalty
    assert any("straight-lining" in r.lower() for r in reasons_gaming)
    assert gaming_mult < 1.0


def test_score_endpoint_applies_contradiction_severity_tiers(trained_model_dir) -> None:
    """Verifies that severity tiers (Tiers 0-4) apply appropriate, distinct penalties."""
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    # Base payload: Level 0 (No penalty)
    payload_l0 = _load_base_payload()
    payload_l0["answers"]["scenario_s1"] = {"primary": "s1_b"}
    payload_l0["answers"]["scenario_s8"] = {"primary": "s8_b"}
    payload_l0["answers"]["honesty_trap_q1"] = 2

    # Level 1: Mild inconsistency (Soft consistency mismatch alone)
    payload_l1 = _load_base_payload()
    payload_l1["answers"]["scenario_s1"] = {"primary": "s1_b"}
    payload_l1["answers"]["scenario_s8"] = {"primary": "s8_c"}  # Soft consistency 0.65
    payload_l1["answers"]["honesty_trap_q1"] = 2

    # Level 3: Strong contradiction (Trap triggered AND hard S1/S8 consistency mismatch)
    payload_l3 = _load_base_payload()
    payload_l3["answers"]["scenario_s1"] = {"primary": "s1_a"}
    payload_l3["answers"]["scenario_s8"] = {"primary": "s8_b"}  # Hard consistency 0.0
    payload_l3["answers"]["honesty_trap_q1"] = 5  # Honesty trap triggered
    # Keep response time slow to avoid triggering malicious telemetry Tier 4
    payload_l3["behavioral"]["avg_response_time_ms"] = 8000.0

    with TestClient(app) as client:
        trace_l0 = client.post("/api/debug-score", json=payload_l0).json()
        trace_l1 = client.post("/api/debug-score", json=payload_l1).json()
        trace_l3 = client.post("/api/debug-score", json=payload_l3).json()

    mult_l0 = trace_l0["governance_adjustments"]["governance_multiplier"]
    mult_l1 = trace_l1["governance_adjustments"]["governance_multiplier"]
    mult_l3 = trace_l3["governance_adjustments"]["governance_multiplier"]

    # Assert that Level 3 is more penalized than Level 1, which is more penalized than Level 0
    assert mult_l3 < mult_l1 < mult_l0
