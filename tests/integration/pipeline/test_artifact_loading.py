import json
from pathlib import Path
import shutil

import joblib
import numpy as np
import pytest

from backend.app.core.artifact_loader import (
    ArtifactLoadError,
    inspect_runtime_artifacts,
    load_runtime_artifact_bundle,
)
from backend.app.core.settings import load_settings
from backend.ml.registry.production_manifest import (
    MANIFEST_REQUIRED_ARTIFACT_KEYS,
    compute_file_sha256,
    load_production_manifest,
)
from backend.app.services.scoring import score_request_with_bundle
from backend.ml.data_generation.generator import generate_synthetic_dataset
from backend.ml.explainability.dice_explainer import (
    build_default_persisted_dice_explainer,
    save_persisted_dice_explainer,
)
from backend.ml.explainability.shap_explainer import PersistedShapExplainer
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES
from backend.ml.training.classical.baselines import train_baselines
from backend.ml.training.classical.train_classical import train_classical_models


class _DummyPreprocessor:
    def transform(self, frame):
        return np.zeros((len(frame), len(ALL_MODEL_FEATURES)), dtype=float)


class _DummyTextPca:
    def transform(self, embeddings):
        return np.zeros((len(embeddings), 2), dtype=float)


class _FixedProbabilityModel:
    def __init__(self, probability: float) -> None:
        self.probability = probability

    def predict_proba(self, features):
        row_count = np.asarray(features).shape[0]
        probabilities = np.full(row_count, self.probability, dtype=float)
        return np.column_stack([1.0 - probabilities, probabilities])


class _AveragingStackingModel:
    def predict_proba(self, meta_features):
        meta_matrix = np.asarray(meta_features, dtype=float)
        probabilities = np.clip(meta_matrix.mean(axis=1), 0.0, 1.0)
        return np.column_stack([1.0 - probabilities, probabilities])


def test_load_runtime_artifact_bundle_supports_manifest_backed_scoring_bundle(
    tmp_path,
) -> None:
    artifact_paths = _prepare_runtime_bundle(tmp_path, include_shap_explainer=True)
    _write_manifest(tmp_path, artifact_paths)

    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
            "ALTERSCORE_MODEL_MANIFEST": "models/registry/production_manifest.json",
        }
    )
    bundle = load_runtime_artifact_bundle(settings, strict=True)

    assert bundle.report.source == "manifest"
    assert bundle.report.runtime_model_name == "logistic_regression"
    assert bundle.report.manifest_version == "test_local_logistic_bundle_v1"
    assert bundle.report.model_version == "0.1.0"
    assert bundle.report.scoring_ready is True
    assert bundle.report.runtime_model_path == artifact_paths["runtime_model"]
    assert "production_manifest" in bundle.report.artifacts_loaded
    assert set(MANIFEST_REQUIRED_ARTIFACT_KEYS).issubset(bundle.report.artifacts_loaded)
    assert bundle.metrics_payload is not None
    assert bundle.baseline_metrics is not None
    assert bundle.shap_explainer is not None
    assert bundle.dice_explainer is not None
    assert bundle.text_pca is not None
    assert bundle.population_percentiles is not None
    assert bundle.population_percentiles["selected_model_name"] == "logistic_regression"


def test_manifest_runtime_selection_is_preferred_over_candidate_loading_when_manifest_is_present(
    tmp_path,
) -> None:
    artifact_paths = _prepare_runtime_bundle(
        tmp_path,
        train_classical_suite=True,
        include_shap_explainer=True,
    )
    metrics_payload = json.loads(artifact_paths["metrics"].read_text(encoding="utf-8"))
    for row in metrics_payload["model_stats"]:
        if row["split"] != "test_months_11_12":
            continue
        if row["model_name"] == "xgboost":
            row["auc_roc"] = 0.9999
        elif row["model_name"] == "logistic_regression":
            row["auc_roc"] = 0.1
    artifact_paths["metrics"].write_text(
        json.dumps(metrics_payload, indent=2),
        encoding="utf-8",
    )
    _write_manifest(tmp_path, artifact_paths)
    settings = load_settings({"ALTERSCORE_REPO_ROOT": str(tmp_path)})

    report = inspect_runtime_artifacts(settings)
    assert report.source == "manifest"
    assert report.runtime_model_name == "logistic_regression"
    assert report.runtime_model_path == artifact_paths["runtime_model"]
    assert report.scoring_ready is True


