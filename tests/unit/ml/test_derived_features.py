from backend.ml.features.derived_features import (
    DERIVED_FEATURES,
    build_model_feature_row,
    compute_derived_features,
)


def test_compute_derived_features_returns_all_expected_keys() -> None:
    derived_features = compute_derived_features(_base_feature_inputs())

    assert set(derived_features) == set(DERIVED_FEATURES)


def test_derived_features_are_clipped_to_expected_ranges() -> None:
    derived_features = compute_derived_features(_stress_feature_inputs())

    assert 0.0 <= derived_features["psychological_credit_index"] <= 1.0
    assert 0.0 <= derived_features["cognitive_consistency_index"] <= 1.0
    assert 0.0 <= derived_features["repayment_intention_score"] <= 1.0
    assert 0.0 <= derived_features["impulsivity_index"] <= 5.0
    assert derived_features["cognitive_load_index"] >= 0.0
    assert 0.0 <= derived_features["engagement_score"] <= 1.0
    assert -1.0 <= derived_features["behavioral_trust_score"] <= 1.0


def test_higher_impulsivity_inputs_increase_impulsivity_index() -> None:
    low_impulsivity = compute_derived_features(
        _base_feature_inputs()
        | {
            "risk_attitude": 0.2,
            "risk_response_speed_ratio": 0.6,
            "CRT_score": 0.9,
        }
    )
    high_impulsivity = compute_derived_features(
        _base_feature_inputs()
        | {
            "risk_attitude": 0.9,
            "risk_response_speed_ratio": 2.0,
            "CRT_score": 0.2,
        }
    )

    assert high_impulsivity["impulsivity_index"] > low_impulsivity["impulsivity_index"]


def test_higher_engagement_inputs_increase_engagement_score() -> None:
    low_engagement = compute_derived_features(
        _base_feature_inputs()
        | {
            "scroll_hesitation_score": 0.9,
            "answer_change_rate": 0.4,
            "dropout_count": 3.0,
            "risk_response_speed_ratio": 2.0,
        }
    )
    high_engagement = compute_derived_features(
        _base_feature_inputs()
        | {
            "scroll_hesitation_score": 0.1,
            "answer_change_rate": 0.05,
            "dropout_count": 0.0,
            "risk_response_speed_ratio": 0.5,
        }
    )

    assert high_engagement["engagement_score"] > low_engagement["engagement_score"]


def test_build_model_feature_row_merges_layers_and_adds_derived_features() -> None:
    feature_row = build_model_feature_row(
        psychometric_features={
            "numeracy_score": 1.0,
            "CRT_score": 1.0,
            "financial_literacy_score": 1.0,
            "future_orientation": 0.9,
            "delay_discounting_rate": 1.0,
            "risk_attitude": 0.5,
            "risk_consistency_flag": 0.0,
            "loss_aversion_score": 0.0,
            "locus_of_control": 0.9,
            "conscientiousness_score": 0.75,
            "social_capital_score": 0.89,
            "honesty_score": 1.0,
            "resilience_score": 0.83,
            "reciprocity_norm": 0.88,
        },
        behavioral_features={
            "avg_response_time_ms": 4800.0,
            "answer_change_rate": 0.08,
            "session_duration_sec": 410.0,
            "dropout_count": 0.0,
            "scroll_hesitation_score": 0.62,
            "risk_response_speed_ratio": 0.85,
            "typing_speed_wpm": 34.0,
            "device_type": "mobile",
            "time_of_day": "afternoon",
        },
        nlp_features={
            "text_sentiment_compound": 0.4,
            "text_agency_score": 0.6,
            "text_problem_solving_flag": 1.0,
            "text_semantic_dim1": 0.12,
            "text_semantic_dim2": -0.08,
            "_embedding_raw": [0.0] * 384,
        },
    )

    assert "psychological_credit_index" in feature_row
    assert "engagement_score" in feature_row
    assert "behavioral_trust_score" in feature_row


def _base_feature_inputs() -> dict[str, float]:
    return {
        "numeracy_score": 0.8,
        "CRT_score": 0.7,
        "financial_literacy_score": 0.6,
        "future_orientation": 0.75,
        "risk_attitude": 0.5,
        "risk_consistency_flag": 0.0,
        "loss_aversion_score": 0.2,
        "locus_of_control": 0.7,
        "conscientiousness_score": 0.65,
        "social_capital_score": 0.75,
        "honesty_score": 0.8,
        "avg_response_time_ms": 5000.0,
        "answer_change_rate": 0.1,
        "dropout_count": 1.0,
        "scroll_hesitation_score": 0.6,
        "risk_response_speed_ratio": 0.9,
    }


def _stress_feature_inputs() -> dict[str, float]:
    return {
        "numeracy_score": 1.0,
        "CRT_score": 0.0,
        "financial_literacy_score": 1.0,
        "future_orientation": 1.0,
        "risk_attitude": 1.0,
        "risk_consistency_flag": 1.0,
        "loss_aversion_score": 1.0,
        "locus_of_control": 1.0,
        "conscientiousness_score": 1.0,
        "social_capital_score": 1.0,
        "honesty_score": 1.0,
        "avg_response_time_ms": 10000.0,
        "answer_change_rate": 1.0,
        "dropout_count": 6.0,
        "scroll_hesitation_score": 1.0,
        "risk_response_speed_ratio": 5.0,
    }
