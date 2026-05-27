import json

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.schemas.analytics import (
    BaselineComparisonResponse,
    CalibrationCurveResponse,
    ConfusionMatrixResponse,
    DriftReport,
    FairnessReport,
    GlobalImportanceResponse,
    ModelStatsResponse,
    PrecisionRecallResponse,
    RocCurveResponse,
    ScoreDistributionResponse,
)
from backend.app.schemas.common import ErrorResponse
from tests.integration.api._support import build_runtime_settings


def test_model_stats_endpoint_returns_report_backed_metrics(trained_model_dir) -> None:
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/model-stats")

    assert response.status_code == 200
    parsed = ModelStatsResponse.model_validate(response.json())
    assert parsed.root
    assert any(item.model_name == "logistic_regression" for item in parsed.root)
    assert any(item.split == "test_months_11_12" for item in parsed.root)


def test_baseline_comparison_endpoint_returns_report_backed_baselines(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
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


def test_governance_report_endpoints_return_saved_report_payloads(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    with TestClient(app) as client:
        fairness_response = client.get("/api/fairness-report")
        drift_response = client.get("/api/drift-report")
        global_importance_response = client.get("/api/global-importance")

    assert fairness_response.status_code == 200
    fairness = FairnessReport.model_validate(fairness_response.json())
    assert fairness.groups["gender"]
    assert fairness.worst_auc_gap >= 0.0
    assert fairness.calibration_parity is not None
    assert fairness.calibration_parity.groups["gender"]
    assert fairness.individual_fairness_proxy is not None
    assert fairness.individual_fairness_proxy.evaluated_pairs > 0

    assert drift_response.status_code == 200
    drift = DriftReport.model_validate(drift_response.json())
    assert drift.all_features
    assert drift.max_psi == drift.all_features[0].psi

    assert global_importance_response.status_code == 200
    importance = GlobalImportanceResponse.model_validate(
        global_importance_response.json()
    )
    assert importance.model_name == "logistic_regression"
    assert len(importance.items) == 35
    assert importance.items[0].rank == 1
    assert importance.items[0].mean_abs_shap >= importance.items[-1].mean_abs_shap


def test_score_distribution_endpoint_returns_saved_histogram_payload(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/score-distribution")

    assert response.status_code == 200
    parsed = ScoreDistributionResponse.model_validate(response.json())
    assert parsed.model_name == "logistic_regression"
    assert parsed.row_count == 2_400
    assert parsed.score_histogram
    assert sum(bucket.count for bucket in parsed.score_histogram) == parsed.row_count


def test_curve_and_confusion_endpoints_return_saved_metrics_payloads(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
    app = create_app(settings)

    with TestClient(app) as client:
        roc_response = client.get("/api/roc-data")
        pr_response = client.get("/api/pr-curve")
        calibration_response = client.get("/api/calibration-curve")
        confusion_response = client.get("/api/confusion-matrix")

    assert roc_response.status_code == 200
    roc_parsed = RocCurveResponse.model_validate(roc_response.json())
    assert roc_parsed.root
    assert roc_parsed.root[0].split == "test_months_11_12"
    assert roc_parsed.root[0].points

    assert pr_response.status_code == 200
    pr_parsed = PrecisionRecallResponse.model_validate(pr_response.json())
    assert pr_parsed.root
    assert pr_parsed.root[0].points

    assert calibration_response.status_code == 200
    calibration_parsed = CalibrationCurveResponse.model_validate(
        calibration_response.json()
    )
    assert calibration_parsed.root
    assert calibration_parsed.root[0].points[0].count >= 1

    assert confusion_response.status_code == 200
    confusion_parsed = ConfusionMatrixResponse.model_validate(confusion_response.json())
    assert confusion_parsed.root
    assert confusion_parsed.root[0].threshold >= 0.0
    assert any(
        item.model_name == "logistic_regression" for item in confusion_parsed.root
    )


def test_model_stats_endpoint_returns_structured_503_when_metrics_are_missing(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
    (trained_model_dir / "models" / "reports" / "metrics.json").unlink()
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/model-stats")

    assert response.status_code == 503
    parsed = ErrorResponse.model_validate(response.json())
    assert parsed.error.code == "ARTIFACTS_NOT_READY"
    assert parsed.error.details["missing_artifacts"] == ["metrics"]


def test_baseline_comparison_endpoint_returns_structured_503_when_baselines_are_missing(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
    (trained_model_dir / "models" / "reports" / "baseline_metrics.json").unlink()
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/baseline-comparison")

    assert response.status_code == 503
    parsed = ErrorResponse.model_validate(response.json())
    assert parsed.error.code == "ARTIFACTS_NOT_READY"
    assert parsed.error.details["missing_artifacts"] == ["baseline_metrics"]


def test_governance_report_endpoints_return_structured_503_when_reports_are_missing(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
    (trained_model_dir / "models" / "reports" / "fairness_report.json").unlink()
    (trained_model_dir / "models" / "reports" / "psi_report.json").unlink()
    (trained_model_dir / "models" / "reports" / "global_importance.json").unlink()
    app = create_app(settings)

    with TestClient(app) as client:
        fairness_response = client.get("/api/fairness-report")
        drift_response = client.get("/api/drift-report")
        global_importance_response = client.get("/api/global-importance")

    for response, artifact_key in (
        (fairness_response, "fairness_report"),
        (drift_response, "psi_report"),
        (global_importance_response, "global_importance"),
    ):
        assert response.status_code == 503
        parsed = ErrorResponse.model_validate(response.json())
        assert parsed.error.code == "ARTIFACTS_NOT_READY"
        assert parsed.error.details["missing_artifacts"] == [artifact_key]


def test_score_distribution_endpoint_returns_structured_503_when_percentiles_are_missing(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
    (trained_model_dir / "models" / "reports" / "population_percentiles.json").unlink()
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/score-distribution")

    assert response.status_code == 503
    parsed = ErrorResponse.model_validate(response.json())
    assert parsed.error.code == "ARTIFACTS_NOT_READY"
    assert parsed.error.details["missing_artifacts"] == ["population_percentiles"]


def test_curve_and_confusion_endpoints_return_structured_503_when_metrics_are_missing(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
    (trained_model_dir / "models" / "reports" / "metrics.json").unlink()
    app = create_app(settings)

    with TestClient(app) as client:
        roc_response = client.get("/api/roc-data")
        pr_response = client.get("/api/pr-curve")
        calibration_response = client.get("/api/calibration-curve")
        confusion_response = client.get("/api/confusion-matrix")

    for response in (
        roc_response,
        pr_response,
        calibration_response,
        confusion_response,
    ):
        assert response.status_code == 503
        parsed = ErrorResponse.model_validate(response.json())
        assert parsed.error.code == "ARTIFACTS_NOT_READY"
        assert parsed.error.details["missing_artifacts"] == ["metrics"]


def test_curve_endpoint_returns_structured_500_when_saved_payload_is_invalid(
    trained_model_dir,
) -> None:
    settings = build_runtime_settings(trained_model_dir)
    metrics_path = trained_model_dir / "models" / "reports" / "metrics.json"
    metrics_payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    del metrics_payload["evaluation_details"]["test_months_11_12"][
        "logistic_regression"
    ]["model_type"]
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/roc-data")

    assert response.status_code == 500
    parsed = ErrorResponse.model_validate(response.json())
    assert parsed.error.code == "ANALYTICS_PAYLOAD_INVALID"
    assert parsed.error.details["artifact"] == "metrics"
