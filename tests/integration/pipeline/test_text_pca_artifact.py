import json
from pathlib import Path

import joblib
import numpy as np
import pytest

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.app.core.settings import load_settings
from backend.app.services.scoring import score_request_with_bundle
from backend.ml.data_generation.generator import (
    TEMPORAL_SPLIT_MONTHS,
    generate_synthetic_dataset,
)
from backend.ml.inference.feature_assembly import assemble_request_features
from backend.ml.preprocessing.pipeline import build_text_embedding_matrix
from backend.ml.training.classical.baselines import train_baselines

pytestmark = pytest.mark.slow


def test_train_baselines_persists_text_pca_from_train_months_only(tmp_path) -> None:
    dataset = generate_synthetic_dataset(row_count=1_200, seed=41)
    artifact_paths = _build_training_artifact_paths(tmp_path)

    artifacts = train_baselines(
        dataset,
        expected_row_count=1_200,
        minimum_test_rows=200,
        preprocessor_artifact_path=artifact_paths["preprocessor"],
        text_pca_artifact_path=artifact_paths["text_pca"],
        logistic_artifact_path=artifact_paths["model"],
        baseline_metrics_path=artifact_paths["baseline_metrics"],
        metrics_path=artifact_paths["metrics"],
        population_percentiles_path=artifact_paths["population_percentiles"],
        psi_report_path=artifact_paths["psi_report"],
        fairness_report_path=artifact_paths["fairness_report"],
        global_importance_path=artifact_paths["global_importance"],
        dice_explainer_path=artifact_paths["dice_explainer"],
        random_state=17,
    )

    raw_embeddings = build_text_embedding_matrix(dataset)
    loaded_text_pca = joblib.load(artifacts.text_pca_path)
    train_mask = dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["train"]).to_numpy()
    validation_mask = (
        dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["validation"]).to_numpy()
    )
    test_mask = dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["test"]).to_numpy()

    assert artifacts.text_pca_path.is_file()
    np.testing.assert_allclose(
        loaded_text_pca.mean_,
        raw_embeddings[train_mask].mean(axis=0),
    )
    assert not np.allclose(loaded_text_pca.mean_, raw_embeddings.mean(axis=0))

    validation_projection = loaded_text_pca.transform(raw_embeddings[validation_mask])
    test_projection = loaded_text_pca.transform(raw_embeddings[test_mask])

    assert validation_projection.shape == (int(validation_mask.sum()), 2)
    assert test_projection.shape == (int(test_mask.sum()), 2)
    assert np.isfinite(validation_projection).all()
    assert np.isfinite(test_projection).all()


def test_runtime_feature_assembly_uses_persisted_text_pca_for_non_zero_semantics(
    tmp_path,
) -> None:
    bundle = _prepare_runtime_bundle(tmp_path, include_text_pca=True)
    payload = _load_valid_score_payload()

    assembled = assemble_request_features(
        payload,
        text_pca=bundle.text_pca,
        require_text_pca=True,
    )
    semantic_projection = np.array(
        [
            assembled.nlp_features["text_semantic_dim1"],
            assembled.nlp_features["text_semantic_dim2"],
        ],
        dtype=float,
    )

    np.testing.assert_allclose(
        semantic_projection,
        bundle.text_pca.transform(assembled.raw_embedding.reshape(1, -1))[0],
    )
    assert np.isfinite(semantic_projection).all()
    assert not np.allclose(semantic_projection, 0.0)


def test_runtime_feature_assembly_zero_fills_when_text_pca_is_intentionally_omitted() -> (
    None
):
    assembled = assemble_request_features(
        _load_valid_score_payload(),
        text_pca=None,
        require_text_pca=False,
    )

    assert assembled.nlp_features["text_semantic_dim1"] == 0.0
    assert assembled.nlp_features["text_semantic_dim2"] == 0.0


def test_artifact_loader_succeeds_when_runtime_bundle_includes_text_pca(
    tmp_path,
) -> None:
    bundle = _prepare_runtime_bundle(tmp_path, include_text_pca=True)
    response = score_request_with_bundle(_load_valid_score_payload(), bundle)

    assert bundle.text_pca is not None
    assert bundle.report.scoring_ready is True
    assert "text_pca" in bundle.report.artifacts_loaded
    assert 300 <= response.credit_score <= 850
    assert 0.0 <= response.repayment_probability <= 1.0


def _prepare_runtime_bundle(tmp_path, *, include_text_pca: bool):
    artifact_paths = _build_training_artifact_paths(tmp_path)
    dataset = generate_synthetic_dataset(row_count=1_200, seed=53)

    train_baselines(
        dataset,
        expected_row_count=1_200,
        minimum_test_rows=200,
        preprocessor_artifact_path=artifact_paths["preprocessor"],
        text_pca_artifact_path=artifact_paths["text_pca"] if include_text_pca else None,
        logistic_artifact_path=artifact_paths["model"],
        baseline_metrics_path=artifact_paths["baseline_metrics"],
        metrics_path=artifact_paths["metrics"],
        population_percentiles_path=artifact_paths["population_percentiles"],
        psi_report_path=artifact_paths["psi_report"],
        fairness_report_path=artifact_paths["fairness_report"],
        global_importance_path=artifact_paths["global_importance"],
        dice_explainer_path=artifact_paths["dice_explainer"],
        random_state=23,
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

    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
            "ALTERSCORE_RUNTIME_MODEL_PATH": "models/artifacts/logistic_best.pkl",
        }
    )
    return load_runtime_artifact_bundle(settings, strict=True)


def _build_training_artifact_paths(tmp_path) -> dict[str, Path]:
    model_root = tmp_path / "models"
    return {
        "preprocessor": model_root / "preprocessors" / "preprocessor.pkl",
        "text_pca": model_root / "preprocessors" / "text_pca.pkl",
        "model": model_root / "artifacts" / "logistic_best.pkl",
        "baseline_metrics": model_root / "reports" / "baseline_metrics.json",
        "metrics": model_root / "reports" / "metrics.json",
        "population_percentiles": model_root
        / "reports"
        / "population_percentiles.json",
        "psi_report": model_root / "reports" / "psi_report.json",
        "fairness_report": model_root / "reports" / "fairness_report.json",
        "global_importance": model_root / "reports" / "global_importance.json",
        "dice_explainer": model_root / "explainers" / "dice_explainer.pkl",
    }


def _load_valid_score_payload() -> dict:
    return json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "score_request_valid.json"
        ).read_text(encoding="utf-8")
    )
