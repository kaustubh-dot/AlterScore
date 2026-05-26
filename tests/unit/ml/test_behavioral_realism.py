import pytest
import numpy as np

from backend.ml.inference.feature_assembly import _apply_timing_realism_transforms
from backend.ml.nlp.extractor import _validate_text_quality, extract_nlp_features
from backend.ml.inference.score_mapper import probability_to_score
from backend.app.services.scoring import _calculate_governance_multiplier


def test_u_shaped_timing_transforms() -> None:
    # 1. Healthy thoughtful inputs
    healthy_inputs = {
        "avg_response_time_ms": 6500.0,
        "session_duration_sec": 190.0,
        "typing_speed_wpm": 60.0,
    }
    transformed_healthy = _apply_timing_realism_transforms(healthy_inputs)
    assert transformed_healthy["avg_response_time_ms"] == 6500.0
    assert transformed_healthy["session_duration_sec"] == 190.0
    assert transformed_healthy["typing_speed_wpm"] == 60.0

    # 2. Impulsive fast pacing
    fast_inputs = {
        "avg_response_time_ms": 500.0,
        "session_duration_sec": 30.0,
        "typing_speed_wpm": 200.0, # copy-pasting / bot typing
    }
    transformed_fast = _apply_timing_realism_transforms(fast_inputs)
    assert transformed_fast["avg_response_time_ms"] > 100000.0 # heavily inflated
    assert transformed_fast["session_duration_sec"] > 4000.0 # heavily inflated
    assert transformed_fast["typing_speed_wpm"] == 0.0 # penalized WPM


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
    assert high_prob_score < 850 # should not saturate early
    
    super_elite_score = probability_to_score(0.995)
    assert super_elite_score == 850 # perfect score remains reachable but difficult


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
        "impulsivity_index": 3.20, # highly impulsive
        "honesty_score": 0.40, # fails honesty check
        "dropout_count": 5, # switched tabs repeatedly
        "answer_change_rate": 0.45,
    }
    mult_game, reasons_game = _calculate_governance_multiplier(gaming_row)
    assert mult_game < 0.80 # heavily penalized
    assert len(reasons_game) > 2
