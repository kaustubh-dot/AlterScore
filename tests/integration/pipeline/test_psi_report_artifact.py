import json

import numpy as np

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.app.core.settings import load_settings
from backend.ml.data_generation.generator import generate_synthetic_dataset
from backend.ml.evaluation.drift import PSI_THRESHOLDS
from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    PROTECTED_FEATURES,
    TARGET,
    TEMPORAL_METADATA,
)
from backend.ml.training.classical.baselines import train_baselines
from backend.ml.training.classical.train_classical import train_classical_models


def test_train_baselines_persists_sorted_psi_report_for_canonical_model_inputs(
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
    )

    psi_report = json.loads(artifacts.psi_report_path.read_text(encoding="utf-8"))
    all_features = psi_report["all_features"]
    top_drifted_features = psi_report["top_drifted_features"]
    feature_names = [row["feature"] for row in all_features]
    psi_values = np.asarray([row["psi"] for row in all_features], dtype=float)
    excluded_features = set(PROTECTED_FEATURES) | set(TEMPORAL_METADATA) | {TARGET}

    assert artifacts.psi_report_path.is_file()
    assert set(feature_names) == set(ALL_MODEL_FEATURES)
    assert len(feature_names) == len(ALL_MODEL_FEATURES)
    assert excluded_features.isdisjoint(feature_names)
    assert psi_report["thresholds"] == PSI_THRESHOLDS
    assert np.isfinite(psi_values).all()
    assert np.all(psi_values >= 0.0)
    assert psi_values.tolist() == sorted(psi_values.tolist(), reverse=True)
    assert top_drifted_features == all_features[: len(top_drifted_features)]
    assert psi_report["max_psi"] == max(row["psi"] for row in all_features)
    assert psi_report["verdict"] == _expected_verdict(
        psi_report["max_psi"],
        psi_report["thresholds"],
    )


def test_train_baselines_supports_persisted_dataset_path_without_raw_text_for_psi_report(
    tmp_path,
) -> None:
    dataset_path = tmp_path / "synthetic_dataset.csv"
    dataset = generate_synthetic_dataset(row_count=1_200, seed=41).drop(
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
    )

    psi_report = json.loads(artifacts.psi_report_path.read_text(encoding="utf-8"))

    assert artifacts.dataset_path == dataset_path
    assert artifacts.text_pca_path.is_file()
    assert artifacts.psi_report_path.is_file()
    assert len(psi_report["all_features"]) == len(ALL_MODEL_FEATURES)


def test_runtime_bundle_loading_still_succeeds_when_psi_report_is_present(
    tmp_path,
) -> None:
    dataset = generate_synthetic_dataset(row_count=2_400, seed=43)
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
    )
    train_classical_models(
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
        psi_report_path=baseline_artifacts.psi_report_path,
        random_state=17,
    )

    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
            "ALTERSCORE_RUNTIME_MODEL_PATH": "models/artifacts/logistic_best.pkl",
        }
    )
    bundle = load_runtime_artifact_bundle(settings, strict=True)

    assert bundle.report.scoring_ready is True
    assert "psi_report" in bundle.report.artifacts_loaded


def _expected_verdict(max_psi: float, thresholds: dict[str, float]) -> str:
    if max_psi >= thresholds["alert_at_or_above"]:
        return "alert"
    if max_psi >= thresholds["stable_below"]:
        return "watch"
    return "stable"
