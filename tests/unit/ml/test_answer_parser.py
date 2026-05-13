from backend.ml.features.answer_parser import PSYCHOMETRIC_FEATURES, parse_answers


def test_known_correct_numeracy_answers_produce_high_numeracy_score() -> None:
    features = parse_answers(_base_answers())

    assert features["numeracy_score"] == 1.0


def test_crt_trap_answers_produce_low_crt_score() -> None:
    trap_answers = _base_answers() | {
        "CRT_q1": 10,
        "CRT_q2": 100,
        "CRT_q3": 24,
    }

    features = parse_answers(trap_answers)

    assert features["CRT_score"] == 0.0


def test_future_orientation_inconsistency_lowers_honesty_score() -> None:
    consistent_features = parse_answers(_base_answers())
    inconsistent_features = parse_answers(
        _base_answers() | {
            "future_orient_repeat": 0,
        }
    )

    assert inconsistent_features["honesty_score"] < consistent_features["honesty_score"]


def test_social_desirability_trap_agreement_lowers_honesty_score() -> None:
    baseline_features = parse_answers(_base_answers())
    suspicious_features = parse_answers(
        _base_answers() | {
            "honesty_trap_q1": 5,
            "honesty_trap_q2": 5,
        }
    )

    assert suspicious_features["honesty_score"] < baseline_features["honesty_score"]


def test_parse_answers_returns_all_psychometric_feature_keys() -> None:
    features = parse_answers(_base_answers())

    assert set(features) == set(PSYCHOMETRIC_FEATURES)


def _base_answers() -> dict[str, int | float | str]:
    return {
        "numeracy_q1": 6600,
        "numeracy_q2": 1120,
        "numeracy_q3": 14400,
        "financial_literacy_q1": 1,
        "financial_literacy_q2": 1,
        "conscientiousness_q1": 4,
        "CRT_q1": 5,
        "CRT_q2": 5,
        "CRT_q3": 47,
        "future_orient_q1": 1,
        "future_orient_q2": 1,
        "future_orient_q3": 4,
        "risk_q1": 1,
        "risk_q2": 1,
        "locus_q1": 0,
        "locus_q2": 0,
        "locus_q3": 4,
        "social_capital_q1": 2,
        "social_capital_q2": 0,
        "social_capital_q3": 0,
        "resilience_q1": 4,
        "resilience_q2": 4,
        "resilience_q3": 0,
        "loss_aversion_q1": 0,
        "honesty_trap_q1": 2,
        "honesty_trap_q2": 2,
        "future_orient_repeat": 1,
        "locus_repeat": 0,
        "reciprocity_q1": 4,
        "reciprocity_q2": 0,
        "q27_resilience_text": "I reduced expenses and found extra work.",
    }
