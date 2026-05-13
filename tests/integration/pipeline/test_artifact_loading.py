import json
from pathlib import Path

from backend.app.core.artifact_loader import (
    inspect_runtime_artifacts,
    load_runtime_artifact_bundle,
)
from backend.app.core.settings import load_settings
from backend.app.services.scoring import score_request_with_bundle
from backend.ml.data_generation.generator import generate_synthetic_dataset
from backend.ml.training.classical.baselines import train_baselines
from backend.ml.training.classical.train_classical import train_classical_models


def test_load_runtime_artifact_bundle_supports_manifest_backed_scoring_bundle(
    tmp_path,
) -> None:
    artifact_paths = _prepare_runtime_bundle(tmp_path)
    manifest_path = tmp_path / "models" / "registry" / "production_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "artifacts": {
                    "model": "models/artifacts/logistic_best.pkl",
                    "preprocessor": "models/preprocessors/preprocessor.pkl",
                    "text_pca": "models/preprocessors/text_pca.pkl",
                    "metrics": "models/reports/metrics.json",
                    "baseline_metrics": "models/reports/baseline_metrics.json",
                    "percentiles": "models/reports/population_percentiles.json",
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
            "ALTERSCORE_MODEL_MANIFEST": "models/registry/production_manifest.json",
        }
    )
    bundle = load_runtime_artifact_bundle(settings, strict=True)

    assert bundle.report.source == "manifest"
    assert bundle.report.runtime_model_name == "logistic_regression"
    assert bundle.report.scoring_ready is True
    assert bundle.report.runtime_model_path == artifact_paths["model"]
    assert "production_manifest" in bundle.report.artifacts_loaded
    assert "text_pca" in bundle.report.artifacts_loaded
    assert bundle.metrics_payload is not None
    assert bundle.baseline_metrics is not None
    assert bundle.text_pca is not None


def test_candidate_runtime_selection_honors_repo_root_and_prefers_best_available_model(
    tmp_path,
) -> None:
    artifact_paths = _prepare_runtime_bundle(tmp_path, train_classical_suite=True)
    settings = load_settings({"ALTERSCORE_REPO_ROOT": str(tmp_path)})

    report = inspect_runtime_artifacts(settings)
    metrics_payload = json.loads(artifact_paths["metrics"].read_text(encoding="utf-8"))
    expected_model_name = max(
        [
            row
            for row in metrics_payload["model_stats"]
            if row["split"] == "test_months_11_12"
            and row["model_name"]
            in {"logistic_regression", "random_forest", "xgboost", "lightgbm"}
        ],
        key=lambda row: row["auc_roc"],
    )["model_name"]

    assert report.source == "candidate"
    assert report.runtime_model_name == expected_model_name
    assert report.runtime_model_path.parent == tmp_path / "models" / "artifacts"
    assert report.scoring_ready is True


def test_score_request_with_loaded_bundle_returns_schema_valid_stub_response(
    tmp_path,
) -> None:
    _prepare_runtime_bundle(tmp_path)
    fixture_payload = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "score_request_valid.json"
        ).read_text(encoding="utf-8")
    )

    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
            "ALTERSCORE_RUNTIME_MODEL_PATH": "models/artifacts/logistic_best.pkl",
        }
    )
    bundle = load_runtime_artifact_bundle(settings, strict=True)
    response = score_request_with_bundle(fixture_payload, bundle)

    assert bundle.report.source == "runtime_model_path"
    assert response.session_id
    assert 300 <= response.credit_score <= 850
    assert response.risk_band in {"poor", "fair", "good", "excellent"}
    assert 0.0 <= response.repayment_probability <= 1.0
    assert 0 <= response.percentile <= 100
    assert response.explanation == []
    assert response.counterfactual_actions == []
    assert response.loan_eligibility.band == response.risk_band
    assert response.improvement_tips


def _prepare_runtime_bundle(tmp_path, *, train_classical_suite: bool = False):
    dataset = generate_synthetic_dataset(row_count=2_400, seed=31)
    model_root = tmp_path / "models"
    artifact_paths = {
        "preprocessor": model_root / "preprocessors" / "preprocessor.pkl",
        "text_pca": model_root / "preprocessors" / "text_pca.pkl",
        "model": model_root / "artifacts" / "logistic_best.pkl",
        "random_forest": model_root / "artifacts" / "rf_best.pkl",
        "xgboost": model_root / "artifacts" / "xgb_best.pkl",
        "lightgbm": model_root / "artifacts" / "lgbm_best.pkl",
        "baseline_metrics": model_root / "reports" / "baseline_metrics.json",
        "metrics": model_root / "reports" / "metrics.json",
        "population_percentiles": model_root / "reports" / "population_percentiles.json",
    }

    train_baselines(
        dataset,
        expected_row_count=2_400,
        minimum_test_rows=300,
        preprocessor_artifact_path=artifact_paths["preprocessor"],
        text_pca_artifact_path=artifact_paths["text_pca"],
        logistic_artifact_path=artifact_paths["model"],
        baseline_metrics_path=artifact_paths["baseline_metrics"],
        metrics_path=artifact_paths["metrics"],
    )
    if train_classical_suite:
        train_classical_models(
            dataset,
            expected_row_count=2_400,
            minimum_test_rows=300,
            preprocessor_artifact_path=artifact_paths["preprocessor"],
            text_pca_artifact_path=artifact_paths["text_pca"],
            random_forest_artifact_path=artifact_paths["random_forest"],
            xgboost_artifact_path=artifact_paths["xgboost"],
            lightgbm_artifact_path=artifact_paths["lightgbm"],
            baseline_metrics_path=artifact_paths["baseline_metrics"],
            metrics_path=artifact_paths["metrics"],
            random_state=17,
        )
    artifact_paths["population_percentiles"].write_text(
        json.dumps(
            {
                "score_to_percentile": {
                    "300": 0,
                    "560": 50,
                    "850": 100,
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return artifact_paths
