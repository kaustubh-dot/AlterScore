"""Monotonic constrained-tree policy for governed production candidates.

This module defines the training-time feature policy for the production-track
tree baselines. The policy favors atomic psychometric, behavioral, and
interpretable NLP features while suppressing brittle high-order composites and
operational metadata.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

import pandas as pd

from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES

NEUTRAL_DEVICE_TYPE: Final[str] = "mobile"
NEUTRAL_TIME_OF_DAY: Final[str] = "afternoon"

MONOTONIC_TREE_MASKED_FEATURES: Final[tuple[str, ...]] = (
    "psychological_credit_index",
    "cognitive_consistency_index",
    "repayment_intention_score",
    "impulsivity_index",
    "cognitive_load_index",
    "engagement_score",
    "behavioral_trust_score",
    "text_semantic_dim1",
    "text_semantic_dim2",
)

MONOTONIC_TREE_DIRECTION_MAP: Final[dict[str, int]] = {
    "numeracy_score": 1,
    "CRT_score": 1,
    "financial_literacy_score": 1,
    "future_orientation": 1,
    "delay_discounting_rate": -1,
    "risk_attitude": 0,
    "risk_consistency_flag": -1,
    "loss_aversion_score": 0,
    "locus_of_control": 1,
    "conscientiousness_score": 1,
    "social_capital_score": 1,
    "honesty_score": 1,
    "resilience_score": 1,
    "reciprocity_norm": 1,
    "avg_response_time_ms": 0,
    "answer_change_rate": -1,
    "session_duration_sec": 0,
    "dropout_count": -1,
    "scroll_hesitation_score": -1,
    "risk_response_speed_ratio": 0,
    "typing_speed_wpm": 0,
    "text_sentiment_compound": 1,
    "text_agency_score": 1,
    "text_problem_solving_flag": 1,
    "text_semantic_dim1": 0,
    "text_semantic_dim2": 0,
    "psychological_credit_index": 0,
    "cognitive_consistency_index": 0,
    "repayment_intention_score": 0,
    "impulsivity_index": 0,
    "cognitive_load_index": 0,
    "engagement_score": 0,
    "behavioral_trust_score": 0,
    "device_type": 0,
    "time_of_day": 0,
}

MONOTONIC_TREE_ACTIVE_FEATURES: Final[tuple[str, ...]] = tuple(
    feature_name
    for feature_name in ALL_MODEL_FEATURES
    if feature_name not in MONOTONIC_TREE_MASKED_FEATURES
    and feature_name not in {"device_type", "time_of_day"}
)


def neutralize_operational_metadata_for_training(
    feature_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Set operational metadata to neutral values for constrained-tree training."""

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
    """Neutralize brittle derived and opaque features using train-split statistics."""

    updated = feature_frame.copy()
    replacements: dict[str, Any] = {}
    train_frame = feature_frame.loc[train_mask]
    for feature_name in masked_features:
        train_series = train_frame[feature_name]
        if pd.api.types.is_numeric_dtype(train_series):
            replacement = float(train_series.median())
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
    """Return one monotonic constraint integer per transformed model feature."""

    return tuple(
        int(direction_map.get(feature_name, 0)) for feature_name in feature_names
    )


__all__ = [
    "MONOTONIC_TREE_ACTIVE_FEATURES",
    "MONOTONIC_TREE_DIRECTION_MAP",
    "MONOTONIC_TREE_MASKED_FEATURES",
    "NEUTRAL_DEVICE_TYPE",
    "NEUTRAL_TIME_OF_DAY",
    "apply_monotonic_tree_feature_masking",
    "build_monotonic_constraint_vector",
    "neutralize_operational_metadata_for_training",
]
