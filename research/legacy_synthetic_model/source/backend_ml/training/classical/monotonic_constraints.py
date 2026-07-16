"""Feature policy for the answer-only monotonic demo model.

The scoring registry intentionally excludes browser/device telemetry, opaque
text embeddings, and legacy composites. This module keeps the training helper
API stable while ensuring only answer-derived model columns receive constraints.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

import pandas as pd

from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES

NEUTRAL_DEVICE_TYPE: Final[str] = "mobile"
NEUTRAL_TIME_OF_DAY: Final[str] = "afternoon"
MONOTONIC_TREE_MASKED_FEATURES: Final[tuple[str, ...]] = ()

MONOTONIC_TREE_DIRECTION_MAP: Final[dict[str, int]] = {
    "numeracy_score": 1,
    "CRT_score": 1,
    "financial_literacy_score": 1,
    "future_orientation": 1,
    "loss_aversion_score": 0,
    "locus_of_control": 1,
    "conscientiousness_score": 1,
    "social_capital_score": 1,
    "honesty_score": 1,
    "resilience_score": 1,
    "reciprocity_norm": 1,
    # Compatibility defaults for legacy test callers; neither is a model input.
    "scroll_hesitation_score": -1,
    "device_type": 0,
    "time_of_day": 0,
}

MONOTONIC_TREE_ACTIVE_FEATURES: Final[tuple[str, ...]] = tuple(ALL_MODEL_FEATURES)
DEFAULT_FEATURE_WEIGHT: Final[float] = 1.0
MONOTONIC_TREE_FEATURE_WEIGHT_MAP: Final[dict[str, float]] = {
    "numeracy_score": 2.0,
    "CRT_score": 2.0,
    "financial_literacy_score": 2.0,
    "future_orientation": 1.25,
    "conscientiousness_score": 1.25,
    "honesty_score": 1.25,
    "locus_of_control": 1.25,
    "resilience_score": 1.25,
}


def neutralize_operational_metadata_for_training(feature_frame: pd.DataFrame) -> pd.DataFrame:
    """Keep legacy callers safe if unregistered metadata columns are present."""

    updated = feature_frame.copy()
    if "device_type" in updated.columns:
        updated.loc[:, "device_type"] = NEUTRAL_DEVICE_TYPE
    if "time_of_day" in updated.columns:
        updated.loc[:, "time_of_day"] = NEUTRAL_TIME_OF_DAY
    return updated


def apply_monotonic_tree_feature_masking(
    feature_frame: pd.DataFrame,
    *,
    train_mask: pd.Series,
    masked_features: tuple[str, ...] = MONOTONIC_TREE_MASKED_FEATURES,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Neutralize explicitly requested legacy columns using train statistics."""

    updated = feature_frame.copy()
    replacements: dict[str, Any] = {}
    train_frame = feature_frame.loc[train_mask]
    for feature_name in masked_features:
        if feature_name not in feature_frame.columns:
            continue
        train_series = train_frame[feature_name]
        if pd.api.types.is_numeric_dtype(train_series):
            replacement: Any = float(train_series.median())
        else:
            mode = train_series.mode(dropna=True)
            replacement = str(mode.iloc[0]) if not mode.empty else ""
        updated.loc[:, feature_name] = replacement
        replacements[feature_name] = replacement
    return updated, replacements


def build_monotonic_constraint_vector(
    feature_names: list[str] | tuple[str, ...] = tuple(ALL_MODEL_FEATURES),
    *,
    direction_map: Mapping[str, int] = MONOTONIC_TREE_DIRECTION_MAP,
) -> tuple[int, ...]:
    return tuple(int(direction_map.get(_canonical_feature_name(name), 0)) for name in feature_names)


def build_feature_weight_vector(
    feature_names: list[str] | tuple[str, ...] = tuple(ALL_MODEL_FEATURES),
    *,
    weight_map: Mapping[str, float] = MONOTONIC_TREE_FEATURE_WEIGHT_MAP,
    default_weight: float = DEFAULT_FEATURE_WEIGHT,
) -> tuple[float, ...]:
    return tuple(float(weight_map.get(_canonical_feature_name(name), default_weight)) for name in feature_names)


def _canonical_feature_name(feature_name: str) -> str:
    for prefix in ("num__", "cat__"):
        if feature_name.startswith(prefix):
            return feature_name[len(prefix):]
    return feature_name


__all__ = [
    "DEFAULT_FEATURE_WEIGHT",
    "MONOTONIC_TREE_ACTIVE_FEATURES",
    "MONOTONIC_TREE_DIRECTION_MAP",
    "MONOTONIC_TREE_FEATURE_WEIGHT_MAP",
    "MONOTONIC_TREE_MASKED_FEATURES",
    "NEUTRAL_DEVICE_TYPE",
    "NEUTRAL_TIME_OF_DAY",
    "apply_monotonic_tree_feature_masking",
    "build_feature_weight_vector",
    "build_monotonic_constraint_vector",
    "neutralize_operational_metadata_for_training",
]
