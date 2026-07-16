"""Dataset materialization and validation-summary helpers for AlterScore."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Final

import pandas as pd

from backend.app.core.paths import DATA_VALIDATION_DIR, RAW_DATA_DIR
from backend.ml.data_generation.generator import (
    DEFAULT_ROW_COUNT,
    DEFAULT_SEED,
    TEMPORAL_SPLIT_MONTHS,
    generate_synthetic_dataset,
)
from backend.ml.data_generation.validators import (
    MINIMUM_TEST_ROWS,
    validate_synthetic_dataset,
)
from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    PROTECTED_FEATURES,
    TARGET,
    TEMPORAL_METADATA,
)

DEFAULT_DATASET_OUTPUT_PATH: Final[Path] = RAW_DATA_DIR / "synthetic_dataset.csv"
DEFAULT_VALIDATION_SUMMARY_PATH: Final[Path] = (
    DATA_VALIDATION_DIR / "validation_summary.json"
)
WEAK_FEATURE_CORRELATION_THRESHOLD: Final[float] = 0.05
LEAKAGE_CORRELATION_THRESHOLD: Final[float] = 0.65
PROTECTED_CORRELATION_THRESHOLD: Final[float] = 0.15


@dataclass(frozen=True)
class MaterializedDatasetArtifacts:
    dataset: pd.DataFrame
    dataset_path: Path
    validation_summary_path: Path
    validation_summary: dict[str, Any]


def materialize_synthetic_dataset(
    *,
    row_count: int = DEFAULT_ROW_COUNT,
    seed: int = DEFAULT_SEED,
    dataset_path: str | Path | None = None,
    validation_summary_path: str | Path | None = None,
    minimum_test_rows: int = MINIMUM_TEST_ROWS,
) -> MaterializedDatasetArtifacts:
    """Generate, validate, and persist the synthetic dataset plus summary JSON."""

    dataset = generate_synthetic_dataset(row_count=row_count, seed=seed)
    summary = build_validation_summary(
        dataset,
        expected_row_count=row_count,
        minimum_test_rows=minimum_test_rows,
        seed=seed,
    )

    resolved_dataset_path = Path(dataset_path or DEFAULT_DATASET_OUTPUT_PATH)
    resolved_summary_path = Path(
        validation_summary_path or DEFAULT_VALIDATION_SUMMARY_PATH
    )
    resolved_dataset_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_summary_path.parent.mkdir(parents=True, exist_ok=True)

    dataset.to_csv(resolved_dataset_path, index=False)
    resolved_summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    return MaterializedDatasetArtifacts(
        dataset=dataset,
        dataset_path=resolved_dataset_path,
        validation_summary_path=resolved_summary_path,
        validation_summary=summary,
    )


def build_validation_summary(
    dataset: pd.DataFrame,
    *,
    expected_row_count: int | None = None,
    minimum_test_rows: int = MINIMUM_TEST_ROWS,
    seed: int | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable validation summary for the synthetic dataset."""

    validation = validate_synthetic_dataset(
        dataset,
        expected_row_count=(
            len(dataset) if expected_row_count is None else expected_row_count
        ),
        minimum_test_rows=minimum_test_rows,
    )
    numeric_correlations = _compute_numeric_feature_label_correlations(dataset)
    categorical_correlations = _compute_dummy_label_correlations(
        dataset, CATEGORICAL_FEATURES
    )
    protected_correlations = _compute_dummy_label_correlations(
        dataset, PROTECTED_FEATURES
    )

    weak_features = [
        feature_name
        for feature_name, correlation in numeric_correlations.items()
        if abs(correlation) < WEAK_FEATURE_CORRELATION_THRESHOLD
    ]
    possible_leakage_features = [
        feature_name
        for feature_name, correlation in numeric_correlations.items()
        if abs(correlation) > LEAKAGE_CORRELATION_THRESHOLD
    ]
    concerning_protected_correlations = [
        feature_name
        for feature_name, correlation in protected_correlations.items()
        if abs(correlation) > PROTECTED_CORRELATION_THRESHOLD
    ]

    return {
        "seed": seed,
        "row_count": validation["row_count"],
        "default_rate": validation["default_rate"],
        "months_11_12_rows": validation["test_rows"],
        "month_count": validation["month_count"],
        "split_row_counts": {
            "train": int(
                dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["train"]).sum()
            ),
            "validation": int(
                dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["validation"]).sum()
            ),
            "test": int(
                dataset["cohort_month"].isin(TEMPORAL_SPLIT_MONTHS["test"]).sum()
            ),
        },
        "shape": [int(dataset.shape[0]), int(dataset.shape[1])],
        "dtypes": {
            column_name: str(dtype) for column_name, dtype in dataset.dtypes.items()
        },
        "missing_values": {
            column_name: int(count)
            for column_name, count in dataset.isnull().sum().items()
        },
        "feature_list_checks": {
            "model_feature_count": len(ALL_MODEL_FEATURES),
            "protected_feature_count": len(PROTECTED_FEATURES),
            "temporal_metadata_count": len(TEMPORAL_METADATA),
            "protected_attributes_excluded_from_model_features": True,
            "temporal_metadata_excluded_from_model_features": True,
            "target_excluded_from_model_features": True,
        },
        "numeric_feature_stats": _compute_numeric_feature_stats(dataset),
        "numeric_feature_label_correlations": numeric_correlations,
        "categorical_feature_label_correlations": categorical_correlations,
        "protected_feature_label_correlations": protected_correlations,
        "weak_numeric_features": weak_features,
        "possible_leakage_numeric_features": possible_leakage_features,
        "concerning_protected_correlations": concerning_protected_correlations,
    }


def _compute_numeric_feature_stats(
    dataset: pd.DataFrame,
) -> dict[str, dict[str, float]]:
    stats: dict[str, dict[str, float]] = {}
    for feature_name in NUMERIC_FEATURES:
        feature_series = pd.to_numeric(dataset[feature_name], errors="coerce")
        stats[feature_name] = {
            "min": _safe_float(feature_series.min()),
            "max": _safe_float(feature_series.max()),
            "mean": _safe_float(feature_series.mean()),
            "std": _safe_float(feature_series.std(ddof=0)),
            "skew": _safe_float(feature_series.skew()),
        }
    return stats


def _compute_numeric_feature_label_correlations(
    dataset: pd.DataFrame,
) -> dict[str, float]:
    label = pd.to_numeric(dataset[TARGET], errors="coerce")
    correlations: dict[str, float] = {}
    for feature_name in NUMERIC_FEATURES:
        feature_series = pd.to_numeric(dataset[feature_name], errors="coerce")
        correlations[feature_name] = _safe_float(feature_series.corr(label))
    return correlations


def _compute_dummy_label_correlations(
    dataset: pd.DataFrame,
    feature_names: list[str],
) -> dict[str, float]:
    label = pd.to_numeric(dataset[TARGET], errors="coerce")
    correlations: dict[str, float] = {}
    for feature_name in feature_names:
        dummy_frame = pd.get_dummies(
            dataset[feature_name],
            prefix=feature_name,
            dtype=float,
        )
        for dummy_name in dummy_frame.columns:
            correlations[dummy_name] = _safe_float(dummy_frame[dummy_name].corr(label))
    return correlations


def _safe_float(value: Any) -> float:
    if pd.isna(value):
        return 0.0
    return float(value)


__all__ = [
    "DEFAULT_DATASET_OUTPUT_PATH",
    "DEFAULT_VALIDATION_SUMMARY_PATH",
    "MaterializedDatasetArtifacts",
    "build_validation_summary",
    "materialize_synthetic_dataset",
]
