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


def test_score_endpoint_returns_schema_valid_runtime_response(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
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
    assert parsed.counterfactual_actions
    assert all(
        action.estimated_score_gain >= 0 for action in parsed.counterfactual_actions
    )
    assert parsed.loan_eligibility.band == parsed.risk_band
    assert parsed.improvement_tips


def test_score_endpoint_writes_success_request_log(trained_model_dir) -> None:
    settings = build_runtime_settings(trained_model_dir)
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


def test_debug_score_endpoint_returns_pipeline_breakdown(trained_model_dir) -> None:
    settings = build_runtime_settings(trained_model_dir)
    payload = _load_valid_score_payload()
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post("/api/debug-score", json=payload)

    assert response.status_code == 200
    parsed = response.json()
    assert (
        parsed["raw_input"]["answers"]["numeracy_q1"]
        == payload["answers"]["numeracy_q1"]
    )
    assert (
        parsed["validated_request"]["behavioral"]["device_type"]
        == payload["behavioral"]["device_type"]
    )
    assert parsed["feature_names"]
    assert parsed["preprocessing"]["transformed_feature_vector"]
    assert parsed["model_debug"]["repayment_probability"] >= 0.0
    if parsed["model_debug"]["model_type"] == "ensemble":
        assert "runtime_mitigation" in parsed["model_debug"]
        assert "ensemble_probabilities_before_mitigation" in parsed["model_debug"]
    assert parsed["score_mapping"]["final_credit_score"] >= 300
    assert (
        parsed["final_score"]["credit_score"]
        == parsed["score_mapping"]["final_credit_score"]
    )
    assert "explanation_generation_inputs" in parsed


def test_debug_score_endpoint_requires_explicit_opt_in(trained_model_dir) -> None:
    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(trained_model_dir),
            "ALTERSCORE_RUNTIME_MODEL_PATH": "models/artifacts/logistic_best.pkl",
        }
    )
    payload = _load_valid_score_payload()
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post("/api/debug-score", json=payload)

    assert response.status_code == 404
    parsed = response.json()
    assert parsed["error"]["code"] == "DEBUG_NOT_AVAILABLE"


def test_debug_score_endpoint_returns_404_in_production(trained_model_dir) -> None:
    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(trained_model_dir),
            "ALTERSCORE_RUNTIME_MODEL_PATH": "models/artifacts/logistic_best.pkl",
            "ALTERSCORE_ENV": "production",
        }
    )
    payload = _load_valid_score_payload()
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post("/api/debug-score", json=payload)

    assert response.status_code == 404
    parsed = response.json()
    assert parsed["error"]["code"] == "DEBUG_NOT_AVAILABLE"


def test_score_endpoint_returns_sanitized_500_and_logs_failure(
    trained_model_dir,
) -> None:
    class FailingScoringService:
        def score_request(self, payload) -> ScoreResponse:
            raise RuntimeError("boom")

    settings = build_runtime_settings(trained_model_dir)
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


def test_score_endpoint_returns_structured_503_when_artifacts_are_missing(
    tmp_path,
) -> None:
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
            json=_load_valid_score_payload(),
        )

    assert response.status_code == 503
    parsed = ErrorResponse.model_validate(response.json())
    assert parsed.error.code == "ARTIFACTS_NOT_READY"
    assert "missing_artifacts" in parsed.error.details
    assert parsed.error.details["invalid_artifacts"] == []
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