def test_score_request_with_loaded_bundle_returns_schema_valid_runtime_response(
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
    assert bundle.dice_explainer is not None
    assert response.session_id
    assert 300 <= response.credit_score <= 850
    assert response.risk_band in {"poor", "fair", "good", "excellent"}
    assert 0.0 <= response.repayment_probability <= 1.0
    assert 0 <= response.percentile <= 100
    assert response.explanation == []
    if response.credit_score < 850:
        assert response.counterfactual_actions
    else:
        assert isinstance(response.counterfactual_actions, list)
    assert all(
        action.estimated_score_gain >= 0 for action in response.counterfactual_actions
    )
    assert response.loan_eligibility.band == response.risk_band
    assert response.improvement_tips


def test_population_percentiles_payload_is_resolved_to_the_active_runtime_model(
    tmp_path,
) -> None:
    artifact_paths = _prepare_runtime_bundle(tmp_path, train_classical_suite=True)
    population_percentiles_path = artifact_paths["population_percentiles"]
    payload = json.loads(population_percentiles_path.read_text(encoding="utf-8"))
    payload["default_model_name"] = "random_forest"
    population_percentiles_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    settings = load_settings(
        {
            "ALTERSCORE_REPO_ROOT": str(tmp_path),
            "ALTERSCORE_RUNTIME_MODEL_PATH": "models/artifacts/logistic_best.pkl",
        }
    )
    bundle = load_runtime_artifact_bundle(settings, strict=True)

    assert bundle.report.runtime_model_name == "logistic_regression"
    assert bundle.population_percentiles is not None
    assert bundle.population_percentiles["selected_model_name"] == "logistic_regression"
    assert bundle.population_percentiles["model_name"] == "logistic_regression"


def test_load_runtime_artifact_bundle_fails_clearly_for_incomplete_manifest(
    tmp_path,
) -> None:
    artifact_paths = _prepare_runtime_bundle(tmp_path, include_shap_explainer=True)
    _write_manifest(
        tmp_path,
        artifact_paths,
        omit_artifacts={"baseline_metrics"},
    )

    settings = load_settings({"ALTERSCORE_REPO_ROOT": str(tmp_path)})

    with pytest.raises(ArtifactLoadError, match="baseline_metrics"):
        load_runtime_artifact_bundle(settings, strict=False)


def test_load_runtime_artifact_bundle_fails_clearly_for_malformed_manifest(
    tmp_path,
) -> None:
    artifact_paths = _prepare_runtime_bundle(tmp_path, include_shap_explainer=True)
    manifest_path = _write_manifest(tmp_path, artifact_paths)
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_payload["artifacts"][
        "runtime_model"
    ] = "models/artifacts/logistic_best.pkl"
    manifest_path.write_text(
        json.dumps(manifest_payload, indent=2),
        encoding="utf-8",
    )

    settings = load_settings({"ALTERSCORE_REPO_ROOT": str(tmp_path)})

    with pytest.raises(ArtifactLoadError, match="runtime_model"):
        load_runtime_artifact_bundle(settings, strict=False)


def test_load_runtime_artifact_bundle_validates_ensemble_dependencies(
    tmp_path,
) -> None:
    _prepare_minimal_ensemble_bundle(tmp_path)
    settings = load_settings({"ALTERSCORE_REPO_ROOT": str(tmp_path)})

    bundle = load_runtime_artifact_bundle(settings, strict=True)

    assert bundle.report.source == "manifest"
    assert bundle.report.runtime_model_type == "ensemble"
    assert bundle.report.scoring_ready is True
    assert "stacking_config" in bundle.report.artifacts_loaded
    assert "base_models" in bundle.report.artifacts_loaded
    assert bundle.base_models is not None
    assert tuple(bundle.base_models) == ("model_a", "model_b")


def test_load_runtime_artifact_bundle_rejects_tampered_ensemble_base_model(
    tmp_path,
) -> None:
    artifact_paths = _prepare_minimal_ensemble_bundle(tmp_path)
    artifact_paths["base_models"]["model_b"].write_text(
        "not-a-valid-model",
        encoding="utf-8",
    )
    settings = load_settings({"ALTERSCORE_REPO_ROOT": str(tmp_path)})

    bundle = load_runtime_artifact_bundle(settings, strict=False)

    assert bundle.report.scoring_ready is False
    assert "base_models" in bundle.report.invalid_artifacts
    assert "base_models" not in bundle.report.artifacts_loaded
    assert "checksum" in bundle.report.artifact_errors["base_models"]
    with pytest.raises(ArtifactLoadError, match="base_models"):
        load_runtime_artifact_bundle(settings, strict=True)


def test_load_runtime_artifact_bundle_rejects_tampered_stacking_config(
    tmp_path,
) -> None:
    artifact_paths = _prepare_minimal_ensemble_bundle(tmp_path)
    artifact_paths["stacking_config"].write_text(
        json.dumps(
            {
                "model_name": "calibrated_stacking",
                "model_type": "ensemble",
                "base_model_order": ["model_a", "model_b"],
                "tampered": True,
            }
        ),
        encoding="utf-8",
    )
    settings = load_settings({"ALTERSCORE_REPO_ROOT": str(tmp_path)})

    bundle = load_runtime_artifact_bundle(settings, strict=False)

    assert bundle.report.scoring_ready is False
    assert "stacking_config" in bundle.report.invalid_artifacts
    assert "stacking_config" not in bundle.report.artifacts_loaded
    assert "checksum" in bundle.report.artifact_errors["stacking_config"]
    with pytest.raises(ArtifactLoadError, match="stacking_config"):
        load_runtime_artifact_bundle(settings, strict=True)


def test_load_runtime_artifact_bundle_rejects_stale_ensemble_base_order(
    tmp_path,
) -> None:
    _prepare_minimal_ensemble_bundle(
        tmp_path,
        base_model_names=("model_a", "model_b"),
        stacking_order=("model_a",),
    )
    settings = load_settings({"ALTERSCORE_REPO_ROOT": str(tmp_path)})

    bundle = load_runtime_artifact_bundle(settings, strict=False)

    assert bundle.report.scoring_ready is False
    assert "base_models" in bundle.report.invalid_artifacts
    assert (
        "must match stacking_config base_model_order"
        in bundle.report.artifact_errors["base_models"]
    )


def test_production_manifest_requires_ensemble_dependency_sections(tmp_path) -> None:
    artifact_paths = _prepare_minimal_ensemble_bundle(tmp_path)
    manifest_path = tmp_path / "models" / "registry" / "production_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload.pop("base_models")
    payload["stacking_config"] = {
        "path": _relative_artifact_path(artifact_paths["stacking_config"], tmp_path),
        "sha256": compute_file_sha256(artifact_paths["stacking_config"]),
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="base_models"):
        load_production_manifest(manifest_path)


def _prepare_runtime_bundle(
    tmp_path,
    *,
    train_classical_suite: bool = False,
    include_shap_explainer: bool = False,
):
    dataset = generate_synthetic_dataset(row_count=2_400, seed=31)
    model_root = tmp_path / "models"
    artifact_paths = {
        "preprocessor": model_root / "preprocessors" / "preprocessor.pkl",
        "text_pca": model_root / "preprocessors" / "text_pca.pkl",
        "runtime_model": model_root / "artifacts" / "logistic_best.pkl",
        "random_forest": model_root / "artifacts" / "rf_best.pkl",
        "xgboost": model_root / "artifacts" / "xgb_best.pkl",
        "lightgbm": model_root / "artifacts" / "lgbm_best.pkl",
        "shap_explainer": model_root / "explainers" / "shap_explainer.pkl",
        "baseline_metrics": model_root / "reports" / "baseline_metrics.json",
        "metrics": model_root / "reports" / "metrics.json",
        "fairness_report": model_root / "reports" / "fairness_report.json",
        "psi_report": model_root / "reports" / "psi_report.json",
        "global_importance": model_root / "reports" / "global_importance.json",
        "population_percentiles": model_root
        / "reports"
        / "population_percentiles.json",
        "dice_explainer": model_root / "explainers" / "dice_explainer.pkl",
    }

    train_baselines(
        dataset,
        expected_row_count=2_400,
        minimum_test_rows=300,
        preprocessor_artifact_path=artifact_paths["preprocessor"],
        text_pca_artifact_path=artifact_paths["text_pca"],
        logistic_artifact_path=artifact_paths["runtime_model"],
        baseline_metrics_path=artifact_paths["baseline_metrics"],
        metrics_path=artifact_paths["metrics"],
        fairness_report_path=artifact_paths["fairness_report"],
        psi_report_path=artifact_paths["psi_report"],
        global_importance_path=artifact_paths["global_importance"],
        population_percentiles_path=artifact_paths["population_percentiles"],
        dice_explainer_path=artifact_paths["dice_explainer"],
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
            logistic_artifact_path=artifact_paths["runtime_model"],
            baseline_metrics_path=artifact_paths["baseline_metrics"],
            metrics_path=artifact_paths["metrics"],
            fairness_report_path=artifact_paths["fairness_report"],
            psi_report_path=artifact_paths["psi_report"],
            global_importance_path=artifact_paths["global_importance"],
            population_percentiles_path=artifact_paths["population_percentiles"],
            dice_explainer_path=artifact_paths["dice_explainer"],
            random_state=17,
        )
    if include_shap_explainer:
        artifact_paths["shap_explainer"].parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            Path(__file__).resolve().parents[3]
            / "archive"
            / "models"
            / "explainers"
            / "shap_explainer.pkl",
            artifact_paths["shap_explainer"],
        )
    return artifact_paths


