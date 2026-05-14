"""Baseline training loop for AlterScore temporal splits."""

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
    MODEL_REPORTS_DIR,
    RAW_DATA_DIR,
)
from backend.ml.explainability.dice_explainer import (
    DEFAULT_DICE_EXPLAINER_PATH,
    build_default_persisted_dice_explainer,
    save_persisted_dice_explainer,
)
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
    build_population_percentiles_report,
    build_split_evaluation_details,
    compute_binary_classification_metrics,
    optimal_threshold,
)
from backend.ml.explainability.global_importance import (
    DEFAULT_GLOBAL_IMPORTANCE_PATH,
    build_global_importance_report_for_candidate_models,
    save_global_importance_report,
)
from backend.ml.preprocessing.pipeline import (
    DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    DEFAULT_TEXT_PCA_ARTIFACT_PATH,
    align_text_features_from_raw_text,
    fit_preprocessor,
    prepare_temporal_data,
    transform_features,
)

DEFAULT_DATASET_PATH: Final[Path] = RAW_DATA_DIR / "synthetic_dataset.csv"
DEFAULT_LOGISTIC_ARTIFACT_PATH: Final[Path] = MODEL_ARTIFACTS_DIR / "logistic_best.pkl"
DEFAULT_BASELINE_METRICS_PATH: Final[Path] = MODEL_REPORTS_DIR / "baseline_metrics.json"
DEFAULT_METRICS_PATH: Final[Path] = MODEL_REPORTS_DIR / "metrics.json"
DEFAULT_POPULATION_PERCENTILES_PATH: Final[Path] = (
    MODEL_REPORTS_DIR / "population_percentiles.json"
)
BASELINE_MODEL_ORDER: Final[tuple[str, ...]] = (
    "majority_class",
    "logistic_regression",
    "simulated_loan_officer",
)
DEFAULT_RANDOM_STATE: Final[int] = 42


@dataclass(frozen=True)
class BaselineTrainingArtifacts:
    run_id: str
    dataset_path: Path | None
    preprocessor_path: Path | None
    text_pca_path: Path | None
    logistic_model_path: Path | None
    baseline_metrics_path: Path | None
    metrics_path: Path | None
    population_percentiles_path: Path | None
    psi_report_path: Path | None
    fairness_report_path: Path | None
    global_importance_path: Path | None
    dice_explainer_path: Path | None
    model_stats: list[dict[str, Any]]
    baseline_metrics: list[dict[str, Any]]


class MajorityClassBaseline:
    """Predict the majority training class with full confidence."""

    def __init__(self) -> None:
        self._repay_probability = 1.0

    def fit(self, y_train: pd.Series | np.ndarray | list[int]) -> "MajorityClassBaseline":
        values = np.asarray(y_train, dtype=int)
        repay_rate = float(values.mean()) if values.size else 1.0
        self._repay_probability = 1.0 if repay_rate >= 0.5 else 0.0
        return self

    def predict_proba(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        row_count = len(X)
        probabilities = np.full(row_count, self._repay_probability, dtype=float)
        return np.column_stack([1.0 - probabilities, probabilities])


class SimulatedLoanOfficer:
    """A deterministic noisy heuristic used only as a benchmark."""

    REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
        "numeracy_score",
        "financial_literacy_score",
        "conscientiousness_score",
        "social_capital_score",
        "honesty_score",
        "impulsivity_index",
    )

    def __init__(self, *, random_state: int = DEFAULT_RANDOM_STATE) -> None:
        self.random_state = random_state

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series | np.ndarray | list[int] | None = None,
    ) -> "SimulatedLoanOfficer":
        self._assert_required_columns(X_train)
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        self._assert_required_columns(X)
        heuristic = (
            0.25 * X["numeracy_score"].to_numpy(dtype=float)
            + 0.20 * X["financial_literacy_score"].to_numpy(dtype=float)
            + 0.20 * X["conscientiousness_score"].to_numpy(dtype=float)
            + 0.15 * X["social_capital_score"].to_numpy(dtype=float)
            + 0.10 * X["honesty_score"].to_numpy(dtype=float)
            + 0.10 * (1.0 - X["impulsivity_index"].to_numpy(dtype=float))
        )
        noise = np.random.default_rng(self.random_state).normal(0.0, 0.08, len(X))
        repay_probability = np.clip(heuristic + noise, 0.0, 1.0)
        return np.column_stack([1.0 - repay_probability, repay_probability])

    def _assert_required_columns(self, X: pd.DataFrame) -> None:
        missing_columns = [
            column_name
            for column_name in self.REQUIRED_COLUMNS
            if column_name not in X.columns
        ]
        if missing_columns:
            raise ValueError(
                f"SimulatedLoanOfficer is missing required columns: {missing_columns}"
            )


