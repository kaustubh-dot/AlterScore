import pytest
pytestmark = pytest.mark.slow

import json

import numpy as np

from backend.ml.data_generation.generator import generate_synthetic_dataset
from backend.ml.training.classical.baselines import train_baselines
from backend.ml.training.classical.train_classical import (
    CLASSICAL_MODEL_ORDER,
    NUMERIC_METRIC_FIELDS,
    train_classical_models,
)


def test_train_classical_models_saves_artifacts_and_merges_metrics(tmp_path) -> None:
    dataset = generate_synthetic_dataset(row_count=2_400, seed=23)
    baseline_artifacts = train_baselines(
        dataset,
        expected_row_count=2_400,
        minimum_test_rows=300,
        preprocessor_artifact_path=tmp_path / "baseline_preprocessor.pkl",
        text_pca_artifact_path=tmp_path / "baseline_text_pca.pkl",
        logistic_artifact_path=tmp_path / "logistic_best.pkl",
        baseline_metrics_path=tmp_path / "baseline_metrics.json",
        metrics_path=tmp_path / "metrics.json",
        population_percentiles_path=tmp_path / "population_percentiles.json",
    )

    artifacts = train_classical_models(
        dataset,
        expected_row_count=2_400,
        minimum_test_rows=300,
        preprocessor_artifact_path=tmp_path / "preprocessor.pkl",
        text_pca_artifact_path=tmp_path / "text_pca.pkl",
        random_forest_artifact_path=tmp_path / "rf_best.pkl",
        xgboost_artifact_path=tmp_path / "xgb_best.pkl",
        lightgbm_artifact_path=tmp_path / "lgbm_best.pkl",
        logistic_artifact_path=baseline_artifacts.logistic_model_path,
        baseline_metrics_path=baseline_artifacts.baseline_metrics_path,
        metrics_path=baseline_artifacts.metrics_path,
        population_percentiles_path=baseline_artifacts.population_percentiles_path,
        psi_report_path=None, fairness_report_path=None, global_importance_path=None, dice_explainer_path=None,
        random_state=17,
    )

    metrics_payload = json.loads(artifacts.metrics_path.read_text(encoding="utf-8"))
    baseline_metrics = json.loads(
        baseline_artifacts.baseline_metrics_path.read_text(encoding="utf-8")
    )
    population_percentiles = json.loads(
        artifacts.population_percentiles_path.read_text(encoding="utf-8")
    )

    for model_name in CLASSICAL_MODEL_ORDER:
        assert artifacts.model_artifact_paths[model_name].is_file()
        assert np.all(artifacts.validation_probabilities[model_name] >= 0.0)
        assert np.all(artifacts.validation_probabilities[model_name] <= 1.0)
        assert np.all(artifacts.test_probabilities[model_name] >= 0.0)
        assert np.all(artifacts.test_probabilities[model_name] <= 1.0)

    assert artifacts.text_pca_path.is_file()
    assert artifacts.metrics_path.is_file()
    assert artifacts.text_pca_path.is_file()
    assert artifacts.population_percentiles_path.is_file()
    assert metrics_payload["baselines"] == baseline_metrics

    expected_rows = {
        ("random_forest", "validation_months_9_10"),
        ("random_forest", "test_months_11_12"),
        ("xgboost", "validation_months_9_10"),
        ("xgboost", "test_months_11_12"),
        ("lightgbm", "validation_months_9_10"),
        ("lightgbm", "test_months_11_12"),
    }
    observed_rows = {
        (row["model_name"], row["split"]) for row in metrics_payload["model_stats"]
    }
    assert expected_rows.issubset(observed_rows)

    test_rows = [
        row
        for row in metrics_payload["model_stats"]
        if row["model_name"] in CLASSICAL_MODEL_ORDER
        and row["split"] == "test_months_11_12"
    ]
    assert len(test_rows) == len(CLASSICAL_MODEL_ORDER)
    for row in test_rows:
        assert row["model_type"] == "classical"
        assert np.isfinite([row[field_name] for field_name in NUMERIC_METRIC_FIELDS]).all()
        validation_row = next(
            item
            for item in metrics_payload["model_stats"]
            if item["model_name"] == row["model_name"]
            and item["split"] == "validation_months_9_10"
        )
        assert row["threshold"] == validation_row["threshold"]
    assert "evaluation_details" in metrics_payload
    assert "xgboost" in metrics_payload["evaluation_details"]["test_months_11_12"]
    assert "logistic_regression" in population_percentiles["models"]
    assert set(CLASSICAL_MODEL_ORDER).issubset(population_percentiles["models"])
    assert population_percentiles["default_model_name"] in {
        "logistic_regression",
        "random_forest",
        "xgboost",
        "lightgbm",
    }
