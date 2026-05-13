import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.core.settings import load_settings
from backend.app.schemas.common import ErrorResponse
from backend.app.schemas.score import ScoreResponse
from tests.integration.api._support import build_runtime_settings


def _load_valid_score_payload() -> dict:
    return json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "score_request_valid.json"
        ).read_text(encoding="utf-8")
    )


def test_score_endpoint_returns_schema_valid_stub_response(tmp_path) -> None:
    settings = build_runtime_settings(tmp_path)
    payload = _load_valid_score_payload()
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


def test_score_endpoint_writes_success_request_log(tmp_path) -> None:
    settings = build_runtime_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post("/api/score", json=_load_valid_score_payload())

    assert response.status_code == 200
    assert settings.request_log_path.is_file()

    entries = [
        json.loads(line)
        for line in settings.request_log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1

    entry = entries[0]
    assert entry["endpoint"] == "/api/score"
    assert entry["outcome"] == "success"
    assert entry["status_code"] == 200
    assert entry["session_id"] == response.json()["session_id"]
    assert entry["runtime_model_name"] == "logistic_regression"
    assert entry["manifest_version"] is None
    assert 0.0 <= entry["repayment_probability"] <= 1.0
    assert "answers" not in entry
    assert "behavioral" not in entry


def test_score_endpoint_returns_sanitized_500_and_logs_failure(tmp_path) -> None:
    class FailingScoringService:
        def score_request(self, payload) -> ScoreResponse:
            raise RuntimeError("boom")

    settings = build_runtime_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        client.app.state.scoring_service = FailingScoringService()
        response = client.post("/api/score", json=_load_valid_score_payload())

    assert response.status_code == 500
    parsed = ErrorResponse.model_validate(response.json())
    assert parsed.error.code == "SCORING_FAILED"
    assert parsed.error.details == {"error_type": "RuntimeError"}
    assert settings.request_log_path.is_file()

    entries = [
        json.loads(line)
        for line in settings.request_log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    assert entries[0]["outcome"] == "error"
    assert entries[0]["error_code"] == "SCORING_FAILED"
    assert entries[0]["details"] == {"error_type": "RuntimeError"}


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
    assert settings.request_log_path.is_file()

    entries = [
        json.loads(line)
        for line in settings.request_log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(entries) == 1
    assert entries[0]["outcome"] == "error"
    assert entries[0]["error_code"] == "ARTIFACTS_NOT_READY"
    assert "missing_artifacts" in entries[0]["details"]
