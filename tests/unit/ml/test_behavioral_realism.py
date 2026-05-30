from backend.ml.nlp.extractor import _validate_text_quality
from backend.ml.inference.score_mapper import probability_to_score
from backend.app.services.scoring import _calculate_governance_multiplier


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
    severe_row = {
        "impulsivity_index": 8.0,
        "honesty_score": 0.2,
        "scenario_consistency_score": 0.0,
        "dropout_count": 20,
        "answer_change_rate": 1.0,
        "engagement_score": 0.0,
        "scenario_fast_gaming": 1.0,
        "scenario_straight_lining_ratio": 1.0,
        "text_agency_score": 0.0,
        "text_problem_solving_flag": 0.0,
    }

    multiplier, reasons = _calculate_governance_multiplier(severe_row)

    assert multiplier == 0.65
    assert len(reasons) > 4
