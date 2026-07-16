import pytest

from backend.ml.features.derived_features import (
    DERIVED_FEATURES,
    build_model_feature_row,
    compute_derived_features,
)
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES


def _answer_features() -> dict[str, float]:
    return {
        "numeracy_score": 0.8,
        "CRT_score": 0.7,
        "financial_literacy_score": 0.6,
        "future_orientation": 0.75,
        "loss_aversion_score": 0.2,
        "locus_of_control": 0.7,
        "conscientiousness_score": 0.65,
        "social_capital_score": 0.75,
        "honesty_score": 0.8,
        "resilience_score": 0.7,
        "reciprocity_norm": 0.6,
    }


def test_derived_feature_layer_is_retired_from_the_model_policy() -> None:
    assert DERIVED_FEATURES == []
    assert compute_derived_features(_answer_features()) == {}


def test_model_feature_row_selects_only_declared_answer_features() -> None:
    answer_features = _answer_features()
    feature_row = build_model_feature_row(
        psychometric_features=answer_features,
        behavioral_features={
            "avg_response_time_ms": 100.0,
            "device_type": "tablet",
            "scroll_hesitation_score": 1.0,
        },
        nlp_features={"text_agency_score": 1.0, "_embedding_raw": [1.0]},
    )

    assert list(feature_row) == ALL_MODEL_FEATURES
    assert feature_row == answer_features
    assert "avg_response_time_ms" not in feature_row
    assert "text_agency_score" not in feature_row


def test_model_feature_row_rejects_missing_declared_answer_feature() -> None:
    answer_features = _answer_features()
    del answer_features["honesty_score"]

    with pytest.raises(ValueError, match="honesty_score"):
        build_model_feature_row(
            psychometric_features=answer_features,
            behavioral_features={},
            nlp_features={},
        )
