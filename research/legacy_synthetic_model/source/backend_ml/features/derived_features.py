"""Compatibility helpers for retired derived features.

The production scorer now uses only direct answer-derived assessment features.
Legacy derived features are intentionally excluded from the registry and this
module no longer adds a second, opaque feature layer during training or
inference.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

import pandas as pd

from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES

DERIVED_FEATURES: Final[list[str]] = []
DERIVED_FEATURE_REQUIREMENTS: Final[list[str]] = []


def compute_derived_features(features: Mapping[str, Any]) -> dict[str, float]:
    """Return no derived values under the answer-only feature policy."""

    del features
    return {}


def add_derived_features(feature_frame: pd.DataFrame) -> pd.DataFrame:
    """Add derived features to a DataFrame when the base inputs are present."""

    return feature_frame.copy()


def build_model_feature_row(
    *,
    psychometric_features: Mapping[str, Any],
    behavioral_features: Mapping[str, Any],
    nlp_features: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge layer outputs into one ordered model feature row."""

    merged_features: dict[str, Any] = {
        **psychometric_features,
        **behavioral_features,
        **{
            key: value for key, value in nlp_features.items() if key != "_embedding_raw"
        },
    }
    missing_features = [
        feature_name
        for feature_name in ALL_MODEL_FEATURES
        if feature_name not in merged_features
    ]
    if missing_features:
        raise ValueError(
            "Model feature assembly is missing answer-derived features: "
            f"{missing_features}"
        )
    return {
        feature_name: merged_features[feature_name]
        for feature_name in ALL_MODEL_FEATURES
    }


__all__ = [
    "DERIVED_FEATURES",
    "DERIVED_FEATURE_REQUIREMENTS",
    "add_derived_features",
    "build_model_feature_row",
    "compute_derived_features",
]
