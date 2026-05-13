from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.schemas.analytics import (
    BaselineComparisonResponse,
    ModelStatsResponse,
)
from backend.app.schemas.common import ErrorResponse
from tests.integration.api._support import build_runtime_settings


def test_model_stats_endpoint_returns_report_backed_metrics(tmp_path) -> None:
    settings = build_runtime_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/model-stats")

    assert response.status_code == 200
    parsed = ModelStatsResponse.model_validate(response.json())
    assert parsed.root
    assert any(item.model_name == "logistic_regression" for item in parsed.root)
    assert any(item.split == "test_months_11_12" for item in parsed.root)


def test_baseline_comparison_endpoint_returns_report_backed_baselines(tmp_path) -> None:
    settings = build_runtime_settings(tmp_path)
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/baseline-comparison")

    assert response.status_code == 200
    parsed = BaselineComparisonResponse.model_validate(response.json())
    assert [item.model_name for item in parsed.root] == [
        "majority_class",
        "logistic_regression",
        "simulated_loan_officer",
    ]


def test_model_stats_endpoint_returns_structured_503_when_metrics_are_missing(
    tmp_path,
) -> None:
    settings = build_runtime_settings(tmp_path)
    (tmp_path / "models" / "reports" / "metrics.json").unlink()
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/model-stats")

    assert response.status_code == 503
    parsed = ErrorResponse.model_validate(response.json())
    assert parsed.error.code == "ARTIFACTS_NOT_READY"
    assert parsed.error.details["missing_artifacts"] == ["metrics"]


def test_baseline_comparison_endpoint_returns_structured_503_when_baselines_are_missing(
    tmp_path,
) -> None:
    settings = build_runtime_settings(tmp_path)
    (tmp_path / "models" / "reports" / "baseline_metrics.json").unlink()
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/baseline-comparison")

    assert response.status_code == 503
    parsed = ErrorResponse.model_validate(response.json())
    assert parsed.error.code == "ARTIFACTS_NOT_READY"
    assert parsed.error.details["missing_artifacts"] == ["baseline_metrics"]
