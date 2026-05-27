import json

import numpy as np
import pytest

from backend.ml.data_generation.generator import generate_synthetic_dataset
from backend.ml.inference.score_mapper import compute_percentile
from backend.ml.training.classical.baselines import train_baselines

pytestmark = pytest.mark.slow


def test_train_baselines_persists_finite_evaluation_and_percentile_artifacts(
    tmp_path,
) -> None:
    artifacts = train_baselines(
        generate_synthetic_dataset(row_count=1_200, seed=41),
        expected_row_count=1_200,
        minimum_test_rows=150,
        preprocessor_artifact_path=tmp_path / "preprocessor.pkl",
        text_pca_artifact_path=tmp_path / "text_pca.pkl",
        logistic_artifact_path=tmp_path / "logistic_best.pkl",
        baseline_metrics_path=tmp_path / "baseline_metrics.json",
        metrics_path=tmp_path / "metrics.json",
        population_percentiles_path=tmp_path / "population_percentiles.json",
    )

    metrics_payload = json.loads(artifacts.metrics_path.read_text(encoding="utf-8"))
    population_percentiles = json.loads(
        artifacts.population_percentiles_path.read_text(encoding="utf-8")
    )
    logistic_test_details = metrics_payload["evaluation_details"]["test_months_11_12"][
        "logistic_regression"
    ]
    confusion_matrix = logistic_test_details["confusion_matrix"]

    assert metrics_payload["evaluation_details"]["validation_months_9_10"][
        "logistic_regression"
    ]["roc_curve"]
    assert logistic_test_details["roc_curve"]
    assert logistic_test_details["pr_curve"]
    assert logistic_test_details["calibration_curve"]
    assert np.isfinite(
        [point["fpr"] for point in logistic_test_details["roc_curve"]]
    ).all()
    assert np.isfinite(
        [point["tpr"] for point in logistic_test_details["roc_curve"]]
    ).all()
    assert (
        confusion_matrix["tp"]
        + confusion_matrix["fp"]
        + confusion_matrix["fn"]
        + confusion_matrix["tn"]
        == metrics_payload["split_row_counts"]["test"]
    )

    assert population_percentiles["default_model_name"] == "logistic_regression"
    assert population_percentiles["model_name"] == "logistic_regression"
    assert population_percentiles["scores"][0] == 300
    assert population_percentiles["scores"][-1] == 850
    assert all(
        left <= right
        for left, right in zip(
            population_percentiles["percentiles"],
            population_percentiles["percentiles"][1:],
        )
    )
    assert (
        sum(bucket["count"] for bucket in population_percentiles["score_histogram"])
        == 1_200
    )
    assert 0 <= compute_percentile(560, population_percentiles) <= 100
