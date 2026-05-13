import json

from backend.ml.data_generation.artifacts import materialize_synthetic_dataset
from backend.ml.data_generation.generator import generate_synthetic_dataset
from backend.ml.training.classical.baselines import (
    BASELINE_MODEL_ORDER,
    train_baselines,
)


def test_materialize_synthetic_dataset_saves_csv_and_validation_summary(tmp_path) -> None:
    artifacts = materialize_synthetic_dataset(
        row_count=2_400,
        seed=7,
        dataset_path=tmp_path / "synthetic_dataset.csv",
        validation_summary_path=tmp_path / "validation_summary.json",
        minimum_test_rows=300,
    )

    summary = json.loads(artifacts.validation_summary_path.read_text(encoding="utf-8"))
    reloaded_dataset = artifacts.dataset_path.read_text(encoding="utf-8")

    assert artifacts.dataset_path.is_file()
    assert artifacts.validation_summary_path.is_file()
    assert "repayment_label" in reloaded_dataset
    assert summary["row_count"] == 2_400
    assert summary["months_11_12_rows"] >= 300
    assert sum(summary["split_row_counts"].values()) == 2_400
    assert summary["feature_list_checks"]["protected_attributes_excluded_from_model_features"] is True
    assert "numeracy_score" in summary["numeric_feature_stats"]
    assert "device_type_mobile" in summary["categorical_feature_label_correlations"]


def test_train_baselines_saves_preprocessor_model_and_metrics_artifacts(tmp_path) -> None:
    dataset = generate_synthetic_dataset(row_count=2_400, seed=13)

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
    )

    baseline_metrics = json.loads(artifacts.baseline_metrics_path.read_text(encoding="utf-8"))
    metrics_payload = json.loads(artifacts.metrics_path.read_text(encoding="utf-8"))
    population_percentiles = json.loads(
        artifacts.population_percentiles_path.read_text(encoding="utf-8")
    )

    assert artifacts.preprocessor_path.is_file()
    assert artifacts.text_pca_path.is_file()
    assert artifacts.logistic_model_path.is_file()
    assert artifacts.baseline_metrics_path.is_file()
    assert artifacts.metrics_path.is_file()
    assert artifacts.population_percentiles_path.is_file()
    assert [item["model_name"] for item in baseline_metrics] == list(BASELINE_MODEL_ORDER)
    assert baseline_metrics[0]["auc_roc"] == 0.5
    assert baseline_metrics[1]["auc_roc"] > baseline_metrics[0]["auc_roc"]
    assert baseline_metrics[2]["lift_vs_loan_officer"] == 0.0
    assert metrics_payload["run_id"] == artifacts.run_id
    assert len(metrics_payload["model_stats"]) == 3
    assert metrics_payload["baselines"][1]["model_name"] == "logistic_regression"
    assert "evaluation_details" in metrics_payload
    assert (
        metrics_payload["evaluation_details"]["test_months_11_12"]["logistic_regression"][
            "confusion_matrix"
        ]["threshold"]
        >= 0.0
    )
    assert population_percentiles["default_model_name"] == "logistic_regression"
    assert population_percentiles["models"]["logistic_regression"]["row_count"] == 2_400
    assert population_percentiles["score_histogram"]


def test_train_baselines_supports_persisted_dataset_path_without_raw_text_column(
    tmp_path,
) -> None:
    dataset_path = tmp_path / "synthetic_dataset.csv"
    dataset = generate_synthetic_dataset(row_count=1_200, seed=19).drop(
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
    )

    assert artifacts.dataset_path == dataset_path
    assert artifacts.text_pca_path.is_file()
    assert artifacts.population_percentiles_path.is_file()
