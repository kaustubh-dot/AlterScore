"""Classical model training loop for AlterScore temporal splits."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Final

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from backend.app.core.paths import MODEL_ARTIFACTS_DIR, MODEL_REPORTS_DIR, RAW_DATA_DIR
from backend.ml.data_generation.validators import MINIMUM_TEST_ROWS, validate_synthetic_dataset
from backend.ml.evaluation.drift import (
    DEFAULT_PSI_REPORT_PATH,
    build_psi_report_from_prepared_data,
)
from backend.ml.evaluation.fairness import (
    DEFAULT_FAIRNESS_REPORT_PATH,
    build_fairness_report_for_candidate_probabilities,
    save_fairness_report,
)
from backend.ml.evaluation.metrics import (
    build_population_percentiles_payload,
    build_split_evaluation_details,
    compute_binary_classification_metrics,
    merge_evaluation_details,
    merge_population_percentiles_reports,
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
)

DEFAULT_DATASET_PATH: Final[Path] = RAW_DATA_DIR / "synthetic_dataset.csv"
DEFAULT_RF_ARTIFACT_PATH: Final[Path] = MODEL_ARTIFACTS_DIR / "rf_best.pkl"
DEFAULT_XGB_ARTIFACT_PATH: Final[Path] = MODEL_ARTIFACTS_DIR / "xgb_best.pkl"
DEFAULT_LGBM_ARTIFACT_PATH: Final[Path] = MODEL_ARTIFACTS_DIR / "lgbm_best.pkl"
CLASSICAL_MODEL_ORDER: Final[tuple[str, ...]] = (
    "random_forest",
    "xgboost",
    "lightgbm",
)
CLASSICAL_MODEL_TYPE: Final[str] = "classical"
NUMERIC_METRIC_FIELDS: Final[tuple[str, ...]] = (
    "auc_roc",
    "auc_pr",
    "ks_statistic",
    "brier_score",
    "expected_calibration_error",
    "accuracy",
    "precision",
    "recall",
    "f1",
    "threshold",
)


@dataclass(frozen=True)
class ClassicalTrainingArtifacts:
    run_id: str
    dataset_path: Path | None
    preprocessor_path: Path | None
    text_pca_path: Path | None
    model_artifact_paths: dict[str, Path | None]
    metrics_path: Path | None
    population_percentiles_path: Path | None
    psi_report_path: Path | None
    fairness_report_path: Path | None
    model_stats: list[dict[str, Any]]
    baseline_metrics: list[dict[str, Any]]
    validation_probabilities: dict[str, np.ndarray]
    test_probabilities: dict[str, np.ndarray]


def train_classical_models(
    dataset: pd.DataFrame | None = None,
    *,
    dataset_path: str | Path | None = None,
    expected_row_count: int | None = None,
    minimum_test_rows: int = MINIMUM_TEST_ROWS,
    preprocessor_artifact_path: str | Path | None = DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    text_pca_artifact_path: str | Path | None = DEFAULT_TEXT_PCA_ARTIFACT_PATH,
    random_forest_artifact_path: str | Path | None = DEFAULT_RF_ARTIFACT_PATH,
    xgboost_artifact_path: str | Path | None = DEFAULT_XGB_ARTIFACT_PATH,
    lightgbm_artifact_path: str | Path | None = DEFAULT_LGBM_ARTIFACT_PATH,
    logistic_artifact_path: str | Path | None = DEFAULT_LOGISTIC_ARTIFACT_PATH,
    baseline_metrics_path: str | Path | None = DEFAULT_BASELINE_METRICS_PATH,
    metrics_path: str | Path | None = DEFAULT_METRICS_PATH,
    population_percentiles_path: str | Path | None = DEFAULT_POPULATION_PERCENTILES_PATH,
    psi_report_path: str | Path | None = DEFAULT_PSI_REPORT_PATH,
    fairness_report_path: str | Path | None = DEFAULT_FAIRNESS_REPORT_PATH,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> ClassicalTrainingArtifacts:
    """Train the bounded classical model suite on the documented temporal split."""

    np.random.seed(random_state)
    resolved_dataset, resolved_dataset_path = _load_dataset(dataset, dataset_path)
    aligned_dataset, raw_text_embeddings = align_text_features_from_raw_text(resolved_dataset)
    validate_synthetic_dataset(
        aligned_dataset,
        expected_row_count=(
            len(aligned_dataset) if expected_row_count is None else expected_row_count
        ),
        minimum_test_rows=minimum_test_rows,
    )

    prepared = prepare_temporal_data(
        aligned_dataset,
        raw_text_embeddings=raw_text_embeddings,
        text_pca_random_state=random_state,
        text_pca_artifact_path=text_pca_artifact_path,
    )
    preprocessor = fit_preprocessor(
        prepared.train.X,
        artifact_path=preprocessor_artifact_path,
    )
    X_full_processed = transform_features(preprocessor, prepared.feature_frame)
    X_train_processed = transform_features(preprocessor, prepared.train.X)
    X_validation_processed = transform_features(preprocessor, prepared.validation.X)
    X_test_processed = transform_features(preprocessor, prepared.test.X)
    y_train = prepared.train.y.to_numpy(dtype=int)
    y_validation = prepared.validation.y.to_numpy(dtype=int)
    y_test = prepared.test.y.to_numpy(dtype=int)
    psi_report = build_psi_report_from_prepared_data(prepared)

    model_artifact_paths = {
        "random_forest": _optional_path(random_forest_artifact_path),
        "xgboost": _optional_path(xgboost_artifact_path),
        "lightgbm": _optional_path(lightgbm_artifact_path),
    }
    models = _build_classical_models(random_state=random_state)
    validation_probabilities: dict[str, np.ndarray] = {}
    test_probabilities: dict[str, np.ndarray] = {}
    model_stats: list[dict[str, Any]] = []
    fairness_candidate_test_probabilities: dict[str, np.ndarray] = {}
    evaluation_details: dict[str, dict[str, Any]] = {
        "validation_months_9_10": {},
        "test_months_11_12": {},
    }
    population_model_payloads: dict[str, dict[str, Any]] = {}

    for model_name in CLASSICAL_MODEL_ORDER:
        model = models[model_name]
        model.fit(X_train_processed, y_train)
        artifact_path = model_artifact_paths[model_name]
        if artifact_path is not None:
            _save_joblib(model, artifact_path)

        validation_probs = _predict_positive_class_probabilities(
            model_name,
            model.predict_proba(X_validation_processed)[:, 1],
        )
        test_probs = _predict_positive_class_probabilities(
            model_name,
            model.predict_proba(X_test_processed)[:, 1],
        )
        validation_probabilities[model_name] = validation_probs
        test_probabilities[model_name] = test_probs
        fairness_candidate_test_probabilities[model_name] = test_probs
        model_stats.extend(
            [
                compute_binary_classification_metrics(
                    y_validation,
                    validation_probs,
                    model_name=model_name,
                    model_type=CLASSICAL_MODEL_TYPE,
                    split="validation_months_9_10",
                ),
                compute_binary_classification_metrics(
                    y_test,
                    test_probs,
                    model_name=model_name,
                    model_type=CLASSICAL_MODEL_TYPE,
                    split="test_months_11_12",
                ),
            ]
        )
        evaluation_details["validation_months_9_10"][model_name] = (
            build_split_evaluation_details(
                y_validation,
                validation_probs,
                model_name=model_name,
                model_type=CLASSICAL_MODEL_TYPE,
                split="validation_months_9_10",
            )
        )
        evaluation_details["test_months_11_12"][model_name] = (
            build_split_evaluation_details(
                y_test,
                test_probs,
                model_name=model_name,
                model_type=CLASSICAL_MODEL_TYPE,
                split="test_months_11_12",
            )
        )
        population_model_payloads[model_name] = build_population_percentiles_payload(
            _predict_positive_class_probabilities(
                model_name,
                model.predict_proba(X_full_processed)[:, 1],
            ),
            model_name=model_name,
        )

    logistic_model = _load_joblib_if_present(logistic_artifact_path)
    if logistic_model is not None:
        logistic_validation_probs = _predict_positive_class_probabilities(
            "logistic_regression",
            logistic_model.predict_proba(X_validation_processed)[:, 1],
        )
        logistic_test_probs = _predict_positive_class_probabilities(
            "logistic_regression",
            logistic_model.predict_proba(X_test_processed)[:, 1],
        )
        fairness_candidate_test_probabilities["logistic_regression"] = logistic_test_probs
        evaluation_details["validation_months_9_10"]["logistic_regression"] = (
            build_split_evaluation_details(
                y_validation,
                logistic_validation_probs,
                model_name="logistic_regression",
                model_type=CLASSICAL_MODEL_TYPE,
                split="validation_months_9_10",
            )
        )
        evaluation_details["test_months_11_12"]["logistic_regression"] = (
            build_split_evaluation_details(
                y_test,
                logistic_test_probs,
                model_name="logistic_regression",
                model_type=CLASSICAL_MODEL_TYPE,
                split="test_months_11_12",
            )
        )
        population_model_payloads["logistic_regression"] = (
            build_population_percentiles_payload(
                _predict_positive_class_probabilities(
                    "logistic_regression",
                    logistic_model.predict_proba(X_full_processed)[:, 1],
                ),
                model_name="logistic_regression",
            )
        )

    baseline_metrics = _load_baseline_metrics(
        baseline_metrics_path=baseline_metrics_path,
        metrics_path=metrics_path,
    )
    existing_payload = _load_existing_metrics_payload(metrics_path)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_classical")
    split_row_counts = {
        "train": int(len(y_train)),
        "validation": int(len(y_validation)),
        "test": int(len(y_test)),
    }
    merged_model_stats = _merge_model_stats(
        existing_model_stats=existing_payload.get("model_stats", []),
        updated_model_stats=model_stats,
    )
    fairness_report, _ = build_fairness_report_for_candidate_probabilities(
        y_test,
        prepared.test.protected,
        fairness_candidate_test_probabilities,
        model_stats=merged_model_stats,
    )

    if metrics_path is not None:
        metrics_payload = {
            **{
                key: value
                for key, value in existing_payload.items()
                if key
                not in {
                    "run_id",
                    "split_row_counts",
                    "model_stats",
                    "baselines",
                    "evaluation_details",
                }
            },
            "run_id": run_id,
            "split_row_counts": split_row_counts,
            "model_stats": merged_model_stats,
            "baselines": baseline_metrics,
            "evaluation_details": merge_evaluation_details(
                existing_payload.get("evaluation_details"),
                evaluation_details,
            ),
        }
        _save_json(metrics_payload, metrics_path)

    if population_percentiles_path is not None:
        existing_population_payload = _load_existing_population_payload(
            population_percentiles_path
        )
        default_model_name = _resolve_population_default_model_name(
            model_stats=merged_model_stats,
            existing_payload=existing_population_payload,
            updated_model_payloads=population_model_payloads,
        )
        merged_population_payload = merge_population_percentiles_reports(
            existing_population_payload,
            population_model_payloads,
            default_model_name=default_model_name,
        )
        _save_json(merged_population_payload, population_percentiles_path)
    if psi_report_path is not None:
        _save_json(psi_report, psi_report_path)
    if fairness_report_path is not None:
        save_fairness_report(fairness_report, fairness_report_path)

    return ClassicalTrainingArtifacts(
        run_id=run_id,
        dataset_path=resolved_dataset_path,
        preprocessor_path=_optional_path(preprocessor_artifact_path),
        text_pca_path=_optional_path(text_pca_artifact_path),
        model_artifact_paths=model_artifact_paths,
        metrics_path=_optional_path(metrics_path),
        population_percentiles_path=_optional_path(population_percentiles_path),
        psi_report_path=_optional_path(psi_report_path),
        fairness_report_path=_optional_path(fairness_report_path),
        model_stats=model_stats,
        baseline_metrics=baseline_metrics,
        validation_probabilities=validation_probabilities,
        test_probabilities=test_probabilities,
    )


def _build_classical_models(*, random_state: int) -> dict[str, Any]:
    try:
        from lightgbm import LGBMClassifier
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "lightgbm is required to train the AlterScore classical model suite."
        ) from exc

    try:
        from xgboost import XGBClassifier
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "xgboost is required to train the AlterScore classical model suite."
        ) from exc

    return {
        "random_forest": RandomForestClassifier(
            class_weight="balanced_subsample",
            min_samples_leaf=4,
            n_estimators=300,
            n_jobs=1,
            random_state=random_state,
        ),
        "xgboost": XGBClassifier(
            colsample_bytree=1.0,
            eval_metric="logloss",
            learning_rate=0.05,
            max_depth=4,
            n_estimators=200,
            n_jobs=1,
            objective="binary:logistic",
            random_state=random_state,
            subsample=1.0,
            tree_method="hist",
            verbosity=0,
        ),
        "lightgbm": LGBMClassifier(
            bagging_seed=random_state,
            colsample_bytree=1.0,
            data_random_seed=random_state,
            deterministic=True,
            feature_fraction_seed=random_state,
            force_col_wise=True,
            learning_rate=0.05,
            n_estimators=200,
            n_jobs=1,
            objective="binary",
            random_state=random_state,
            subsample=1.0,
            verbose=-1,
        ),
    }


def _predict_positive_class_probabilities(
    model_name: str,
    probabilities: np.ndarray | list[float],
) -> np.ndarray:
    probability_array = np.asarray(probabilities, dtype=float)
    if np.isnan(probability_array).any():
        raise ValueError(f"{model_name} produced NaN predicted probabilities.")
    if ((probability_array < 0.0) | (probability_array > 1.0)).any():
        raise ValueError(
            f"{model_name} produced probabilities outside the documented [0, 1] range."
        )
    return probability_array


def _load_baseline_metrics(
    *,
    baseline_metrics_path: str | Path | None,
    metrics_path: str | Path | None,
) -> list[dict[str, Any]]:
    metrics_payload = _load_existing_metrics_payload(metrics_path)
    baselines = metrics_payload.get("baselines")
    if isinstance(baselines, list) and baselines:
        return baselines

    if baseline_metrics_path is None:
        raise FileNotFoundError(
            "Baseline metrics are required before classical training. "
            "Run train_baselines first or provide baseline_metrics_path."
        )

    resolved_baseline_metrics_path = Path(baseline_metrics_path)
    if not resolved_baseline_metrics_path.is_file():
        raise FileNotFoundError(
            f"Baseline metrics not found at {resolved_baseline_metrics_path}. "
            "Run train_baselines first."
        )

    baseline_metrics = json.loads(
        resolved_baseline_metrics_path.read_text(encoding="utf-8")
    )
    if not isinstance(baseline_metrics, list) or not baseline_metrics:
        raise ValueError("Baseline metrics payload must be a non-empty JSON list.")
    return baseline_metrics


def _load_existing_metrics_payload(
    metrics_path: str | Path | None,
) -> dict[str, Any]:
    if metrics_path is None:
        return {}

    resolved_metrics_path = Path(metrics_path)
    if not resolved_metrics_path.is_file():
        return {}

    payload = json.loads(resolved_metrics_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("metrics.json payload must be a JSON object.")
    return payload


def _load_existing_population_payload(
    population_percentiles_path: str | Path | None,
) -> dict[str, Any] | None:
    if population_percentiles_path is None:
        return None

    resolved_population_percentiles_path = Path(population_percentiles_path)
    if not resolved_population_percentiles_path.is_file():
        return None

    payload = json.loads(
        resolved_population_percentiles_path.read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise ValueError(
            "population_percentiles.json payload must be a JSON object."
        )
    return payload


def _merge_model_stats(
    *,
    existing_model_stats: list[dict[str, Any]],
    updated_model_stats: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    updated_lookup = {
        (item["model_name"], item["split"]): item for item in updated_model_stats
    }
    merged_model_stats: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()

    for item in existing_model_stats:
        key = (str(item.get("model_name")), str(item.get("split")))
        replacement = updated_lookup.get(key)
        if replacement is not None:
            merged_model_stats.append(replacement)
            seen_keys.add(key)
            continue
        merged_model_stats.append(item)

    for item in updated_model_stats:
        key = (item["model_name"], item["split"])
        if key in seen_keys:
            continue
        merged_model_stats.append(item)
        seen_keys.add(key)

    return merged_model_stats


def _load_dataset(
    dataset: pd.DataFrame | None,
    dataset_path: str | Path | None,
) -> tuple[pd.DataFrame, Path | None]:
    if dataset is not None:
        return dataset.copy(), None

    resolved_dataset_path = Path(dataset_path or DEFAULT_DATASET_PATH)
    if not resolved_dataset_path.is_file():
        raise FileNotFoundError(
            f"Dataset not found at {resolved_dataset_path}. "
            "Run the synthetic dataset materialization command first."
        )
    return pd.read_csv(resolved_dataset_path), resolved_dataset_path


def _optional_path(path: str | Path | None) -> Path | None:
    return None if path is None else Path(path)


def _resolve_population_default_model_name(
    *,
    model_stats: list[dict[str, Any]],
    existing_payload: dict[str, Any] | None,
    updated_model_payloads: dict[str, dict[str, Any]],
) -> str:
    available_model_names = set(updated_model_payloads)
    if isinstance(existing_payload, dict):
        existing_models = existing_payload.get("models")
        if isinstance(existing_models, dict):
            available_model_names.update(
                model_name
                for model_name, payload in existing_models.items()
                if isinstance(model_name, str) and isinstance(payload, dict)
            )

    selected_model_name = select_best_test_auc_model(
        model_stats,
        candidate_model_names=available_model_names,
    )
    if selected_model_name is not None:
        return selected_model_name

    existing_default = None if existing_payload is None else existing_payload.get("default_model_name")
    if isinstance(existing_default, str) and existing_default in available_model_names:
        return existing_default

    if available_model_names:
        return sorted(available_model_names)[0]

    raise ValueError("At least one population percentile model payload is required.")


def _load_joblib_if_present(path: str | Path | None) -> Any | None:
    if path is None:
        return None

    resolved_path = Path(path)
    if not resolved_path.is_file():
        return None

    return joblib.load(resolved_path)


def _save_joblib(artifact: object, path: str | Path) -> None:
    artifact_path = Path(path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, artifact_path)


def _save_json(payload: Any, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


__all__ = [
    "CLASSICAL_MODEL_ORDER",
    "CLASSICAL_MODEL_TYPE",
    "DEFAULT_DATASET_PATH",
    "DEFAULT_FAIRNESS_REPORT_PATH",
    "DEFAULT_LGBM_ARTIFACT_PATH",
    "DEFAULT_RF_ARTIFACT_PATH",
    "DEFAULT_XGB_ARTIFACT_PATH",
    "DEFAULT_PSI_REPORT_PATH",
    "ClassicalTrainingArtifacts",
    "NUMERIC_METRIC_FIELDS",
    "train_classical_models",
]
