"""Offline PSI drift report generation for AlterScore temporal splits."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd

from backend.app.core.paths import MODEL_REPORTS_DIR, RAW_DATA_DIR
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES
from backend.ml.preprocessing.pipeline import (
    PreparedTemporalData,
    TEXT_PCA_RANDOM_STATE,
    align_text_features_from_raw_text,
    prepare_temporal_data,
)

DEFAULT_DATASET_PATH: Final[Path] = RAW_DATA_DIR / "synthetic_dataset.csv"
DEFAULT_PSI_REPORT_PATH: Final[Path] = MODEL_REPORTS_DIR / "psi_report.json"
PSI_BIN_COUNT: Final[int] = 10
PSI_EPSILON: Final[float] = 1e-6
TOP_DRIFTED_FEATURE_COUNT: Final[int] = 10
PSI_THRESHOLDS: Final[dict[str, float]] = {
    "stable_below": 0.2,
    "watch_below": 0.3,
    "alert_at_or_above": 0.3,
}


@dataclass(frozen=True)
class PsiReportArtifacts:
    dataset_path: Path | None
    report_path: Path | None
    max_psi: float
    verdict: str


def generate_psi_report(
    dataset: pd.DataFrame | None = None,
    *,
    dataset_path: str | Path | None = None,
    report_path: str | Path | None = DEFAULT_PSI_REPORT_PATH,
    text_pca_random_state: int = TEXT_PCA_RANDOM_STATE,
) -> PsiReportArtifacts:
    """Build and optionally persist the PSI drift report from the offline dataset."""

    resolved_dataset, resolved_dataset_path = _load_dataset(dataset, dataset_path)
    aligned_dataset, raw_text_embeddings = align_text_features_from_raw_text(
        resolved_dataset
    )
    prepared = prepare_temporal_data(
        aligned_dataset,
        raw_text_embeddings=raw_text_embeddings,
        text_pca_random_state=text_pca_random_state,
        text_pca_artifact_path=None,
    )
    report = build_psi_report_from_prepared_data(prepared)

    resolved_report_path = None if report_path is None else Path(report_path)
    if resolved_report_path is not None:
        _save_json(report, resolved_report_path)

    return PsiReportArtifacts(
        dataset_path=resolved_dataset_path,
        report_path=resolved_report_path,
        max_psi=float(report["max_psi"]),
        verdict=str(report["verdict"]),
    )


def build_psi_report_from_prepared_data(
    prepared: PreparedTemporalData,
    *,
    top_drifted_feature_count: int = TOP_DRIFTED_FEATURE_COUNT,
) -> dict[str, Any]:
    """Build the documented PSI report payload from prepared train/test features."""

    train_frame = prepared.train.X.loc[:, ALL_MODEL_FEATURES].copy()
    test_frame = prepared.test.X.loc[:, ALL_MODEL_FEATURES].copy()
    all_features = _build_feature_psi_table(train_frame, test_frame)
    max_psi = 0.0 if not all_features else float(all_features[0]["psi"])

    return {
        "max_psi": round(max_psi, 4),
        "verdict": determine_drift_verdict(max_psi),
        "thresholds": dict(PSI_THRESHOLDS),
        "top_drifted_features": all_features[:top_drifted_feature_count],
        "all_features": all_features,
    }


def determine_drift_status(psi_value: float) -> str:
    """Map a PSI value to the documented drift status buckets."""

    if psi_value >= PSI_THRESHOLDS["alert_at_or_above"]:
        return "alert"
    if psi_value >= PSI_THRESHOLDS["stable_below"]:
        return "watch"
    return "stable"


def determine_drift_verdict(max_psi: float) -> str:
    """Map the maximum PSI value to the overall report verdict."""

    return determine_drift_status(max_psi)


def calculate_feature_psi(
    expected: pd.Series,
    actual: pd.Series,
    *,
    bin_count: int = PSI_BIN_COUNT,
) -> float:
    """Compute PSI for one feature using deterministic train-derived bins."""

    if pd.api.types.is_numeric_dtype(expected) and pd.api.types.is_numeric_dtype(
        actual
    ):
        return _calculate_numeric_psi(expected, actual, bin_count=bin_count)
    return _calculate_categorical_psi(expected, actual)


def _build_feature_psi_table(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    feature_rows = [
        {
            "feature": feature_name,
            "psi": round(
                calculate_feature_psi(
                    train_frame[feature_name],
                    test_frame[feature_name],
                ),
                4,
            ),
        }
        for feature_name in ALL_MODEL_FEATURES
    ]

    for feature_row in feature_rows:
        feature_row["status"] = determine_drift_status(float(feature_row["psi"]))

    return sorted(
        feature_rows,
        key=lambda item: (-float(item["psi"]), str(item["feature"])),
    )


def _calculate_numeric_psi(
    expected: pd.Series,
    actual: pd.Series,
    *,
    bin_count: int,
) -> float:
    expected_values = expected.to_numpy(dtype=float, copy=False)
    actual_values = actual.to_numpy(dtype=float, copy=False)
    _assert_finite(expected_values, feature_name=str(expected.name))
    _assert_finite(actual_values, feature_name=str(actual.name))

    bin_edges = _resolve_numeric_bin_edges(expected_values, bin_count=bin_count)
    if bin_edges is None:
        return 0.0

    expected_bin_ids = np.digitize(expected_values, bin_edges[1:-1], right=True)
    actual_bin_ids = np.digitize(actual_values, bin_edges[1:-1], right=True)
    bin_total = len(bin_edges) - 1

    expected_counts = np.bincount(expected_bin_ids, minlength=bin_total).astype(float)
    actual_counts = np.bincount(actual_bin_ids, minlength=bin_total).astype(float)
    return _calculate_psi_from_counts(expected_counts, actual_counts)


def _calculate_categorical_psi(expected: pd.Series, actual: pd.Series) -> float:
    expected_values = expected.fillna("__MISSING__").astype(str)
    actual_values = actual.fillna("__MISSING__").astype(str)
    categories = sorted(set(expected_values.tolist()) | set(actual_values.tolist()))

    expected_counts = (
        expected_values.value_counts(sort=False)
        .reindex(categories, fill_value=0)
        .to_numpy(dtype=float)
    )
    actual_counts = (
        actual_values.value_counts(sort=False)
        .reindex(categories, fill_value=0)
        .to_numpy(dtype=float)
    )
    return _calculate_psi_from_counts(expected_counts, actual_counts)


def _resolve_numeric_bin_edges(
    expected_values: np.ndarray,
    *,
    bin_count: int,
) -> np.ndarray | None:
    minimum = float(np.min(expected_values))
    maximum = float(np.max(expected_values))
    if np.isclose(minimum, maximum):
        return None

    quantiles = np.linspace(0.0, 1.0, bin_count + 1, dtype=float)
    internal_edges = np.quantile(expected_values, quantiles[1:-1])
    internal_edges = np.unique(np.asarray(internal_edges, dtype=float))
    internal_edges = internal_edges[
        (internal_edges > minimum) & (internal_edges < maximum)
    ]

    if internal_edges.size == 0:
        internal_edges = np.asarray([(minimum + maximum) / 2.0], dtype=float)

    return np.concatenate(([-np.inf], internal_edges, [np.inf]))


def _calculate_psi_from_counts(
    expected_counts: np.ndarray,
    actual_counts: np.ndarray,
) -> float:
    expected_distribution = expected_counts / float(expected_counts.sum())
    actual_distribution = actual_counts / float(actual_counts.sum())
    expected_distribution = np.where(
        expected_distribution <= 0.0,
        PSI_EPSILON,
        expected_distribution,
    )
    actual_distribution = np.where(
        actual_distribution <= 0.0,
        PSI_EPSILON,
        actual_distribution,
    )

    psi = np.sum(
        (actual_distribution - expected_distribution)
        * np.log(actual_distribution / expected_distribution)
    )
    return max(float(psi), 0.0)


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


def _assert_finite(values: np.ndarray, *, feature_name: str) -> None:
    if not np.isfinite(values).all():
        raise ValueError(f"PSI feature '{feature_name}' contains non-finite values.")


def _save_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


__all__ = [
    "DEFAULT_DATASET_PATH",
    "DEFAULT_PSI_REPORT_PATH",
    "PSI_THRESHOLDS",
    "PsiReportArtifacts",
    "build_psi_report_from_prepared_data",
    "calculate_feature_psi",
    "determine_drift_status",
    "determine_drift_verdict",
    "generate_psi_report",
]
