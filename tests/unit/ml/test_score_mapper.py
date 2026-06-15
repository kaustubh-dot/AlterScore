from backend.app.core.constants import (
    SCORE_BASE,
    SCORE_LOG_ODDS_FACTOR,
    SCORE_PDO,
    SCORE_ANCHOR_SCORE,
    SCORE_ANCHOR_ODDS,
)
from backend.ml.inference.score_mapper import (
    compute_percentile,
    get_loan_eligibility,
    get_risk_band,
    probability_to_score,
    resolve_score_mapping_config,
    score_mapping_debug,
    DEFAULT_SCORE_MAPPING_CONFIG,
)


def test_score_policy_constants_are_derived_not_hardcoded() -> None:
    import math

    expected_factor = SCORE_PDO / math.log(2.0)
    expected_base = SCORE_ANCHOR_SCORE - expected_factor * math.log(SCORE_ANCHOR_ODDS)
    assert abs(SCORE_LOG_ODDS_FACTOR - expected_factor) < 1e-6
    assert abs(SCORE_BASE - expected_base) < 1e-6


def test_default_config_uses_derived_constants() -> None:
    assert DEFAULT_SCORE_MAPPING_CONFIG.score_base == SCORE_BASE
    assert DEFAULT_SCORE_MAPPING_CONFIG.log_odds_factor == SCORE_LOG_ODDS_FACTOR


def test_probability_to_score_tracks_boundary_midpoint_and_upper_tail() -> None:
    # Even-odds (p=0.50) maps to SCORE_BASE (derived from anchor, not 500)
    midpoint_score = probability_to_score(0.50)
    strong_score = probability_to_score(0.72)
    upper_tail_score = probability_to_score(0.90)

    assert midpoint_score == int(round(SCORE_BASE))
    assert 300 <= strong_score <= 850
    assert 300 <= upper_tail_score <= 850
    assert midpoint_score < strong_score < upper_tail_score


def test_probability_to_score_is_monotonic_and_bounded() -> None:
    low_score = probability_to_score(0.1)
    mid_score = probability_to_score(0.5)
    high_score = probability_to_score(0.9)

    assert 300 <= low_score <= 850
    assert 300 <= mid_score <= 850
    assert 300 <= high_score <= 850
    assert low_score <= mid_score <= high_score


def test_score_mapping_full_range_reachable() -> None:
    # Good applicants (p=0.96+) must reach Excellent (>=750)
    top_score = probability_to_score(0.96)
    assert top_score >= 750, f"p=0.96 -> {top_score}, Excellent (750+) unreachable"

    # Weak applicants (p=0.30) must land in Poor (<550)
    weak_score = probability_to_score(0.30)
    assert weak_score < 550, f"p=0.30 -> {weak_score}, expected Poor (<550)"


def test_probability_to_score_supports_manifest_mapping_config() -> None:
    config = {
        "method": "log_odds",
        "score_base": 520,
        "log_odds_factor": 70,
        "probability_clip_min": 0.02,
        "probability_clip_max": 0.98,
        "score_min": 300,
        "score_max": 850,
        "calibration": "none",
    }

    details = score_mapping_debug(0.50, config)

    assert probability_to_score(0.50, config) == 520
    assert details["method"] == "log_odds"
    assert details["score_base"] == 520
    assert details["log_odds_factor"] == 70


def test_score_mapping_config_rejects_invalid_probability_clips() -> None:
    config = {
        "probability_clip_min": 0.99,
        "probability_clip_max": 0.01,
    }

    try:
        resolve_score_mapping_config(config)
    except ValueError as exc:
        assert "probability clips" in str(exc)
    else:
        raise AssertionError("invalid score mapping clips should fail validation")


def test_risk_bands_and_loan_eligibility_thresholds_are_stable() -> None:
    assert get_risk_band(540) == "poor"
    assert get_risk_band(600) == "fair"
    assert get_risk_band(700) == "good"
    assert get_risk_band(780) == "excellent"

    eligibility = get_loan_eligibility(700)

    assert eligibility["band"] == "good"
    assert eligibility["amount_min"] == 10000
    assert eligibility["amount_max"] == 30000


def test_compute_percentile_supports_saved_lookup_payloads_and_fallback() -> None:
    percentile_payload = {
        "score_to_percentile": {
            "300": 1,
            "560": 50,
            "850": 99,
        }
    }

    assert compute_percentile(560, percentile_payload) == 50
    assert compute_percentile(850, percentile_payload) == 99
    assert 0 <= compute_percentile(620, None) <= 100


def test_compute_percentile_supports_multi_model_saved_payloads() -> None:
    percentile_payload = {
        "default_model_name": "logistic_regression",
        "models": {
            "logistic_regression": {
                "score_to_percentile": {
                    "560": 47,
                }
            },
            "xgboost": {
                "score_to_percentile": {
                    "560": 52,
                }
            },
        },
    }

    assert compute_percentile(560, percentile_payload) == 47
