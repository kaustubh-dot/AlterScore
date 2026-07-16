"""Canonical synthetic-demo model feature registry.

Only answer-derived assessment features may enter the model.  Browser and
device telemetry is deliberately kept out of this registry so it cannot leak
into training, derived features, inference, explanations, or counterfactuals.
"""

NUMERIC_FEATURES: list[str] = [
    "numeracy_score",
    "CRT_score",
    "financial_literacy_score",
    "future_orientation",
    "loss_aversion_score",
    "locus_of_control",
    "conscientiousness_score",
    "social_capital_score",
    "honesty_score",
    "resilience_score",
    "reciprocity_norm",
]

CATEGORICAL_FEATURES: list[str] = []

ALL_MODEL_FEATURES: list[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES

PROTECTED_FEATURES: list[str] = [
    "gender",
    "age_group",
    "region",
    "education_level",
]

TEMPORAL_METADATA: list[str] = [
    "cohort_month",
    "application_date",
]

TARGET = "repayment_label"

ACTIONABLE_FEATURES: list[str] = [
    "numeracy_score",
    "financial_literacy_score",
    "future_orientation",
    "conscientiousness_score",
    "locus_of_control",
    "resilience_score",
]

RAW_BROWSER_TELEMETRY_FIELDS: list[str] = [
    "avg_response_time_ms",
    "answer_change_rate",
    "session_duration_sec",
    "dropout_count",
    "scroll_hesitation_score",
    "risk_response_speed_ratio",
    "typing_speed_wpm",
    "device_type",
    "time_of_day",
    "first_click_ms",
    "change_count",
]

IMMUTABLE_FEATURES: list[str] = [
    *PROTECTED_FEATURES,
    *TEMPORAL_METADATA,
]

__all__ = [
    "ACTIONABLE_FEATURES",
    "ALL_MODEL_FEATURES",
    "CATEGORICAL_FEATURES",
    "IMMUTABLE_FEATURES",
    "NUMERIC_FEATURES",
    "PROTECTED_FEATURES",
    "RAW_BROWSER_TELEMETRY_FIELDS",
    "TARGET",
    "TEMPORAL_METADATA",
]
