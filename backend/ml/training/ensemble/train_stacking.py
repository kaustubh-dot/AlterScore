"""Calibrated stacking ensemble training for AlterScore temporal splits.

Architecture:
  Base models (logistic, RF, XGBoost, LightGBM, TabNet, MLP)
    -> validation-split probability arrays (months 9-10, out-of-fold)
    -> stacked meta-feature matrix  [n_val x 6]
    -> LogisticRegression meta-learner fit on (meta_X_val, y_val)
    -> CalibratedClassifierCV(method='isotonic', cv='prefit') on same fold
    -> calibrated_stacking.pkl  (CalibratedClassifierCV wrapping LogisticRegression)

The calibration fold is months 9-10 only; months 11-12 are held out purely
for evaluation.  No training data touches the meta-learner or calibrator.

Artifact format: joblib pickle of CalibratedClassifierCV + a sidecar
JSON config ``calibrated_stacking_config.json`` containing base model order,
feature names, and meta-learner hyper-parameters.
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
from sklearn.calibration import CalibratedClassifierCV
try:
    from sklearn.frozen import FrozenEstimator
except ImportError:
    FrozenEstimator = None
from sklearn.linear_model import LogisticRegression

from backend.app.core.paths import MODEL_ARTIFACTS_DIR, RAW_DATA_DIR
from backend.ml.data_generation.validators import MINIMUM_TEST_ROWS, validate_synthetic_dataset
from backend.ml.evaluation.metrics import (
    build_population_percentiles_payload,
    build_split_evaluation_details,
    compute_binary_classification_metrics,
    merge_evaluation_details,
    merge_population_percentiles_reports,
    optimal_threshold,
    select_best_test_auc_model,
)
from backend.ml.preprocessing.pipeline import (
    DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    DEFAULT_TEXT_PCA_ARTIFACT_PATH,
    align_text_features_from_raw_text,
    fit_preprocessor,
    prepare_temporal_data,
    transform_features,
)
from backend.ml.training.classical.baselines import (
    DEFAULT_BASELINE_METRICS_PATH,
    DEFAULT_LOGISTIC_ARTIFACT_PATH,
    DEFAULT_METRICS_PATH,
    DEFAULT_POPULATION_PERCENTILES_PATH,
    DEFAULT_RANDOM_STATE,
    train_baselines,
)
from backend.ml.training.classical.train_classical import train_classical_models
from backend.ml.training.neural.train_tabnet import train_tabnet
from backend.ml.training.neural.train_mlp import train_mlp

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DATASET_PATH: Final[Path] = RAW_DATA_DIR / "synthetic_dataset.csv"
DEFAULT_STACKING_ARTIFACT_PATH: Final[Path] = (
    MODEL_ARTIFACTS_DIR / "calibrated_stacking.pkl"
)
DEFAULT_STACKING_CONFIG_PATH: Final[Path] = (
    MODEL_ARTIFACTS_DIR / "calibrated_stacking_config.json"
)

ENSEMBLE_MODEL_NAME: Final[str] = "calibrated_stacking"
ENSEMBLE_MODEL_TYPE: Final[str] = "ensemble"

# Ordered list of base model names — order defines column order in meta-matrix
BASE_MODEL_ORDER: Final[tuple[str, ...]] = (
    "logistic_regression",
    "random_forest",
    "xgboost",
    "lightgbm",
    "tabnet",
    "residual_mlp",
)

NUMERIC_METRIC_FIELDS: Final[tuple[str, ...]] = (
    "auc_roc", "auc_pr", "ks_statistic", "brier_score",
    "expected_calibration_error", "accuracy", "precision",
    "recall", "f1", "threshold",
)

_META_LEARNER_C: Final[float] = 1.0
_META_LEARNER_MAX_ITER: Final[int] = 1000
_META_LEARNER_SOLVER: Final[str] = "lbfgs"


# ---------------------------------------------------------------------------
# Input / Output containers
# ---------------------------------------------------------------------------


@dataclass
class StackingInputs:
    """Probability arrays from all base models on the same temporal split."""
    validation_probabilities: dict[str, np.ndarray]  # model_name -> (n_val,)
    test_probabilities: dict[str, np.ndarray]         # model_name -> (n_test,)
    y_validation: np.ndarray
    y_test: np.ndarray


@dataclass(frozen=True)
class StackingTrainingArtifacts:
    run_id: str
    stacking_artifact_path: Path | None
    stacking_config_path: Path | None
    metrics_path: Path | None
    population_percentiles_path: Path | None
    model_stats: list[dict[str, Any]]
    validation_probabilities: np.ndarray
    test_probabilities: np.ndarray
    base_model_order: tuple[str, ...]


# ---------------------------------------------------------------------------
# Primary entry point
# ---------------------------------------------------------------------------


def train_stacking(
    dataset: pd.DataFrame | None = None,
    *,
    stacking_inputs: StackingInputs | None = None,
    dataset_path: str | Path | None = None,
    expected_row_count: int | None = None,
    minimum_test_rows: int = MINIMUM_TEST_ROWS,
    preprocessor_artifact_path: str | Path | None = DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    text_pca_artifact_path: str | Path | None = DEFAULT_TEXT_PCA_ARTIFACT_PATH,
    stacking_artifact_path: str | Path | None = DEFAULT_STACKING_ARTIFACT_PATH,
    stacking_config_path: str | Path | None = DEFAULT_STACKING_CONFIG_PATH,
    metrics_path: str | Path | None = DEFAULT_METRICS_PATH,
    population_percentiles_path: str | Path | None = DEFAULT_POPULATION_PERCENTILES_PATH,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> StackingTrainingArtifacts:
    """Train and calibrate a stacking ensemble on the documented temporal split.

    If ``stacking_inputs`` is provided the base models are not re-trained; the
    pre-computed probability arrays are used directly.  Otherwise all six base
    models are re-trained from scratch on the same dataset.

    The meta-learner and isotonic calibrator are fitted on months 9-10 only.
    Months 11-12 are held out purely for evaluation.

    Args:
        dataset: Pre-loaded DataFrame; ignored when ``stacking_inputs`` given.
        stacking_inputs: Pre-computed base model probability arrays. When
            ``None`` the base models are re-trained automatically.
        dataset_path: CSV path; used only when ``dataset`` is also ``None``.
        expected_row_count: Optional validation guard.
        minimum_test_rows: Minimum acceptable test-split rows.
        preprocessor_artifact_path: Sklearn preprocessor save path.
        text_pca_artifact_path: Text-PCA artifact save path.
        stacking_artifact_path: ``.pkl`` destination for the calibrated model.
        stacking_config_path: ``.json`` sidecar config path.
        metrics_path: Merged ``metrics.json`` destination.
        population_percentiles_path: Merged percentile report destination.
        random_state: Master seed.

    Returns:
        :class:`StackingTrainingArtifacts` with paths and probability arrays.
    """
    np.random.seed(random_state)

    # ------------------------------------------------------------------
    # Obtain base model probability arrays
    # ------------------------------------------------------------------
    if stacking_inputs is not None:
        inputs = stacking_inputs
    else:
        inputs = _build_stacking_inputs(
            dataset=dataset,
            dataset_path=dataset_path,
            expected_row_count=expected_row_count,
            minimum_test_rows=minimum_test_rows,
            preprocessor_artifact_path=preprocessor_artifact_path,
            text_pca_artifact_path=text_pca_artifact_path,
            random_state=random_state,
        )

    # Validate that all required base models are present
    missing = [m for m in BASE_MODEL_ORDER if m not in inputs.validation_probabilities]
    if missing:
        raise ValueError(
            f"Missing base model probability arrays for: {missing}. "
            "All six base models must be present."
        )

    # ------------------------------------------------------------------
    # Build meta-feature matrices (column order = BASE_MODEL_ORDER)
    # ------------------------------------------------------------------
    meta_X_val = _build_meta_matrix(inputs.validation_probabilities)
    meta_X_test = _build_meta_matrix(inputs.test_probabilities)
    y_val = inputs.y_validation
    y_test = inputs.y_test

    # ------------------------------------------------------------------
    # Fit logistic meta-learner on validation fold only
    # ------------------------------------------------------------------
    meta_learner = LogisticRegression(
        C=_META_LEARNER_C,
        max_iter=_META_LEARNER_MAX_ITER,
        solver=_META_LEARNER_SOLVER,
        random_state=random_state,
    )
    meta_learner.fit(meta_X_val, y_val)

    # ------------------------------------------------------------------
    # Isotonic calibration on the same validation fold (cv='prefit')
    # ------------------------------------------------------------------
    if FrozenEstimator is not None:
        calibrated_model = CalibratedClassifierCV(
            estimator=FrozenEstimator(meta_learner),
            method="isotonic",
        )
    else:
        calibrated_model = CalibratedClassifierCV(
            estimator=meta_learner,
            method="isotonic",
            cv="prefit",
        )
    calibrated_model.fit(meta_X_val, y_val)

    # ------------------------------------------------------------------
    # Artifact persistence
    # ------------------------------------------------------------------
    resolved_artifact_path = _optional_path(stacking_artifact_path)
    resolved_config_path = _optional_path(stacking_config_path)

    stacking_config = {
        "model_name": ENSEMBLE_MODEL_NAME,
        "model_type": ENSEMBLE_MODEL_TYPE,
        "base_model_order": list(BASE_MODEL_ORDER),
        "meta_learner": {
            "class": "LogisticRegression",
            "C": _META_LEARNER_C,
            "max_iter": _META_LEARNER_MAX_ITER,
            "solver": _META_LEARNER_SOLVER,
        },
        "calibration": {"method": "isotonic", "cv": "prefit"},
        "random_state": random_state,
    }

    if resolved_artifact_path is not None:
        resolved_artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(calibrated_model, str(resolved_artifact_path))

    if resolved_config_path is not None:
        _save_json(stacking_config, resolved_config_path)

    # ------------------------------------------------------------------
    # Probability inference
    # ------------------------------------------------------------------
    val_probs = _validate_probs(
        ENSEMBLE_MODEL_NAME,
        calibrated_model.predict_proba(meta_X_val)[:, 1],
    )
    test_probs = _validate_probs(
        ENSEMBLE_MODEL_NAME,
        calibrated_model.predict_proba(meta_X_test)[:, 1],
    )
    val_threshold = optimal_threshold(y_val, val_probs)

    # ------------------------------------------------------------------
    # Metrics and evaluation details
    # ------------------------------------------------------------------
    model_stats = [
        compute_binary_classification_metrics(
            y_val, val_probs,
            model_name=ENSEMBLE_MODEL_NAME, model_type=ENSEMBLE_MODEL_TYPE,
            split="validation_months_9_10", threshold=val_threshold,
        ),
        compute_binary_classification_metrics(
            y_test, test_probs,
            model_name=ENSEMBLE_MODEL_NAME, model_type=ENSEMBLE_MODEL_TYPE,
            split="test_months_11_12", threshold=val_threshold,
        ),
    ]
    eval_details: dict[str, dict[str, Any]] = {
        "validation_months_9_10": {
            ENSEMBLE_MODEL_NAME: build_split_evaluation_details(
                y_val, val_probs,
                model_name=ENSEMBLE_MODEL_NAME, model_type=ENSEMBLE_MODEL_TYPE,
                split="validation_months_9_10", threshold=val_threshold,
            )
        },
        "test_months_11_12": {
            ENSEMBLE_MODEL_NAME: build_split_evaluation_details(
                y_test, test_probs,
                model_name=ENSEMBLE_MODEL_NAME, model_type=ENSEMBLE_MODEL_TYPE,
                split="test_months_11_12", threshold=val_threshold,
            )
        },
    }

    # For population percentiles we need full-population probs; approximate
    # with combined val + test probs as a convenient population estimate.
    pop_probs = np.concatenate([val_probs, test_probs])
    population_payload = build_population_percentiles_payload(
        pop_probs, model_name=ENSEMBLE_MODEL_NAME
    )

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_stacking")

    # ------------------------------------------------------------------
    # Merge and persist metrics.json
    # ------------------------------------------------------------------
    merged_model_stats: list[dict[str, Any]] = model_stats
    if metrics_path is not None:
        existing = _load_json_if_exists(metrics_path)
        merged_model_stats = _merge_model_stats(
            existing_model_stats=existing.get("model_stats", []),
            updated_model_stats=model_stats,
        )
        metrics_out: dict[str, Any] = {
            **{k: v for k, v in existing.items()
               if k not in {"run_id", "split_row_counts", "model_stats", "evaluation_details"}},
            "run_id": run_id,
            "split_row_counts": {
                "validation": int(len(y_val)),
                "test": int(len(y_test)),
            },
            "model_stats": merged_model_stats,
            "baselines": existing.get("baselines", []),
            "evaluation_details": merge_evaluation_details(
                existing.get("evaluation_details"), eval_details
            ),
        }
        _save_json(metrics_out, metrics_path)

    # ------------------------------------------------------------------
    # Merge and persist population_percentiles.json
    # ------------------------------------------------------------------
    if population_percentiles_path is not None:
        existing_pop = _load_json_if_exists(population_percentiles_path) or None
        default_name = _resolve_default_model_name(
            model_stats=merged_model_stats,
            existing_payload=existing_pop,
            updated_payloads={ENSEMBLE_MODEL_NAME: population_payload},
        )
        _save_json(
            merge_population_percentiles_reports(
                existing_pop,
                {ENSEMBLE_MODEL_NAME: population_payload},
                default_model_name=default_name,
            ),
            population_percentiles_path,
        )

    return StackingTrainingArtifacts(
        run_id=run_id,
        stacking_artifact_path=resolved_artifact_path,
        stacking_config_path=resolved_config_path,
        metrics_path=_optional_path(metrics_path),
        population_percentiles_path=_optional_path(population_percentiles_path),
        model_stats=model_stats,
        validation_probabilities=val_probs,
        test_probabilities=test_probs,
        base_model_order=BASE_MODEL_ORDER,
    )


# ---------------------------------------------------------------------------
# Stacking artifact load (inference-time)
# ---------------------------------------------------------------------------


def load_stacking_model(artifact_path: str | Path) -> CalibratedClassifierCV:
    """Load the calibrated stacking ensemble from a ``.pkl`` artifact.

    Args:
        artifact_path: Path to the ``.pkl`` produced by ``train_stacking``.

    Returns:
        A ``CalibratedClassifierCV`` ready for ``predict_proba``.

    Raises:
        FileNotFoundError: If the artifact does not exist.
    """
    resolved = Path(artifact_path)
    if not resolved.is_file():
        raise FileNotFoundError(
            f"Stacking artifact not found at {resolved}. "
            "Run the stacking training job first."
        )
    return joblib.load(str(resolved))


def predict_stacking_proba(
    model: CalibratedClassifierCV,
    base_model_probabilities: dict[str, np.ndarray],
) -> np.ndarray:
    """Run inference with the stacking ensemble.

    Args:
        model: Loaded calibrated stacking model.
        base_model_probabilities: Dict mapping model name to 1-D probability
            arrays (must contain all BASE_MODEL_ORDER names).

    Returns:
        1-D array of calibrated positive-class probabilities.
    """
    meta_X = _build_meta_matrix(base_model_probabilities)
    return model.predict_proba(meta_X)[:, 1]


# ---------------------------------------------------------------------------
# Build stacking inputs by re-training all base models
# ---------------------------------------------------------------------------


def _build_stacking_inputs(
    *,
    dataset: pd.DataFrame | None,
    dataset_path: str | Path | None,
    expected_row_count: int | None,
    minimum_test_rows: int,
    preprocessor_artifact_path: str | Path | None,
    text_pca_artifact_path: str | Path | None,
    random_state: int,
) -> StackingInputs:
    """Re-train all six base models and collect their probability arrays."""
    resolved_dataset, _ = _load_dataset(dataset, dataset_path)

    # Pass metrics/percentile paths as None to avoid partial writes;
    # the stacking module owns the final merged write.
    bl = train_baselines(
        resolved_dataset,
        expected_row_count=expected_row_count,
        minimum_test_rows=minimum_test_rows,
        preprocessor_artifact_path=preprocessor_artifact_path,
        text_pca_artifact_path=text_pca_artifact_path,
        logistic_artifact_path=None,
        baseline_metrics_path=None,
        metrics_path=None,
        population_percentiles_path=None,
        psi_report_path=None,
        fairness_report_path=None,
        global_importance_path=None,
        dice_explainer_path=None,
        random_state=random_state,
    )

    cl = train_classical_models(
        resolved_dataset,
        expected_row_count=expected_row_count,
        minimum_test_rows=minimum_test_rows,
        preprocessor_artifact_path=preprocessor_artifact_path,
        text_pca_artifact_path=text_pca_artifact_path,
        random_forest_artifact_path=None,
        xgboost_artifact_path=None,
        lightgbm_artifact_path=None,
        logistic_artifact_path=None,
        baseline_metrics_path=DEFAULT_BASELINE_METRICS_PATH,
        metrics_path=None,
        population_percentiles_path=None,
        psi_report_path=None,
        fairness_report_path=None,
        global_importance_path=None,
        dice_explainer_path=None,
        random_state=random_state,
    )

    tn = train_tabnet(
        resolved_dataset,
        expected_row_count=expected_row_count,
        minimum_test_rows=minimum_test_rows,
        preprocessor_artifact_path=preprocessor_artifact_path,
        text_pca_artifact_path=text_pca_artifact_path,
        tabnet_artifact_path=None,
        metrics_path=None,
        population_percentiles_path=None,
        random_state=random_state,
    )

    mlp = train_mlp(
        resolved_dataset,
        expected_row_count=expected_row_count,
        minimum_test_rows=minimum_test_rows,
        preprocessor_artifact_path=preprocessor_artifact_path,
        text_pca_artifact_path=text_pca_artifact_path,
        mlp_artifact_path=None,
        metrics_path=None,
        population_percentiles_path=None,
        random_state=random_state,
    )

    # Derive y arrays from the prepared data (lightweight re-prepare)
    aligned, raw_emb = align_text_features_from_raw_text(resolved_dataset)
    prepared = prepare_temporal_data(
        aligned,
        raw_text_embeddings=raw_emb,
        text_pca_random_state=random_state,
        text_pca_artifact_path=None,
    )
    y_validation = prepared.validation.y.to_numpy(dtype=int)
    y_test_arr = prepared.test.y.to_numpy(dtype=int)

    # Logistic probabilities: re-derive from the saved preprocessor + logistic artifact.
    # The classical module only returns RF/XGB/LGBM in validation_probabilities;
    # logistic is trained in baselines and saved separately.
    logistic_val: np.ndarray
    logistic_test: np.ndarray
    if (
        preprocessor_artifact_path is not None
        and Path(preprocessor_artifact_path).is_file()
        and bl.logistic_model_path is not None
        and bl.logistic_model_path.is_file()
    ):
        import joblib as _jl
        _pre = _jl.load(str(preprocessor_artifact_path))
        _log = _jl.load(str(bl.logistic_model_path))
        _Xv = transform_features(_pre, prepared.validation.X)
        _Xt = transform_features(_pre, prepared.test.X)
        logistic_val = _log.predict_proba(_Xv)[:, 1].astype(float)
        logistic_test = _log.predict_proba(_Xt)[:, 1].astype(float)
    else:
        # Fallback: fit logistic inline on the prepared split
        from sklearn.linear_model import LogisticRegression as _LR
        _pre2 = fit_preprocessor(prepared.train.X, artifact_path=None)
        _Xtr = transform_features(_pre2, prepared.train.X)
        _Xv2 = transform_features(_pre2, prepared.validation.X)
        _Xt2 = transform_features(_pre2, prepared.test.X)
        _lr = _LR(max_iter=1000, random_state=random_state)
        _lr.fit(_Xtr, prepared.train.y.to_numpy(dtype=int))
        logistic_val = _lr.predict_proba(_Xv2)[:, 1].astype(float)
        logistic_test = _lr.predict_proba(_Xt2)[:, 1].astype(float)

    val_probs: dict[str, np.ndarray] = {
        "logistic_regression": logistic_val,
        "random_forest": cl.validation_probabilities["random_forest"],
        "xgboost": cl.validation_probabilities["xgboost"],
        "lightgbm": cl.validation_probabilities["lightgbm"],
        "tabnet": tn.validation_probabilities,
        "residual_mlp": mlp.validation_probabilities,
    }
    test_probs: dict[str, np.ndarray] = {
        "logistic_regression": logistic_test,
        "random_forest": cl.test_probabilities["random_forest"],
        "xgboost": cl.test_probabilities["xgboost"],
        "lightgbm": cl.test_probabilities["lightgbm"],
        "tabnet": tn.test_probabilities,
        "residual_mlp": mlp.test_probabilities,
    }

    return StackingInputs(
        validation_probabilities=val_probs,
        test_probabilities=test_probs,
        y_validation=y_validation,
        y_test=y_test_arr,
    )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _build_meta_matrix(prob_dict: dict[str, np.ndarray]) -> np.ndarray:
    """Stack base model probability arrays into an (n, 6) meta-feature matrix."""
    columns = [np.asarray(prob_dict[name], dtype=float) for name in BASE_MODEL_ORDER]
    return np.column_stack(columns)


def _validate_probs(model_name: str, probs: np.ndarray) -> np.ndarray:
    arr = np.asarray(probs, dtype=float)
    if np.isnan(arr).any():
        raise ValueError(f"{model_name} produced NaN probabilities.")
    if ((arr < 0.0) | (arr > 1.0)).any():
        raise ValueError(f"{model_name} produced probabilities outside [0, 1].")
    return arr


def _load_dataset(
    dataset: pd.DataFrame | None, dataset_path: str | Path | None
) -> tuple[pd.DataFrame, Path | None]:
    if dataset is not None:
        return dataset.copy(), None
    resolved = Path(dataset_path or DEFAULT_DATASET_PATH)
    if not resolved.is_file():
        raise FileNotFoundError(
            f"Dataset not found at {resolved}. Run the synthetic data generator first."
        )
    return pd.read_csv(resolved), resolved


def _optional_path(path: str | Path | None) -> Path | None:
    return None if path is None else Path(path)


def _load_json_if_exists(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    p = Path(path)
    if not p.is_file():
        return {}
    payload = json.loads(p.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _save_json(payload: Any, path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _merge_model_stats(
    *, existing_model_stats: list[dict[str, Any]],
    updated_model_stats: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lookup = {(r["model_name"], r["split"]): r for r in updated_model_stats}
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in existing_model_stats:
        key = (str(item.get("model_name")), str(item.get("split")))
        rep = lookup.get(key)
        if rep is not None:
            merged.append(rep)
            seen.add(key)
        else:
            merged.append(item)
    for item in updated_model_stats:
        key = (item["model_name"], item["split"])
        if key not in seen:
            merged.append(item)
            seen.add(key)
    return merged


def _resolve_default_model_name(
    *, model_stats: list[dict[str, Any]],
    existing_payload: dict[str, Any] | None,
    updated_payloads: dict[str, dict[str, Any]],
) -> str:
    available = set(updated_payloads)
    if isinstance(existing_payload, dict):
        em = existing_payload.get("models")
        if isinstance(em, dict):
            available.update(n for n, p in em.items() if isinstance(n, str) and isinstance(p, dict))
    selected = select_best_test_auc_model(model_stats, candidate_model_names=available)
    if selected is not None:
        return selected
    ed = None if existing_payload is None else existing_payload.get("default_model_name")
    if isinstance(ed, str) and ed in available:
        return ed
    if available:
        return sorted(available)[0]
    raise ValueError("At least one population percentile payload is required.")


__all__ = [
    "BASE_MODEL_ORDER", "DEFAULT_STACKING_ARTIFACT_PATH",
    "DEFAULT_STACKING_CONFIG_PATH", "ENSEMBLE_MODEL_NAME", "ENSEMBLE_MODEL_TYPE",
    "StackingInputs", "StackingTrainingArtifacts",
    "load_stacking_model", "predict_stacking_proba", "train_stacking",
]
