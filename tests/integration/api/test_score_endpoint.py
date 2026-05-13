import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.core.settings import load_settings
from backend.app.schemas.common import ErrorResponse
from backend.app.schemas.score import ScoreResponse
from tests.integration.api._support import build_runtime_settings


def test_score_endpoint_returns_schema_valid_stub_response(tmp_path) -> None:
    settings = build_runtime_settings(tmp_path)
    payload = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "score_request_valid.json"
        ).read_text(encoding="utf-8")
    )
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post("/api/score", json=payload)

    assert response.status_code == 200
    parsed = ScoreResponse.model_validate(response.json())
    assert 300 <= parsed.credit_score <= 850
    assert parsed.risk_band in {"poor", "fair", "good", "excellent"}
    assert 0.0 <= parsed.repayment_probability <= 1.0
    assert 0 <= parsed.percentile <= 100
    assert parsed.explanation == []
    assert parsed.counterfactual_actions == []
    assert parsed.loan_eligibility.band == parsed.risk_band
    assert parsed.improvement_tips


def test_score_endpoint_returns_structured_503_when_artifacts_are_missing(tmp_path) -> None:
    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
            "ALTERSCORE_RUNTIME_MODEL_PATH": "models/artifacts/logistic_best.pkl",
        }
    )
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post(
            "/api/score",
            json={
                "answers": {
                    "numeracy_q1": 6600,
                    "numeracy_q2": 1120,
                    "numeracy_q3": 14400,
                    "financial_literacy_q1": 1,
                    "financial_literacy_q2": 1,
                    "conscientiousness_q1": 4,
                    "CRT_q1": 5,
                    "CRT_q2": 5,
                    "CRT_q3": 47,
                    "future_orient_q1": 1,
                    "future_orient_q2": 1,
                    "future_orient_q3": 4,
                    "risk_q1": 0,
                    "risk_q2": 1,
                    "locus_q1": 0,
                    "locus_q2": 1,
                    "locus_q3": 4,
                    "social_capital_q1": 2,
                    "social_capital_q2": 0,
                    "social_capital_q3": 0,
                    "resilience_q1": 4,
                    "resilience_q2": 4,
                    "resilience_q3": 0,
                    "loss_aversion_q1": 0,
                    "honesty_trap_q1": 2,
                    "honesty_trap_q2": 3,
                    "future_orient_repeat": 1,
                    "locus_repeat": 0,
                    "reciprocity_q1": 4,
                    "reciprocity_q2": 0,
                    "q27_resilience_text": "I made a plan and looked for extra work."
                },
                "behavioral": {
                    "avg_response_time_ms": 5200.0,
                    "answer_change_rate": 0.08,
                    "session_duration_sec": 410.0,
                    "dropout_count": 0,
                    "scroll_hesitation_score": 0.52,
                    "risk_response_speed_ratio": 0.85,
                    "time_of_day": "afternoon",
                    "device_type": "mobile",
                    "typing_speed_wpm": 34.0
                }
            },
        )

    assert response.status_code == 503
    parsed = ErrorResponse.model_validate(response.json())
    assert parsed.error.code == "ARTIFACTS_NOT_READY"
    assert "missing_artifacts" in parsed.error.details