def train_baselines(
    dataset: pd.DataFrame | None = None,
    *,
    dataset_path: str | Path | None = None,
    expected_row_count: int | None = None,
    minimum_test_rows: int = MINIMUM_TEST_ROWS,
    preprocessor_artifact_path: str | Path | None = DEFAULT_PREPROCESSOR_ARTIFACT_PATH,
    text_pca_artifact_path: str | Path | None = DEFAULT_TEXT_PCA_ARTIFACT_PATH,
    logistic_artifact_path: str | Path | None = DEFAULT_LOGISTIC_ARTIFACT_PATH,
    baseline_metrics_path: str | Path | None = DEFAULT_BASELINE_METRICS_PATH,
    metrics_path: str | Path | None = DEFAULT_METRICS_PATH,
    population_percentiles_path: str | Path | None = DEFAULT_POPULATION_PERCENTILES_PATH,
    psi_report_path: str | Path | None = DEFAULT_PSI_REPORT_PATH,
    fairness_report_path: str | Path | None = DEFAULT_FAIRNESS_REPORT_PATH,
    global_importance_path: str | Path | None = DEFAULT_GLOBAL_IMPORTANCE_PATH,
    dice_explainer_path: str | Path | None = DEFAULT_DICE_EXPLAINER_PATH,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> BaselineTrainingArtifacts:
    """Fit the first baseline suite on the documented temporal splits."""

    np.random.seed(random_state)
    resolved_dataset, resolved_dataset_path = _load_dataset(dataset, dataset_path)
    aligned_dataset, raw_text_embeddings = align_text_features_from_raw_text(resolved_dataset)
    validate_synthetic_dataset(
        aligned_dataset,
        expected_row_count=len(aligned_dataset) if expected_row_count is None else expected_row_count,
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
    psi_report = build_psi_report_from_prepared_data(prepared)

    majority_model = MajorityClassBaseline().fit(prepared.train.y)
    logistic_model = LogisticRegression(
        class_weight="balanced",
        max_iter=1_000,
        random_state=random_state,
        solver="liblinear",
    )
    logistic_model.fit(X_train_processed, prepared.train.y.to_numpy(dtype=int))
    simulated_model = SimulatedLoanOfficer(random_state=random_state).fit(prepared.train.X)

    if logistic_artifact_path is not None:
        _save_joblib(logistic_model, logistic_artifact_path)

    logistic_train_probs = logistic_model.predict_proba(X_train_processed)[:, 1]
    logistic_validation_probs = logistic_model.predict_proba(X_validation_processed)[:, 1]
    logistic_test_probs = logistic_model.predict_proba(X_test_processed)[:, 1]
    logistic_population_probs = logistic_model.predict_proba(X_full_processed)[:, 1]

    logistic_train_metrics = compute_binary_classification_metrics(
        prepared.train.y.to_numpy(dtype=int),
        logistic_train_probs,
        model_name="logistic_regression",
        model_type="classical",
        split="train_months_1_8",
    )
    logistic_validation_threshold = optimal_threshold(
        prepared.validation.y.to_numpy(dtype=int),
        logistic_validation_probs,
    )
    logistic_validation_metrics = compute_binary_classification_metrics(
        prepared.validation.y.to_numpy(dtype=int),
        logistic_validation_probs,
        model_name="logistic_regression",
        model_type="classical",
        split="validation_months_9_10",
        threshold=logistic_validation_threshold,
    )
    logistic_test_metrics = compute_binary_classification_metrics(
        prepared.test.y.to_numpy(dtype=int),
        logistic_test_probs,
        model_name="logistic_regression",
        model_type="classical",
        split="test_months_11_12",
        threshold=logistic_validation_threshold,
    )

    comparison_metrics = {
        "majority_class": compute_binary_classification_metrics(
            prepared.test.y.to_numpy(dtype=int),
            majority_model.predict_proba(prepared.test.X)[:, 1],
            model_name="majority_class",
            model_type="baseline",
            split="test_months_11_12",
        ),
        "logistic_regression": compute_binary_classification_metrics(
            prepared.test.y.to_numpy(dtype=int),
            logistic_test_probs,
            model_name="logistic_regression",
            model_type="baseline",
            split="test_months_11_12",
        ),
        "simulated_loan_officer": compute_binary_classification_metrics(
            prepared.test.y.to_numpy(dtype=int),
            simulated_model.predict_proba(prepared.test.X)[:, 1],
            model_name="simulated_loan_officer",
            model_type="baseline",
            split="test_months_11_12",
        ),
    }
    loan_officer_auc = comparison_metrics["simulated_loan_officer"]["auc_roc"]
    baseline_metrics = [
        _build_baseline_comparison_item(
            comparison_metrics[model_name],
            loan_officer_auc=loan_officer_auc,
        )
        for model_name in BASELINE_MODEL_ORDER
    ]

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_baselines")
    model_stats = [
        logistic_train_metrics,
        logistic_validation_metrics,
        logistic_test_metrics,
    ]
    global_importance_report, _ = build_global_importance_report_for_candidate_models(
        {"logistic_regression": logistic_model},
        train_processed_features=X_train_processed,
        test_processed_features=X_test_processed,
        model_stats=model_stats,
        candidate_model_types={"logistic_regression": "classical"},
    )
    fairness_report, _ = build_fairness_report_for_candidate_probabilities(
        prepared.test.y.to_numpy(dtype=int),
        prepared.test.protected,
        {"logistic_regression": logistic_test_probs},
        model_stats=model_stats,
        feature_frame=prepared.test.X,
    )
    evaluation_details = {
        "validation_months_9_10": {
            "logistic_regression": build_split_evaluation_details(
                prepared.validation.y.to_numpy(dtype=int),
                logistic_validation_probs,
                model_name="logistic_regression",
                model_type="classical",
                split="validation_months_9_10",
                threshold=logistic_validation_threshold,
            )
        },
        "test_months_11_12": {
            "logistic_regression": build_split_evaluation_details(
                prepared.test.y.to_numpy(dtype=int),
                logistic_test_probs,
                model_name="logistic_regression",
                model_type="classical",
                split="test_months_11_12",
                threshold=logistic_validation_threshold,
            )
        },
    }
    population_percentiles_payload = build_population_percentiles_report(
        {
            "logistic_regression": build_population_percentiles_payload(
                logistic_population_probs,
                model_name="logistic_regression",
            )
        },
        default_model_name="logistic_regression",
    )
    metrics_payload = {
        "run_id": run_id,
        "split_row_counts": {
            "train": int(len(prepared.train.y)),
            "validation": int(len(prepared.validation.y)),
            "test": int(len(prepared.test.y)),
        },
        "model_stats": model_stats,
        "baselines": baseline_metrics,
        "evaluation_details": evaluation_details,
    }

    if baseline_metrics_path is not None:
        _save_json(baseline_metrics, baseline_metrics_path)
    if metrics_path is not None:
        _save_json(metrics_payload, metrics_path)
    if population_percentiles_path is not None:
        _save_json(population_percentiles_payload, population_percentiles_path)
    if psi_report_path is not None:
        _save_json(psi_report, psi_report_path)
    if fairness_report_path is not None:
        save_fairness_report(fairness_report, fairness_report_path)
    if global_importance_path is not None:
        save_global_importance_report(global_importance_report, global_importance_path)
    if dice_explainer_path is not None:
        save_persisted_dice_explainer(
            build_default_persisted_dice_explainer(model_name="logistic_regression"),
            dice_explainer_path,
        )

    return BaselineTrainingArtifacts(
        run_id=run_id,
        dataset_path=resolved_dataset_path,
        preprocessor_path=None if preprocessor_artifact_path is None else Path(preprocessor_artifact_path),
        text_pca_path=None if text_pca_artifact_path is None else Path(text_pca_artifact_path),
        logistic_model_path=None if logistic_artifact_path is None else Path(logistic_artifact_path),
        baseline_metrics_path=None if baseline_metrics_path is None else Path(baseline_metrics_path),
        metrics_path=None if metrics_path is None else Path(metrics_path),
        population_percentiles_path=(
            None if population_percentiles_path is None else Path(population_percentiles_path)
        ),
        psi_report_path=None if psi_report_path is None else Path(psi_report_path),
        fairness_report_path=(
            None if fairness_report_path is None else Path(fairness_report_path)
        ),
        global_importance_path=(
            None if global_importance_path is None else Path(global_importance_path)
        ),
        dice_explainer_path=(
            None if dice_explainer_path is None else Path(dice_explainer_path)
        ),
        model_stats=model_stats,
        baseline_metrics=baseline_metrics,
    )


def _build_baseline_comparison_item(
    metrics: dict[str, Any],
    *,
    loan_officer_auc: float,
) -> dict[str, Any]:
    return {
        "model_name": metrics["model_name"],
        "model_type": "baseline",
        "auc_roc": metrics["auc_roc"],
        "ks_statistic": metrics["ks_statistic"],
        "brier_score": metrics["brier_score"],
        "expected_calibration_error": metrics["expected_calibration_error"],
        "lift_vs_loan_officer": round(metrics["auc_roc"] - loan_officer_auc, 4),
    }


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


def _save_joblib(artifact: object, path: str | Path) -> None:
    artifact_path = Path(path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, artifact_path)


def _save_json(payload: Any, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


__all__ = [
    "BASELINE_MODEL_ORDER",
    "BaselineTrainingArtifacts",
    "DEFAULT_BASELINE_METRICS_PATH",
    "DEFAULT_DATASET_PATH",
    "DEFAULT_DICE_EXPLAINER_PATH",
    "DEFAULT_FAIRNESS_REPORT_PATH",
    "DEFAULT_GLOBAL_IMPORTANCE_PATH",
    "DEFAULT_LOGISTIC_ARTIFACT_PATH",
    "DEFAULT_METRICS_PATH",
    "DEFAULT_POPULATION_PERCENTILES_PATH",
    "DEFAULT_PSI_REPORT_PATH",
    "DEFAULT_RANDOM_STATE",
    "MajorityClassBaseline",
    "SimulatedLoanOfficer",
    "train_baselines",
]
