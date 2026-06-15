from backend.ml.nlp.extractor import _validate_text_quality
from backend.ml.inference.score_mapper import probability_to_score
from backend.app.services.scoring import (
    SEVERE_GOVERNANCE_MULTIPLIER_MIN,
    _calculate_governance_multiplier,
)


def test_text_quality_validation() -> None:
    # 1. Natural thoughtful text
    thoughtful_text = "I draft detailed plans, budget my savings strictly, and recover operations fast."
    tokens = thoughtful_text.lower().replace(".", "").replace(",", "").split()
    assert _validate_text_quality(thoughtful_text, tokens) is True

    # 2. Repeated gibberish spam text
    gibberish_text = "repay repay repay repay repay repay repay"
    gibberish_tokens = gibberish_text.split()
    assert _validate_text_quality(gibberish_text, gibberish_tokens) is False

    # 3. Keyboard spam character repetitions
    spam_text = "qwertyuiopasdfghjkl"
    spam_tokens = [spam_text]
    assert _validate_text_quality(spam_text, spam_tokens) is False

    # 4. Legitimate short vowel-heavy sentence (regression check for false-positive bug)
    regression_text = "I had a bad day"
    regression_tokens = ["i", "had", "a", "bad", "day"]
    assert _validate_text_quality(regression_text, regression_tokens) is True


def test_score_saturation_fix() -> None:
    # Under old logic, 0.968 mapped to 850. Let's verify our new wider logistic mapping:
    high_prob_score = probability_to_score(0.968)
    assert high_prob_score < 850  # should not saturate early

    super_elite_score = probability_to_score(0.995)
    assert super_elite_score == 850  # perfect score remains reachable but difficult


def test_post_model_governance_multiplier() -> None:
    # 1. High Trust Profile
    clean_row = {
        "impulsivity_index": 0.20,
        "honesty_score": 0.95,
        "dropout_count": 0,
        "answer_change_rate": 0.05,
    }
    mult_clean, reasons_clean = _calculate_governance_multiplier(clean_row)
    assert mult_clean == 1.0
    assert len(reasons_clean) == 0

    # 2. Highly Gaming/Anomalous Profile
    gaming_row = {
        "impulsivity_index": 3.20,  # highly impulsive
        "honesty_score": 0.40,  # fails honesty check
        "scenario_consistency_score": 0.0,  # independent contradiction evidence
        "dropout_count": 5,  # switched tabs repeatedly
        "answer_change_rate": 0.45,
    }
    mult_game, reasons_game = _calculate_governance_multiplier(gaming_row)
    assert mult_game < 0.80  # heavily penalized
    assert len(reasons_game) > 2


def test_governance_does_not_penalize_low_cognition_without_gaming_evidence() -> None:
    low_cognition_row = {
        "impulsivity_index": 0.20,
        "honesty_score": 0.95,
        "dropout_count": 0,
        "answer_change_rate": 0.05,
        "numeracy_score": 0.0,
        "CRT_score": 0.0,
    }

    multiplier, reasons = _calculate_governance_multiplier(low_cognition_row)

    assert multiplier == 1.0
    assert not any("cognitive" in reason.lower() for reason in reasons)


def test_governance_does_not_apply_standalone_average_speed_penalty() -> None:
    fast_but_clean_row = {
        "impulsivity_index": 0.20,
        "honesty_score": 0.95,
        "dropout_count": 0,
        "answer_change_rate": 0.05,
        "avg_response_time_ms": 500.0,
    }

    multiplier, reasons = _calculate_governance_multiplier(fast_but_clean_row)

    assert multiplier == 1.0
    assert not any("fast response" in reason.lower() for reason in reasons)


def test_governance_does_not_penalize_single_honesty_trap_without_other_evidence() -> (
    None
):
    honesty_only_row = {
        "impulsivity_index": 0.20,
        "honesty_score": 0.40,
        "scenario_consistency_score": 1.0,
        "dropout_count": 0,
        "answer_change_rate": 0.05,
        "engagement_score": 0.95,
        "avg_response_time_ms": 5200.0,
    }

    multiplier, reasons = _calculate_governance_multiplier(honesty_only_row)

    assert multiplier == 1.0
    assert not any("contradiction" in reason.lower() for reason in reasons)


def test_governance_multiplier_floor_matches_documented_bound() -> None:
    # Heavily penalised but NOT a gaming stack: contradiction + dropouts +
    # erratic changes + low (not near-zero) engagement + zero cognition. Fewer
    # than two strong gaming signals, so the default 0.65 floor still holds.
    severe_row = {
        "impulsivity_index": 8.0,
        "honesty_score": 0.2,
        "scenario_consistency_score": 0.0,
        "dropout_count": 20,
        "answer_change_rate": 0.35,
        "engagement_score": 0.15,
        "avg_response_time_ms": 5000.0,
        "numeracy_score": 0.0,
        "CRT_score": 0.0,
        "financial_literacy_score": 0.0,
        "text_agency_score": 0.0,
        "text_problem_solving_flag": 0.0,
    }

    multiplier, reasons = _calculate_governance_multiplier(severe_row)

    assert multiplier == 0.65
    assert len(reasons) > 4


def test_gaming_stack_escalation_bypasses_default_floor() -> None:
    # A *prepared* gamer: perfect cognitive scores (memorised answers) but the
    # behaviour is mechanical — straight-lining + fast-pattern scenario gaming +
    # near-zero engagement. Two-plus independent gaming signals must bypass the
    # 0.65 floor and drop to the severe floor despite correct answers.
    gaming_row = {
        "honesty_score": 1.0,
        "scenario_consistency_score": 1.0,
        "numeracy_score": 1.0,
        "CRT_score": 1.0,
        "financial_literacy_score": 1.0,
        "avg_response_time_ms": 490.0,
        "session_duration_sec": 55.0,
        "answer_change_rate": 0.0,
        "engagement_score": 0.05,
        "scenario_fast_gaming": 1.0,
        "scenario_straight_lining_ratio": 1.0,
    }

    multiplier, reasons = _calculate_governance_multiplier(gaming_row)

    assert multiplier == SEVERE_GOVERNANCE_MULTIPLIER_MIN
    assert any("gaming signals stacked" in reason.lower() for reason in reasons)


def test_single_gaming_signal_does_not_escalate() -> None:
    # A fast but legitimate user trips exactly one gaming signal (fast-pattern)
    # with varied answers and healthy engagement. One signal alone must NOT
    # escalate — the multiplier stays well above the severe floor.
    fast_legit_row = {
        "honesty_score": 1.0,
        "scenario_consistency_score": 1.0,
        "numeracy_score": 1.0,
        "CRT_score": 1.0,
        "financial_literacy_score": 1.0,
        "avg_response_time_ms": 1800.0,
        "session_duration_sec": 210.0,
        "answer_change_rate": 0.10,
        "engagement_score": 0.80,
        "scenario_fast_gaming": 1.0,
        "scenario_straight_lining_ratio": 0.43,
    }

    multiplier, reasons = _calculate_governance_multiplier(fast_legit_row)

    assert multiplier > SEVERE_GOVERNANCE_MULTIPLIER_MIN
    assert not any("gaming signals stacked" in reason.lower() for reason in reasons)
