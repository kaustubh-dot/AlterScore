"""Validation helpers for AlterScore synthetic data generation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

import pandas as pd

from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    PROTECTED_FEATURES,
    TARGET,
    TEMPORAL_METADATA,
)

EXPECTED_ROW_COUNT: Final[int] = 10_000
DEFAULT_RATE_BOUNDS: Final[tuple[float, float]] = (0.30, 0.45)
MINIMUM_TEST_ROWS: Final[int] = 1_000
VALID_COHORT_MONTHS: Final[set[int]] = set(range(1, 13))
REQUIRED_DATASET_COLUMNS: Final[list[str]] = [
    *ALL_MODEL_FEATURES,
    *PROTECTED_FEATURES,
    *TEMPORAL_METADATA,
    TARGET,
]


def validate_synthetic_dataset(
    dataset: pd.DataFrame,
    model_features: Sequence[str] | None = None,
    expected_row_count: int = EXPECTED_ROW_COUNT,
    minimum_test_rows: int = MINIMUM_TEST_ROWS,
) -> dict[str, float | int]:
    """Run the required validation gates for the synthetic dataset."""

    feature_list = list(
        ALL_MODEL_FEATURES if model_features is None else model_features
    )

    assert_required_columns_present(dataset)
    assert_row_count(dataset, expected_row_count=expected_row_count)
    assert_no_missing_values(dataset)

    default_rate = calculate_default_rate(dataset)
    assert_default_rate_bounds(default_rate)
    assert_valid_cohort_months(dataset)
    test_rows = assert_minimum_test_rows(dataset, minimum_rows=minimum_test_rows)
    assert_protected_attributes_not_in_model_features(feature_list)
    assert_temporal_metadata_not_in_model_features(feature_list)
    assert_target_not_in_model_features(feature_list)

    return {
        "row_count": int(len(dataset)),
        "default_rate": default_rate,
        "test_rows": test_rows,
        "month_count": int(dataset["cohort_month"].nunique()),
    }


def assert_required_columns_present(dataset: pd.DataFrame) -> None:
    missing_columns = [
        column for column in REQUIRED_DATASET_COLUMNS if column not in dataset.columns
    ]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")


def assert_row_count(
    dataset: pd.DataFrame, expected_row_count: int = EXPECTED_ROW_COUNT
) -> None:
    if len(dataset) != expected_row_count:
        raise ValueError(
            f"Dataset row count must be {expected_row_count:,}; found {len(dataset):,}."
        )


def assert_no_missing_values(dataset: pd.DataFrame) -> None:
    if dataset.isnull().to_numpy().any():
        raise ValueError("Synthetic dataset contains missing values.")


def calculate_default_rate(dataset: pd.DataFrame) -> float:
    return float((dataset[TARGET] == 0).mean())


def assert_default_rate_bounds(
    default_rate: float,
    lower_bound: float = DEFAULT_RATE_BOUNDS[0],
    upper_bound: float = DEFAULT_RATE_BOUNDS[1],
) -> None:
    if not lower_bound <= default_rate <= upper_bound:
        raise ValueError(
            f"Default rate must be between {lower_bound:.0%} and {upper_bound:.0%}; "
            f"found {default_rate:.2%}."
        )


def assert_valid_cohort_months(dataset: pd.DataFrame) -> None:
    observed_months = set(dataset["cohort_month"].tolist())
    invalid_months = sorted(observed_months - VALID_COHORT_MONTHS)
    if invalid_months:
        raise ValueError(
            f"Cohort month values must be between 1 and 12; found {invalid_months}."
        )


def assert_minimum_test_rows(
    dataset: pd.DataFrame,
    minimum_rows: int = MINIMUM_TEST_ROWS,
) -> int:
    test_rows = int(dataset["cohort_month"].isin([11, 12]).sum())
    if test_rows < minimum_rows:
        raise ValueError(
            f"Months 11-12 must contain at least {minimum_rows:,} rows; found {test_rows:,}."
        )
    return test_rows


def assert_protected_attributes_not_in_model_features(
    model_features: Sequence[str],
) -> None:
    overlap = sorted(set(model_features) & set(PROTECTED_FEATURES))
    if overlap:
        raise ValueError(
            f"Protected attributes cannot appear in model features: {overlap}"
        )


def assert_temporal_metadata_not_in_model_features(
    model_features: Sequence[str],
) -> None:
    overlap = sorted(set(model_features) & set(TEMPORAL_METADATA))
    if overlap:
        raise ValueError(
            f"Temporal metadata cannot appear in model features: {overlap}"
        )


def assert_target_not_in_model_features(
    model_features: Sequence[str], target: str = TARGET
) -> None:
    if target in model_features:
        raise ValueError(f"Target column '{target}' cannot appear in model features.")


__all__ = [
    "DEFAULT_RATE_BOUNDS",
    "EXPECTED_ROW_COUNT",
    "MINIMUM_TEST_ROWS",
    "REQUIRED_DATASET_COLUMNS",
    "VALID_COHORT_MONTHS",
    "assert_default_rate_bounds",
    "assert_minimum_test_rows",
    "assert_no_missing_values",
    "assert_protected_attributes_not_in_model_features",
    "assert_required_columns_present",
    "assert_row_count",
    "assert_target_not_in_model_features",
    "assert_temporal_metadata_not_in_model_features",
    "assert_valid_cohort_months",
    "calculate_default_rate",
    "validate_synthetic_dataset",
]
