"""Ensemble promotion pipeline for AlterScore Track D.

Runs the full offline pipeline (baselines → classical → TabNet → MLP →
stacking), saves all artifacts to models/, refreshes SHAP/DICE/fairness/
global-importance artifacts for the calibrated stacking ensemble, computes
SHA256 checksums, and writes an updated production_manifest.json.

SHAP explainer strategy:
  A surrogate LogisticRegression is fit on the train-split processed features
  against the stacking ensemble's binarised soft-label predictions.  This gives
  a feature-level linear approximation of the ensemble, enabling the existing
  exact-linear-SHAP infrastructure without changing the serving pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Final

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from backend.app.core.paths import (
    MODEL_ARTIFACTS_DIR,
    MODEL_EXPLAINERS_DIR,
    MODEL_PREPROCESSORS_DIR,
    MODEL_REPORTS_DIR,
    MODEL_REGISTRY_DIR,
    RAW_DATA_DIR,
)
from backend.ml.data_generation.validators import MINIMUM_TEST_ROWS, validate_synthetic_dataset
from backend.ml.evaluation.fairness import (
    build_fairness_report_for_candidate_probabilities,
    save_fairness_report,
)
from backend.ml.explainability.dice_explainer import (
    build_default_persisted_dice_explainer,
    save_persisted_dice_explainer,
)
from backend.ml.explainability.global_importance import (
    build_global_importance_report_for_candidate_models,
    save_global_importance_report,
)
from backend.ml.explainability.shap_explainer import PersistedShapExplainer
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES
from backend.ml.preprocessing.pipeline import (
    align_text_features_from_raw_text,
    prepare_temporal_data,
    transform_features,
)
from backend.ml.registry.production_manifest import compute_file_sha256
from backend.ml.training.classical.baselines import (
    DEFAULT_LOGISTIC_ARTIFACT_PATH,
    DEFAULT_METRICS_PATH,
    DEFAULT_POPULATION_PERCENTILES_PATH,
    train_baselines,
)
from backend.ml.training.classical.train_classical import train_classical_models
from backend.ml.training.ensemble.train_stacking import (
    BASE_MODEL_ORDER,
    ENSEMBLE_MODEL_NAME,
    ENSEMBLE_MODEL_TYPE,
    StackingInputs,
    _build_meta_matrix,
    train_stacking,
)
from backend.ml.training.neural.train_mlp import train_mlp
from backend.ml.training.neural.train_tabnet import train_tabnet

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DEFAULT_DATASET_PATH: Final[Path] = RAW_DATA_DIR / "synthetic_dataset.csv"
DEFAULT_STACKING_ARTIFACT_PATH: Final[Path] = MODEL_ARTIFACTS_DIR / "calibrated_stacking.pkl"
DEFAULT_STACKING_CONFIG_PATH: Final[Path] = MODEL_ARTIFACTS_DIR / "calibrated_stacking_config.json"
DEFAULT_PREPROCESSOR_PATH: Final[Path] = MODEL_PREPROCESSORS_DIR / "preprocessor.pkl"
DEFAULT_TEXT_PCA_PATH: Final[Path] = MODEL_PREPROCESSORS_DIR / "text_pca.pkl"
DEFAULT_SHAP_EXPLAINER_PATH: Final[Path] = MODEL_EXPLAINERS_DIR / "shap_explainer.pkl"
DEFAULT_DICE_EXPLAINER_PATH: Final[Path] = MODEL_EXPLAINERS_DIR / "dice_explainer.pkl"
DEFAULT_GLOBAL_IMPORTANCE_PATH: Final[Path] = MODEL_REPORTS_DIR / "global_importance.json"
DEFAULT_FAIRNESS_REPORT_PATH: Final[Path] = MODEL_REPORTS_DIR / "fairness_report.json"
DEFAULT_PSI_REPORT_PATH: Final[Path] = MODEL_REPORTS_DIR / "psi_report.json"
DEFAULT_MANIFEST_PATH: Final[Path] = MODEL_REGISTRY_DIR / "production_manifest.json"

MANIFEST_SCHEMA_VERSION: Final[str] = "1.0.0"
ENSEMBLE_MODEL_VERSION: Final[str] = "0.2.0"
DATA_VERSION: Final[str] = "synthetic_v0.1.0"
FEATURE_REGISTRY_VERSION: Final[str] = "0.1.0"


@dataclass(frozen=True)
class PromotionArtifacts:
    manifest_path: Path
    stacking_artifact_path: Path
    shap_explainer_path: Path
    dice_explainer_path: Path
    metrics_path: Path
    fairness_report_path: Path
    global_importance_path: Path
    test_auc_roc: float
    run_id: str


def promote_ensemble(
    dataset: pd.DataFrame | None = None,
    *,
    dataset_path: str | Path | None = None,
    expected_row_count: int | None = None,
    minimum_test_rows: int = MINIMUM_TEST_ROWS,
    random_state: int = 42,
    stacking_artifact_path: str | Path = DEFAULT_STACKING_ARTIFACT_PATH,
    stacking_config_path: str | Path = DEFAULT_STACKING_CONFIG_PATH,
    preprocessor_path: str | Path = DEFAULT_PREPROCESSOR_PATH,
    text_pca_path: str | Path = DEFAULT_TEXT_PCA_PATH,
    shap_explainer_path: str | Path = DEFAULT_SHAP_EXPLAINER_PATH,
    dice_explainer_path: str | Path = DEFAULT_DICE_EXPLAINER_PATH,
    global_importance_path: str | Path = DEFAULT_GLOBAL_IMPORTANCE_PATH,
    fairness_report_path: str | Path = DEFAULT_FAIRNESS_REPORT_PATH,
    psi_report_path: str | Path = DEFAULT_PSI_REPORT_PATH,
    metrics_path: str | Path = DEFAULT_METRICS_PATH,
    population_percentiles_path: str | Path = DEFAULT_POPULATION_PERCENTILES_PATH,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    manifest_version: str = "calibrated_stacking_ensemble_v1",
    code_ref: str = "antigravity/dev",
    logistic_artifact_path: str | Path | None = None,
    random_forest_artifact_path: str | Path | None = None,
    xgboost_artifact_path: str | Path | None = None,
    lightgbm_artifact_path: str | Path | None = None,
    tabnet_artifact_path: str | Path | None = None,
    mlp_artifact_path: str | Path | None = None,
) -> PromotionArtifacts:
    """Full offline pipeline → promotion.

    Steps:
      1. Train baselines + classical + TabNet + MLP to collect val/test proba arrays.
      2. Fit + calibrate the stacking ensemble; save to models/artifacts/.
      3. Build a surrogate-LR SHAP explainer (train features → ensemble predictions).
      4. Build the DICE counterfactual explainer (model-agnostic, predict_proba).
      5. Refresh global-importance and fairness reports.
      6. Compute SHA256 checksums; write production_manifest.json.
    """
    np.random.seed(random_state)

    # ------------------------------------------------------------------
    # 1. Load / validate dataset
    # ------------------------------------------------------------------
    if dataset is None:
        resolved_path = Path(dataset_path or DEFAULT_DATASET_PATH)
        if not resolved_path.is_file():
            raise FileNotFoundError(f"Dataset not found at {resolved_path}.")
        dataset = pd.read_csv(resolved_path)

    validate_synthetic_dataset(
        dataset,
        expected_row_count=expected_row_count if expected_row_count is not None else len(dataset),
        minimum_test_rows=minimum_test_rows,
    )

    logi_path = Path(logistic_artifact_path) if logistic_artifact_path else MODEL_ARTIFACTS_DIR / "logistic_best.pkl"
    rf_path = Path(random_forest_artifact_path) if random_forest_artifact_path else MODEL_ARTIFACTS_DIR / "rf_best.pkl"
    xgb_path = Path(xgboost_artifact_path) if xgboost_artifact_path else MODEL_ARTIFACTS_DIR / "xgb_best.pkl"
    lgbm_path = Path(lightgbm_artifact_path) if lightgbm_artifact_path else MODEL_ARTIFACTS_DIR / "lgbm_best.pkl"
    tabnet_path = Path(tabnet_artifact_path) if tabnet_artifact_path else MODEL_ARTIFACTS_DIR / "tabnet_epoch_best.zip"
    mlp_path = Path(mlp_artifact_path) if mlp_artifact_path else MODEL_ARTIFACTS_DIR / "mlp_best.pt"
    baseline_metrics_path = MODEL_REPORTS_DIR / "baseline_metrics.json"

    # ------------------------------------------------------------------
    # 2. Train all six base models
    # ------------------------------------------------------------------
    bl = train_baselines(
        dataset.copy(),
        expected_row_count=expected_row_count,
        minimum_test_rows=minimum_test_rows,
        preprocessor_artifact_path=preprocessor_path,
        text_pca_artifact_path=text_pca_path,
        logistic_artifact_path=logi_path,
        baseline_metrics_path=baseline_metrics_path,
        metrics_path=metrics_path,
        population_percentiles_path=population_percentiles_path,
        psi_report_path=psi_report_path,
        fairness_report_path=None,
        global_importance_path=None,
        dice_explainer_path=None,
    )

    cl = train_classical_models(
        dataset.copy(),
        expected_row_count=expected_row_count,
        minimum_test_rows=minimum_test_rows,
        preprocessor_artifact_path=preprocessor_path,
        text_pca_artifact_path=text_pca_path,
        random_forest_artifact_path=rf_path,
        xgboost_artifact_path=xgb_path,
        lightgbm_artifact_path=lgbm_path,
        logistic_artifact_path=bl.logistic_model_path,
        baseline_metrics_path=bl.baseline_metrics_path,
        metrics_path=bl.metrics_path,
        population_percentiles_path=bl.population_percentiles_path,
        psi_report_path=None,
        fairness_report_path=None,
        global_importance_path=None,
        dice_explainer_path=None,
        random_state=random_state,
    )

    tn = train_tabnet(
        dataset.copy(),
        expected_row_count=expected_row_count,
        minimum_test_rows=minimum_test_rows,
        preprocessor_artifact_path=preprocessor_path,
        text_pca_artifact_path=text_pca_path,
        tabnet_artifact_path=tabnet_path,
        metrics_path=cl.metrics_path,
        population_percentiles_path=cl.population_percentiles_path,
        random_state=random_state,
    )

    mlp_art = train_mlp(
        dataset.copy(),
        expected_row_count=expected_row_count,
        minimum_test_rows=minimum_test_rows,
        preprocessor_artifact_path=preprocessor_path,
        text_pca_artifact_path=text_pca_path,
        mlp_artifact_path=mlp_path,
        metrics_path=tn.metrics_path,
        population_percentiles_path=tn.population_percentiles_path,
        random_state=random_state,
    )

    # ------------------------------------------------------------------
    # Derive processed feature matrices for SHAP and global importance
    # ------------------------------------------------------------------
    aligned, raw_emb = align_text_features_from_raw_text(dataset.copy())
    prepared = prepare_temporal_data(
        aligned,
        raw_text_embeddings=raw_emb,
        text_pca_random_state=random_state,
        text_pca_artifact_path=None,
    )
    pre = joblib.load(str(preprocessor_path))
    X_train = transform_features(pre, prepared.train.X)
    X_val = transform_features(pre, prepared.validation.X)
    X_test = transform_features(pre, prepared.test.X)
    y_val = prepared.validation.y.to_numpy(dtype=int)
    y_test = prepared.test.y.to_numpy(dtype=int)

    # Derive logistic probs (ClassicalTrainingArtifacts only stores RF/XGB/LGBM)
    log_model = joblib.load(str(logi_path))
    logistic_val = log_model.predict_proba(X_val)[:, 1].astype(float)
    logistic_test = log_model.predict_proba(X_test)[:, 1].astype(float)

    # ------------------------------------------------------------------
    # 3. Fit + calibrate stacking ensemble
    # ------------------------------------------------------------------
    stk_inputs = StackingInputs(
        validation_probabilities={
            "logistic_regression": logistic_val,
            "random_forest": cl.validation_probabilities["random_forest"],
            "xgboost": cl.validation_probabilities["xgboost"],
            "lightgbm": cl.validation_probabilities["lightgbm"],
            "tabnet": tn.validation_probabilities,
            "residual_mlp": mlp_art.validation_probabilities,
        },
        test_probabilities={
            "logistic_regression": logistic_test,
            "random_forest": cl.test_probabilities["random_forest"],
            "xgboost": cl.test_probabilities["xgboost"],
            "lightgbm": cl.test_probabilities["lightgbm"],
            "tabnet": tn.test_probabilities,
            "residual_mlp": mlp_art.test_probabilities,
        },
        y_validation=y_val,
        y_test=y_test,
    )

    stk = train_stacking(
        stacking_inputs=stk_inputs,
        stacking_artifact_path=stacking_artifact_path,
        stacking_config_path=stacking_config_path,
        metrics_path=mlp_art.metrics_path,
        population_percentiles_path=mlp_art.population_percentiles_path,
        random_state=random_state,
    )

    stacking_model = joblib.load(str(stacking_artifact_path))
    test_auc = next(
        (r["auc_roc"] for r in stk.model_stats if r["split"] == "test_months_11_12"),
        0.0,
    )

    # ------------------------------------------------------------------
    # 4. Surrogate-LR SHAP explainer
    # ------------------------------------------------------------------
    # Get ensemble train-set predictions via the meta-matrix
    log_train_probs = log_model.predict_proba(X_train)[:, 1].astype(float)
    rf_model = joblib.load(str(rf_path))
    xgb_model = joblib.load(str(xgb_path))
    lgbm_model = joblib.load(str(lgbm_path))

    from backend.ml.training.neural.train_tabnet import load_tabnet_model
    from backend.ml.training.neural.train_mlp import load_mlp_model
    import torch

    tabnet_model = load_tabnet_model(tabnet_path)
    tabnet_train_probs = tabnet_model.predict_proba(X_train)[:, 1].astype(float)

    mlp_model = load_mlp_model(mlp_path)
    mlp_model.eval()
    with torch.no_grad():
        mlp_train_probs = (
            mlp_model(torch.tensor(X_train, dtype=torch.float32)).cpu().numpy().astype(float)
        )

    train_meta_X = _build_meta_matrix({
        "logistic_regression": log_train_probs,
        "random_forest": rf_model.predict_proba(X_train)[:, 1],
        "xgboost": xgb_model.predict_proba(X_train)[:, 1],
        "lightgbm": lgbm_model.predict_proba(X_train)[:, 1],
        "tabnet": tabnet_train_probs,
        "residual_mlp": mlp_train_probs,
    })
    ensemble_train_probs = stacking_model.predict_proba(train_meta_X)[:, 1]
    surrogate_labels = (ensemble_train_probs >= 0.5).astype(int)

    surrogate_lr = LogisticRegression(max_iter=1000, random_state=random_state)
    surrogate_lr.fit(X_train, surrogate_labels)
    surrogate_coef = np.asarray(surrogate_lr.coef_, dtype=float)
    if surrogate_coef.ndim == 2:
        surrogate_coef = surrogate_coef[-1]
    background_mean = np.asarray(np.mean(X_train, axis=0), dtype=float)

    shap_explainer = PersistedShapExplainer(
        model_name=ENSEMBLE_MODEL_NAME,
        algorithm="exact_linear_shap",
        feature_names=tuple(ALL_MODEL_FEATURES),
        background_mean=background_mean,
        background_size=int(X_train.shape[0]),
        coefficients=surrogate_coef,
    )
    shap_explainer.validate(expected_feature_names=ALL_MODEL_FEATURES)
    resolved_shap_path = Path(shap_explainer_path)
    resolved_shap_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(shap_explainer, str(resolved_shap_path))

    # ------------------------------------------------------------------
    # 5. DICE counterfactual explainer (model-agnostic, predict_proba ready)
    # ------------------------------------------------------------------
    dice_explainer = build_default_persisted_dice_explainer(model_name=ENSEMBLE_MODEL_NAME)
    save_persisted_dice_explainer(dice_explainer, dice_explainer_path)

    # ------------------------------------------------------------------
    # 6. Refresh global-importance with best classical base model
    # ------------------------------------------------------------------
    merged_stats = json.loads(Path(metrics_path).read_text(encoding="utf-8")).get("model_stats", [])
    gi_report, _ = build_global_importance_report_for_candidate_models(
        {"random_forest": rf_model, "xgboost": xgb_model, "lightgbm": lgbm_model},
        train_processed_features=X_train,
        test_processed_features=X_test,
        model_stats=merged_stats,
        candidate_model_types={n: "classical" for n in ("random_forest", "xgboost", "lightgbm")},
    )
    save_global_importance_report(gi_report, global_importance_path)

    # ------------------------------------------------------------------
    # 7. Fairness report against the stacking ensemble
    # ------------------------------------------------------------------
    fairness_report, _ = build_fairness_report_for_candidate_probabilities(
        y_test,
        prepared.test.protected,
        {ENSEMBLE_MODEL_NAME: stk.test_probabilities},
        model_stats=stk.model_stats,
        feature_frame=prepared.test.X,
    )
    save_fairness_report(fairness_report, fairness_report_path)

    # ------------------------------------------------------------------
    # 8. Compute SHA256 checksums; write manifest
    # ------------------------------------------------------------------
    artifact_spec: dict[str, tuple[Path, str]] = {
        "runtime_model": (Path(stacking_artifact_path), "models/artifacts/calibrated_stacking.pkl"),
        "preprocessor": (Path(preprocessor_path), "models/preprocessors/preprocessor.pkl"),
        "text_pca": (Path(text_pca_path), "models/preprocessors/text_pca.pkl"),
        "shap_explainer": (resolved_shap_path, "models/explainers/shap_explainer.pkl"),
        "dice_explainer": (Path(dice_explainer_path), "models/explainers/dice_explainer.pkl"),
        "metrics": (Path(metrics_path), "models/reports/metrics.json"),
        "baseline_metrics": (baseline_metrics_path, "models/reports/baseline_metrics.json"),
        "fairness_report": (Path(fairness_report_path), "models/reports/fairness_report.json"),
        "psi_report": (Path(psi_report_path), "models/reports/psi_report.json"),
        "global_importance": (Path(global_importance_path), "models/reports/global_importance.json"),
        "population_percentiles": (
            Path(population_percentiles_path), "models/reports/population_percentiles.json"
        ),
    }
    artifacts_block = {
        key: {"path": rel, "sha256": compute_file_sha256(p)}
        for key, (p, rel) in artifact_spec.items()
        if p.is_file()
    }

    fairness_payload = json.loads(Path(fairness_report_path).read_text(encoding="utf-8"))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_ensemble_promotion")


    # Build base_models section
    base_model_specs = {
        "logistic_regression": (logi_path, "models/artifacts/logistic_best.pkl"),
        "random_forest": (rf_path, "models/artifacts/rf_best.pkl"),
        "xgboost": (xgb_path, "models/artifacts/xgb_best.pkl"),
        "lightgbm": (lgbm_path, "models/artifacts/lgbm_best.pkl"),
        "tabnet": (tabnet_path, "models/artifacts/tabnet_epoch_best.zip"),
        "residual_mlp": (mlp_path, "models/artifacts/mlp_best.pt"),
    }
    base_models_block = {
        name: {"path": rel, "sha256": compute_file_sha256(p)}
        for name, (p, rel) in base_model_specs.items()
        if p.is_file()
    }
    
    stacking_config_p = Path(stacking_config_path)
    stacking_config_block = {
        "path": "models/artifacts/calibrated_stacking_config.json",
        "sha256": compute_file_sha256(stacking_config_p)
    } if stacking_config_p.is_file() else None

    manifest: dict[str, Any] = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "manifest_version": manifest_version,
        "model_version": ENSEMBLE_MODEL_VERSION,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "code_ref": code_ref,
        "data_version": DATA_VERSION,
        "feature_registry_version": FEATURE_REGISTRY_VERSION,
        "runtime_model_name": "stacking_ensemble",
        "runtime_model_type": ENSEMBLE_MODEL_TYPE,
        "target": "repayment_label",
        "split": {
            "train": "cohort_month 1-8",
            "validation": "cohort_month 9-10",
            "test": "cohort_month 11-12",
        },
        "artifacts": artifacts_block,
        "base_models": base_models_block,
        "stacking_config": stacking_config_block,

        "metrics_summary": {
            "test_split": "test_months_11_12",
            "test_auc_roc": round(float(test_auc), 4),
            "ensemble_base_models": list(BASE_MODEL_ORDER),
            "meta_learner": "LogisticRegression(C=1.0)",
            "calibration": "isotonic",
        },
        "fairness_summary": {
            "overall_auc": round(float(test_auc), 4),
            "verdict": fairness_payload.get("verdict", "see fairness_report.json"),
        },
        "drift_summary": {
            "verdict": "see psi_report.json",
            "note": "PSI computed on base features; ensemble does not alter feature distribution.",
        },
        "promotion_status": "promoted",
        "promotion_notes": (
            "Calibrated stacking ensemble promoted. "
            "Meta-learner: LogisticRegression on months-9-10 stacked probabilities. "
            "Calibration: isotonic (cv=prefit). "
            "SHAP: surrogate LR on train-split features vs ensemble soft labels. "
            "DICE: model-agnostic (predict_proba compatible)."
        ),
    }

    manifest_out = Path(manifest_path)
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return PromotionArtifacts(
        manifest_path=manifest_out,
        stacking_artifact_path=Path(stacking_artifact_path),
        shap_explainer_path=resolved_shap_path,
        dice_explainer_path=Path(dice_explainer_path),
        metrics_path=Path(metrics_path),
        fairness_report_path=Path(fairness_report_path),
        global_importance_path=Path(global_importance_path),
        test_auc_roc=float(test_auc),
        run_id=run_id,
    )


__all__ = ["PromotionArtifacts", "promote_ensemble"]
