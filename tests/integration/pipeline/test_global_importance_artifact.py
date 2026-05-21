import json

import numpy as np

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.app.core.settings import load_settings
from backend.app.schemas.analytics import GlobalImportanceResponse
from backend.ml.data_generation.generator import generate_synthetic_dataset
from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    PROTECTED_FEATURES,
    TARGET,
    TEMPORAL_METADATA,
)
from backend.ml.training.classical.baselines import train_baselines
from backend.ml.training.classical.train_classical import train_classical_models


def test_train_baselines_persists_global_importance_report_for_canonical_model_inputs(
    tmp_path,
) -> None:
    dataset = generate_synthetic_dataset(row_count=2_400, seed=37)

    artifacts = train_baselines(
        dataset,
        expected_row_count=2_400,
        minimum_test_rows=300,
        preprocessor_artifact_path=tmp_path / "preprocessor.pkl",
        text_pca_artifact_path=tmp_path / "text_pca.pkl",
        logistic_artifact_path=tmp_path / "logistic_best.pkl",
        baseline_metrics_path=tmp_path / "baseline_metrics.json",
        metrics_path=tmp_path / "metrics.json",
        population_percentiles_path=tmp_path / "population_percentiles.json",
        psi_report_path=tmp_path / "psi_report.json",
        fairness_report_path=tmp_path / "fairness_report.json",
        global_importance_path=tmp_path / "global_importance.json",
        dice_explainer_path=tmp_path / "dice_explainer.pkl",
    )

    report = GlobalImportanceResponse.model_validate(
        json.loads(artifacts.global_importance_path.read_text(encoding="utf-8"))
    )
    feature_names = [row.feature for row in report.items]
    importance_values = np.asarray(
        [row.mean_abs_shap for row in report.items],
        dtype=float,
    )
    excluded_features = set(PROTECTED_FEATURES) | set(TEMPORAL_METADATA) | {TARGET}

    assert artifacts.global_importance_path.is_file()
    assert report.model_name == "logistic_regression"
    assert report.model_type == "classical"
    assert set(feature_names) == set(ALL_MODEL_FEATURES)
    assert len(feature_names) == len(ALL_MODEL_FEATURES)
    assert excluded_features.isdisjoint(feature_names)
    assert np.isfinite(importance_values).all()
    assert np.all(importance_values >= 0.0)
    assert np.any(importance_values > 0.0)
    assert importance_values.tolist() == sorted(importance_values.tolist(), reverse=True)
    assert [row.rank for row in report.items] == list(range(1, len(report.items) + 1))
    assert {row.category for row in report.items} == {
        "psychometric",
        "behavioral",
        "nlp",
        "derived",
    }


def test_train_baselines_supports_persisted_dataset_path_without_raw_text_for_global_importance(
    tmp_path,
) -> None:
    dataset_path = tmp_path / "synthetic_dataset.csv"
    dataset = generate_synthetic_dataset(row_count=1_200, seed=71).drop(
        columns=["q27_resilience_text"]
    )
    dataset.to_csv(dataset_path, index=False)

    artifacts = train_baselines(
        dataset_path=dataset_path,
        expected_row_count=1_200,
        minimum_test_rows=150,
        preprocessor_artifact_path=tmp_path / "preprocessor.pkl",
        text_pca_artifact_path=tmp_path / "text_pca.pkl",
        logistic_artifact_path=tmp_path / "logistic_best.pkl",
        baseline_metrics_path=tmp_path / "baseline_metrics.json",
        metrics_path=tmp_path / "metrics.json",
        population_percentiles_path=tmp_path / "population_percentiles.json",
        psi_report_path=tmp_path / "psi_report.json",
        fairness_report_path=tmp_path / "fairness_report.json",
        global_importance_path=tmp_path / "global_importance.json",
        dice_explainer_path=tmp_path / "dice_explainer.pkl",
    )

    report = GlobalImportanceResponse.model_validate(
        json.loads(artifacts.global_importance_path.read_text(encoding="utf-8"))
    )

    assert artifacts.dataset_path == dataset_path
    assert artifacts.text_pca_path.is_file()
    assert artifacts.global_importance_path.is_file()
    assert len(report.items) == len(ALL_MODEL_FEATURES)


def test_train_classical_models_persists_global_importance_and_runtime_loading_still_succeeds(
    tmp_path,
) -> None:
    dataset = generate_synthetic_dataset(row_count=2_400, seed=73)
    model_root = tmp_path / "models"

    baseline_artifacts = train_baselines(
        dataset,
        expected_row_count=2_400,
        minimum_test_rows=300,
        preprocessor_artifact_path=model_root / "preprocessors" / "preprocessor.pkl",
        text_pca_artifact_path=model_root / "preprocessors" / "text_pca.pkl",
        logistic_artifact_path=model_root / "artifacts" / "logistic_best.pkl",
        baseline_metrics_path=model_root / "reports" / "baseline_metrics.json",
        metrics_path=model_root / "reports" / "metrics.json",
        population_percentiles_path=model_root / "reports" / "population_percentiles.json",
        psi_report_path=model_root / "reports" / "psi_report.json",
        fairness_report_path=model_root / "reports" / "fairness_report.json",
        global_importance_path=model_root / "reports" / "global_importance.json",
        dice_explainer_path=model_root / "explainers" / "dice_explainer.pkl",
    )
    artifacts = train_classical_models(
        dataset,
        expected_row_count=2_400,
        minimum_test_rows=300,
        preprocessor_artifact_path=model_root / "preprocessors" / "preprocessor.pkl",
        text_pca_artifact_path=model_root / "preprocessors" / "text_pca.pkl",
        random_forest_artifact_path=model_root / "artifacts" / "rf_best.pkl",
        xgboost_artifact_path=model_root / "artifacts" / "xgb_best.pkl",
        lightgbm_artifact_path=model_root / "artifacts" / "lgbm_best.pkl",
        logistic_artifact_path=baseline_artifacts.logistic_model_path,
        baseline_metrics_path=baseline_artifacts.baseline_metrics_path,
        metrics_path=baseline_artifacts.metrics_path,
        population_percentiles_path=baseline_artifacts.population_percentiles_path,
        global_importance_path=baseline_artifacts.global_importance_path, psi_report_path=None, fairness_report_path=None, dice_explainer_path=None,
        random_state=17,
    )

    report = GlobalImportanceResponse.model_validate(
        json.loads(artifacts.global_importance_path.read_text(encoding="utf-8"))
    )
    metrics_payload = json.loads(artifacts.metrics_path.read_text(encoding="utf-8"))
    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
            "ALTERSCORE_RUNTIME_MODEL_PATH": "models/artifacts/logistic_best.pkl",
        }
    )
    bundle = load_runtime_artifact_bundle(settings, strict=True)

    assert artifacts.global_importance_path.is_file()
    assert report.items[0].mean_abs_shap >= report.items[-1].mean_abs_shap
    assert report.model_name == _best_supported_model_name(metrics_payload["model_stats"])
    assert bundle.report.scoring_ready is True
    assert "global_importance" in bundle.report.artifacts_loaded


def _best_supported_model_name(model_stats: list[dict[str, object]]) -> str:
    supported_model_names = {
        "logistic_regression",
        "random_forest",
        "xgboost",
        "lightgbm",
    }
    best_model_name = ""
    best_auc = float("-inf")
    for row in model_stats:
        if row["split"] != "test_months_11_12":
            continue
        if row["model_name"] not in supported_model_names:
            continue
        auc_roc = float(row["auc_roc"])
        if auc_roc > best_auc:
            best_model_name = str(row["model_name"])
            best_auc = auc_roc
    return best_model_name
