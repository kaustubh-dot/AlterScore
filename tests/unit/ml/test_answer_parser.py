"""Unit tests for the v2 answer parser.

Tests the base psychometric feature extraction from objective questions.
Scenario-derived enrichments are tested separately in test_scenario_analyzer.py.
"""

from backend.ml.features.answer_parser import PSYCHOMETRIC_FEATURES, parse_answers


def test_known_correct_numeracy_answers_produce_high_numeracy_score() -> None:
    features = parse_answers(_base_answers())

    assert features["numeracy_score"] == 1.0


def test_crt_trap_answers_produce_low_crt_score() -> None:
    """The CRT instinctive wrong answers (10 and 100) should produce a zero CRT score."""
    trap_answers = _base_answers() | {
        "CRT_q1": 10,   # instinctive wrong answer (correct is 5)
        "CRT_q2": 24,   # instinctive wrong answer (correct is 47)
    }

    features = parse_answers(trap_answers)

    assert features["CRT_score"] == 0.0


def test_social_desirability_trap_agreement_lowers_honesty_score() -> None:
    """Agreeing strongly with implausible universals should reduce honesty score."""
    baseline_features = parse_answers(_base_answers())
    suspicious_features = parse_answers(
        _base_answers() | {
            "honesty_trap_q1": 5,
            "honesty_trap_q2": 5,
        }
    )

    assert suspicious_features["honesty_score"] < baseline_features["honesty_score"]


def test_honesty_score_highest_when_traps_answered_neutrally() -> None:
    """Neutral (3) honesty trap answers should produce a reasonably high honesty score."""
    neutral_features = parse_answers(_base_answers())
    # Default _base_answers uses honesty_trap_q1=2, honesty_trap_q2=2 (Disagree)
    # which is honest — no penalty
    assert neutral_features["honesty_score"] > 0.7


def test_parse_answers_returns_all_psychometric_feature_keys() -> None:
    features = parse_answers(_base_answers())

    assert set(features) == set(PSYCHOMETRIC_FEATURES)


def test_all_psychometric_features_are_clipped_to_unit_interval() -> None:
    """All feature values must be in [0.0, 1.0]."""
    features = parse_answers(_base_answers())

    for key, value in features.items():
        assert 0.0 <= value <= 1.0, f"Feature '{key}' out of range: {value}"


def test_features_without_v2_direct_questions_default_to_neutral_prior() -> None:
    """Features without a direct v2 question source should default to 0.5 neutral prior.

    These are enriched downstream by scenario_analyzer, not by this parser.
    """
    features = parse_answers(_base_answers())

    neutral_prior_features = [
        "future_orientation",
        "delay_discounting_rate",
        "risk_attitude",
        "loss_aversion_score",
        "locus_of_control",
        "conscientiousness_score",
        "social_capital_score",
        "resilience_score",
        "reciprocity_norm",
    ]
    for feature_name in neutral_prior_features:
        assert features[feature_name] == 0.5, (
            f"Expected 0.5 neutral prior for '{feature_name}', got {features[feature_name]}"
        )


def test_risk_consistency_flag_defaults_to_zero_in_v2() -> None:
    """v2 has no direct risk pair questions — flag should be 0.0 (no conflict)."""
    features = parse_answers(_base_answers())
    assert features["risk_consistency_flag"] == 0.0


def _base_answers() -> dict[str, int | float | str]:
    """Minimal v2 answer dict — only objective question fields needed by parse_answers."""
    return {
        # Section A — Financial Reasoning
        "numeracy_q1": 6600,
        "numeracy_q2": 1120,
        "financial_literacy_q1": 1,
        "CRT_q1": 5,
        "CRT_q2": 47,
        # Honesty traps (embedded in Section B)
        "honesty_trap_q1": 2,   # Disagree — honest response
        "honesty_trap_q2": 2,   # Disagree — honest response
        # Open text
        "q27_resilience_text": "I reduced expenses and found extra work.",
    }
