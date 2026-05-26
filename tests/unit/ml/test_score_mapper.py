import pytest

from backend.ml.inference.score_mapper import (
    compute_percentile,
    get_loan_eligibility,
    get_risk_band,
    probability_to_score,
)


def test_probability_to_score_tracks_boundary_midpoint_and_upper_tail() -> None:
    midpoint_score = probability_to_score(0.50)
    strong_score = probability_to_score(0.72)
    upper_tail_score = probability_to_score(0.90)

    assert midpoint_score == 500
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
