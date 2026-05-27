"""Derived feature engineering for AlterScore."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

import pandas as pd

from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES

DERIVED_FEATURES: Final[list[str]] = [
    "psychological_credit_index",
    "cognitive_consistency_index",
    "repayment_intention_score",
    "impulsivity_index",
    "cognitive_load_index",
    "engagement_score",
    "behavioral_trust_score",
]

DERIVED_FEATURE_REQUIREMENTS: Final[list[str]] = [
    "numeracy_score",
    "CRT_score",
    "financial_literacy_score",
    "future_orientation",
    "risk_attitude",
    "risk_consistency_flag",
    "loss_aversion_score",
    "locus_of_control",
    "conscientiousness_score",
    "social_capital_score",
    "honesty_score",
    "avg_response_time_ms",
    "answer_change_rate",
    "dropout_count",
    "scroll_hesitation_score",
    "risk_response_speed_ratio",
]


def compute_derived_features(features: Mapping[str, Any]) -> dict[str, float]:
    """Compute the 7 derived AlterScore features for one feature row."""

    values = {key: float(features[key]) for key in DERIVED_FEATURE_REQUIREMENTS}

    psychological_credit_index = _clip(
        0.22 * values["numeracy_score"]
        + 0.18 * values["honesty_score"]
        + 0.16 * values["future_orientation"]
        + 0.12 * values["locus_of_control"]
        + 0.10 * values["social_capital_score"]
        + 0.08 * values["conscientiousness_score"]
        + 0.06 * values["CRT_score"]
        + 0.05 * values["financial_literacy_score"]
        + 0.03 * (1.0 - values["loss_aversion_score"]),
        lower=0.0,
        upper=1.0,
    )
    cognitive_consistency_index = _clip(
        values["CRT_score"]
        * (1.0 - values["risk_consistency_flag"])
        * (1.0 - values["answer_change_rate"]),
        lower=0.0,
        upper=1.0,
    )
    repayment_intention_score = _clip(
        values["locus_of_control"]
        * values["social_capital_score"]
        * values["honesty_score"],
        lower=0.0,
        upper=1.0,
    )
    impulsivity_index = _clip(
        (values["risk_attitude"] * values["risk_response_speed_ratio"])
        / (values["CRT_score"] + 0.1),
        lower=0.0,
        upper=5.0,
    )
    cognitive_load_index = _clip(
        (values["avg_response_time_ms"] / 4500.0)
        * (1.0 + values["answer_change_rate"])
        * (1.0 + values["dropout_count"] * 0.2),
        lower=0.0,
    )
    engagement_score = _clip(
        (1.0 - values["scroll_hesitation_score"])
        * (1.0 - values["answer_change_rate"])
        * _clip(1.0 - values["dropout_count"] / 4.0, lower=0.0, upper=1.0)
        * _clip(1.0 - values["risk_response_speed_ratio"] * 0.3, lower=0.0, upper=1.0),
        lower=0.0,
        upper=1.0,
    )
    behavioral_trust_score = _clip(
        engagement_score * values["honesty_score"] * (1.0 - impulsivity_index),
        lower=-1.0,
        upper=1.0,
    )

    return {
        "psychological_credit_index": psychological_credit_index,
        "cognitive_consistency_index": cognitive_consistency_index,
        "repayment_intention_score": repayment_intention_score,
        "impulsivity_index": impulsivity_index,
        "cognitive_load_index": cognitive_load_index,
        "engagement_score": engagement_score,
        "behavioral_trust_score": behavioral_trust_score,
    }


def add_derived_features(feature_frame: pd.DataFrame) -> pd.DataFrame:
    """Add derived features to a DataFrame when the base inputs are present."""

    _assert_required_columns(feature_frame)
    derived_rows = feature_frame.apply(
        lambda row: pd.Series(compute_derived_features(row.to_dict())),
        axis=1,
    )
    updated_frame = feature_frame.copy()
    for column in DERIVED_FEATURES:
        updated_frame.loc[:, column] = derived_rows[column].to_numpy(dtype=float)
    return updated_frame


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
    merged_features.update(compute_derived_features(merged_features))
    return {
        feature_name: merged_features[feature_name]
        for feature_name in ALL_MODEL_FEATURES
    }


def _assert_required_columns(feature_frame: pd.DataFrame) -> None:
    missing_columns = [
        column_name
        for column_name in DERIVED_FEATURE_REQUIREMENTS
        if column_name not in feature_frame.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Feature frame is missing required columns for derived features: {missing_columns}"
        )


def _clip(value: float, *, lower: float, upper: float | None = None) -> float:
    clipped = max(value, lower)
    if upper is not None:
        clipped = min(clipped, upper)
    return float(clipped)


__all__ = [
    "DERIVED_FEATURES",
    "DERIVED_FEATURE_REQUIREMENTS",
    "add_derived_features",
    "build_model_feature_row",
    "compute_derived_features",
]
