"""Canonical AlterScore model feature registry.

This module is the single backend source of truth for model input columns and
for fields that must stay outside training and inference inputs.
"""

NUMERIC_FEATURES: list[str] = [
    "numeracy_score",
    "CRT_score",
    "financial_literacy_score",
    "future_orientation",
    "delay_discounting_rate",
    "risk_attitude",
    "risk_consistency_flag",
    "loss_aversion_score",
    "locus_of_control",
    "conscientiousness_score",
    "social_capital_score",
    "honesty_score",
    "resilience_score",
    "reciprocity_norm",
    "avg_response_time_ms",
    "answer_change_rate",
    "session_duration_sec",
    "dropout_count",
    "scroll_hesitation_score",
    "risk_response_speed_ratio",
    "typing_speed_wpm",
    "text_sentiment_compound",
    "text_agency_score",
    "text_problem_solving_flag",
    "text_semantic_dim1",
    "text_semantic_dim2",
    "psychological_credit_index",
    "cognitive_consistency_index",
    "repayment_intention_score",
    "impulsivity_index",
    "cognitive_load_index",
    "engagement_score",
    "behavioral_trust_score",
]

CATEGORICAL_FEATURES: list[str] = [
    "device_type",
    "time_of_day",
]

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
    "social_capital_score",
    "engagement_score",
    "avg_response_time_ms",
    "answer_change_rate",
    "text_agency_score",
]

IMMUTABLE_FEATURES: list[str] = [
    *PROTECTED_FEATURES,
    *CATEGORICAL_FEATURES,
    *TEMPORAL_METADATA,
]

__all__ = [
    "ACTIONABLE_FEATURES",
    "ALL_MODEL_FEATURES",
    "CATEGORICAL_FEATURES",
    "IMMUTABLE_FEATURES",
    "NUMERIC_FEATURES",
    "PROTECTED_FEATURES",
    "TARGET",
    "TEMPORAL_METADATA",
]
