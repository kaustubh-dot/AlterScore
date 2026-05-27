import pytest
pytestmark = pytest.mark.slow

import json

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.app.core.settings import load_settings
from backend.app.schemas.analytics import FairnessReport
from backend.ml.data_generation.generator import generate_synthetic_dataset
from backend.ml.preprocessing.feature_registry import PROTECTED_FEATURES
from backend.ml.training.classical.baselines import train_baselines
from backend.ml.training.classical.train_classical import train_classical_models


def test_train_baselines_persists_fairness_report_with_guarded_subgroup_metrics(
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

    report = FairnessReport.model_validate(
        json.loads(artifacts.fairness_report_path.read_text(encoding="utf-8"))
    )
    subgroup_rows = [
        (attribute_name, group_name, group_metrics)
        for attribute_name, group_payload in report.groups.items()
        for group_name, group_metrics in group_payload.items()
    ]
    expected_flagged_groups = sorted(
        f"{attribute_name}={group_name}"
        for attribute_name, group_name, group_metrics in subgroup_rows
        if group_metrics.flag != "green"
    )

    assert artifacts.fairness_report_path.is_file()
    assert set(report.groups) == set(PROTECTED_FEATURES)
    assert report.calibration_parity is not None
    assert report.individual_fairness_proxy is not None
    assert subgroup_rows
    assert all(group_metrics.n_samples >= 30 for _, _, group_metrics in subgroup_rows)
    assert all(0.0 <= group_metrics.auc <= 1.0 for _, _, group_metrics in subgroup_rows)
    assert all(
        0.0 <= group_metrics.approval_rate <= 1.0
        for _, _, group_metrics in subgroup_rows
    )
    assert all(0.0 <= group_metrics.fpr <= 1.0 for _, _, group_metrics in subgroup_rows)
    assert all(0.0 <= group_metrics.fnr <= 1.0 for _, _, group_metrics in subgroup_rows)
    assert all(
        300.0 <= group_metrics.mean_score <= 850.0
        for _, _, group_metrics in subgroup_rows
    )
    assert report.worst_auc_gap == max(
        [0.0, *[group_metrics.auc_gap_from_overall for _, _, group_metrics in subgroup_rows]]
    )
    assert sorted(report.flagged_groups) == expected_flagged_groups
    assert set(report.calibration_parity.groups) == set(PROTECTED_FEATURES)
    assert report.calibration_parity.evaluated_group_count > 0
    assert report.calibration_parity.max_ece_gap >= 0.0
    assert report.individual_fairness_proxy.evaluated_applicants > 0
    assert report.individual_fairness_proxy.evaluated_pairs > 0
    assert not set(report.individual_fairness_proxy.similarity_feature_set) & set(
        PROTECTED_FEATURES
    )
    if report.flagged_groups:
        assert "requires attention" in report.verdict
    else:
        assert "acceptable fairness" in report.verdict


def test_train_baselines_supports_persisted_dataset_path_without_raw_text_for_fairness(
    tmp_path,
) -> None:
    dataset_path = tmp_path / "synthetic_dataset.csv"
    dataset = generate_synthetic_dataset(row_count=1_200, seed=53).drop(
        columns=["open_response_text"]
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

    report = FairnessReport.model_validate(
        json.loads(artifacts.fairness_report_path.read_text(encoding="utf-8"))
    )

    assert artifacts.dataset_path == dataset_path
    assert artifacts.text_pca_path.is_file()
    assert artifacts.fairness_report_path.is_file()
    assert set(report.groups) == set(PROTECTED_FEATURES)
    assert report.calibration_parity is not None
    assert report.individual_fairness_proxy is not None


def test_train_classical_models_persists_fairness_report_and_runtime_loading_still_succeeds(
    tmp_path,
) -> None:
    dataset = generate_synthetic_dataset(row_count=2_400, seed=59)
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
        psi_report_path=baseline_artifacts.psi_report_path,
        fairness_report_path=baseline_artifacts.fairness_report_path,
        global_importance_path=baseline_artifacts.global_importance_path,
        dice_explainer_path=baseline_artifacts.dice_explainer_path,
        random_state=17,
    )

    report = FairnessReport.model_validate(
        json.loads(artifacts.fairness_report_path.read_text(encoding="utf-8"))
    )
    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
            "ALTERSCORE_RUNTIME_MODEL_PATH": "models/artifacts/logistic_best.pkl",
        }
    )
    bundle = load_runtime_artifact_bundle(settings, strict=True)

    assert artifacts.fairness_report_path.is_file()
    assert report.groups["gender"]
    assert report.calibration_parity is not None
    assert report.individual_fairness_proxy is not None
    assert bundle.report.scoring_ready is True
    assert "fairness_report" in bundle.report.artifacts_loaded