def _prepare_minimal_ensemble_bundle(
    tmp_path,
    *,
    base_model_names: tuple[str, ...] = ("model_a", "model_b"),
    stacking_order: tuple[str, ...] | None = None,
) -> dict[str, object]:
    model_root = tmp_path / "models"
    artifact_paths = {
        "runtime_model": model_root / "artifacts" / "calibrated_stacking.pkl",
        "preprocessor": model_root / "preprocessors" / "preprocessor.pkl",
        "text_pca": model_root / "preprocessors" / "text_pca.pkl",
        "shap_explainer": model_root / "explainers" / "shap_explainer.pkl",
        "dice_explainer": model_root / "explainers" / "dice_explainer.pkl",
        "metrics": model_root / "reports" / "metrics.json",
        "baseline_metrics": model_root / "reports" / "baseline_metrics.json",
        "fairness_report": model_root / "reports" / "fairness_report.json",
        "psi_report": model_root / "reports" / "psi_report.json",
        "global_importance": model_root / "reports" / "global_importance.json",
        "population_percentiles": model_root
        / "reports"
        / "population_percentiles.json",
        "stacking_config": model_root / "artifacts" / "calibrated_stacking_config.json",
        "base_models": {
            model_name: model_root / "artifacts" / f"{model_name}.pkl"
            for model_name in base_model_names
        },
    }
    for artifact_path in [
        value for key, value in artifact_paths.items() if key != "base_models"
    ]:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
    for artifact_path in artifact_paths["base_models"].values():
        artifact_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(_AveragingStackingModel(), artifact_paths["runtime_model"])
    joblib.dump(_DummyPreprocessor(), artifact_paths["preprocessor"])
    joblib.dump(_DummyTextPca(), artifact_paths["text_pca"])
    joblib.dump(
        PersistedShapExplainer(
            model_name="stacking_ensemble",
            feature_names=tuple(ALL_MODEL_FEATURES),
            background_mean=np.zeros(len(ALL_MODEL_FEATURES), dtype=float),
            background_size=1,
            coefficients=np.zeros(len(ALL_MODEL_FEATURES), dtype=float),
        ),
        artifact_paths["shap_explainer"],
    )
    save_persisted_dice_explainer(
        build_default_persisted_dice_explainer(model_name="stacking_ensemble"),
        artifact_paths["dice_explainer"],
    )
    for index, artifact_path in enumerate(artifact_paths["base_models"].values()):
        joblib.dump(_FixedProbabilityModel(0.4 + index * 0.2), artifact_path)

    artifact_paths["metrics"].write_text(json.dumps({}), encoding="utf-8")
    artifact_paths["baseline_metrics"].write_text(json.dumps([]), encoding="utf-8")
    artifact_paths["fairness_report"].write_text(json.dumps({}), encoding="utf-8")
    artifact_paths["psi_report"].write_text(json.dumps({}), encoding="utf-8")
    artifact_paths["global_importance"].write_text(json.dumps({}), encoding="utf-8")
    artifact_paths["population_percentiles"].write_text(
        json.dumps({}), encoding="utf-8"
    )
    artifact_paths["stacking_config"].write_text(
        json.dumps(
            {
                "model_name": "calibrated_stacking",
                "model_type": "ensemble",
                "base_model_order": list(stacking_order or base_model_names),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_minimal_ensemble_manifest(tmp_path, artifact_paths)
    return artifact_paths


def _write_minimal_ensemble_manifest(
    tmp_path, artifact_paths: dict[str, object]
) -> Path:
    manifest_path = tmp_path / "models" / "registry" / "production_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_entries = {
        artifact_key: {
            "path": _relative_artifact_path(artifact_path, tmp_path),
            "sha256": compute_file_sha256(artifact_path),
        }
        for artifact_key, artifact_path in artifact_paths.items()
        if artifact_key in MANIFEST_REQUIRED_ARTIFACT_KEYS
    }
    base_model_entries = {
        model_name: {
            "path": _relative_artifact_path(artifact_path, tmp_path),
            "sha256": compute_file_sha256(artifact_path),
        }
        for model_name, artifact_path in artifact_paths["base_models"].items()
    }
    manifest_path.write_text(
        json.dumps(
            {
                "manifest_schema_version": "1.0.0",
                "manifest_version": "test_ensemble_bundle_v1",
                "model_version": "0.2.0",
                "run_id": "20260516_095448_ensemble_promotion",
                "created_at": "2026-05-16T09:54:48Z",
                "code_ref": "test-code-ref",
                "data_version": "synthetic_v0.1.0",
                "feature_registry_version": "0.1.0",
                "runtime_model_name": "stacking_ensemble",
                "runtime_model_type": "ensemble",
                "target": "repayment_label",
                "split": {
                    "train": "cohort_month 1-8",
                    "validation": "cohort_month 9-10",
                    "test": "cohort_month 11-12",
                },
                "artifacts": artifact_entries,
                "base_models": base_model_entries,
                "stacking_config": {
                    "path": _relative_artifact_path(
                        artifact_paths["stacking_config"],
                        tmp_path,
                    ),
                    "sha256": compute_file_sha256(artifact_paths["stacking_config"]),
                },
                "metrics_summary": {"test_auc_roc": 0.8},
                "fairness_summary": {"verdict": "acceptable"},
                "drift_summary": {"verdict": "stable"},
                "promotion_status": "promoted",
                "promotion_notes": "Synthetic ensemble manifest for loader tests.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest_path


def _relative_artifact_path(path: Path, repo_root: Path) -> str:
    return str(path.relative_to(repo_root)).replace("\\", "/")


def _write_manifest(
    tmp_path,
    artifact_paths: dict[str, Path],
    *,
    omit_artifacts: set[str] | None = None,
) -> Path:
    manifest_path = tmp_path / "models" / "registry" / "production_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            _build_manifest_payload(
                artifact_paths,
                omit_artifacts=omit_artifacts or set(),
            ),
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest_path


def _build_manifest_payload(
    artifact_paths: dict[str, Path],
    *,
    omit_artifacts: set[str],
) -> dict[str, object]:
    artifact_entries = {
        artifact_key: {
            "path": str(path.relative_to(path.parents[2])).replace("\\", "/"),
            "sha256": compute_file_sha256(path),
        }
        for artifact_key, path in artifact_paths.items()
        if artifact_key in MANIFEST_REQUIRED_ARTIFACT_KEYS
        and artifact_key not in omit_artifacts
    }

    return {
        "manifest_schema_version": "1.0.0",
        "manifest_version": "test_local_logistic_bundle_v1",
        "model_version": "0.1.0",
        "run_id": "20260513_171150_baselines",
        "created_at": "2026-05-14T00:00:00Z",
        "code_ref": "test-code-ref",
        "data_version": "synthetic_v0.1.0",
        "feature_registry_version": "0.1.0",
        "runtime_model_name": "logistic_regression",
        "runtime_model_type": "classical",
        "target": "repayment_label",
        "split": {
            "train": "cohort_month 1-8",
            "validation": "cohort_month 9-10",
            "test": "cohort_month 11-12",
        },
        "artifacts": artifact_entries,
        "metrics_summary": {
            "test_auc_roc": 0.8098,
            "test_auc_pr": 0.9109,
        },
        "fairness_summary": {
            "overall_auc": 0.8098,
            "worst_auc_gap": 0.0379,
            "flagged_groups": [],
            "verdict": "acceptable",
        },
        "drift_summary": {
            "max_psi": 0.2007,
            "verdict": "watch",
        },
        "promotion_status": "candidate",
        "promotion_notes": "Test manifest for runtime bundle coverage.",
    }
