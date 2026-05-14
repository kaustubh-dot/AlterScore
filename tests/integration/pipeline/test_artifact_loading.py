import json
from pathlib import Path
import shutil

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
)
from backend.app.services.scoring import score_request_with_bundle
from backend.ml.data_generation.generator import generate_synthetic_dataset
from backend.ml.training.classical.baselines import train_baselines
from backend.ml.training.classical.train_classical import train_classical_models


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
    assert response.counterfactual_actions
    assert all(action.estimated_score_gain >= 0 for action in response.counterfactual_actions)
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
    manifest_payload["artifacts"]["runtime_model"] = "models/artifacts/logistic_best.pkl"
    manifest_path.write_text(
        json.dumps(manifest_payload, indent=2),
        encoding="utf-8",
    )

    settings = load_settings({"ALTERSCORE_REPO_ROOT": str(tmp_path)})

    with pytest.raises(ArtifactLoadError, match="runtime_model"):
        load_runtime_artifact_bundle(settings, strict=False)


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
        "population_percentiles": model_root / "reports" / "population_percentiles.json",
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
            / "models"
            / "explainers"
            / "shap_explainer.pkl",
            artifact_paths["shap_explainer"],
        )
    return artifact_paths


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
