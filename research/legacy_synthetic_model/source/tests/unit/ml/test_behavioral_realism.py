from backend.app.services.scoring import _calculate_governance_multiplier
from backend.ml.inference.score_mapper import probability_to_score
from backend.ml.inference.text_quality import assess_text_response_quality


def test_text_quality_is_bounded_and_never_rejects_a_response() -> None:
    substantive = assess_text_response_quality(
        "I made a budget, reduced spending, found extra income, and followed the repayment plan carefully."
    )
    limited = assess_text_response_quality("I made a plan.")
    gibberish = assess_text_response_quality("plan " * 12)

    assert substantive.status == "substantive"
    assert substantive.score_adjustment_points == 0
    assert limited.status == "limited"
    assert limited.score_adjustment_points == -6
    assert gibberish.status == "gibberish"
    assert gibberish.score_adjustment_points == -12
    assert all(
        -assessment.max_penalty_points <= assessment.score_adjustment_points <= 0
        for assessment in (substantive, limited, gibberish)
    )


def test_text_quality_does_not_penalize_substantive_non_latin_text() -> None:
    assessment = assess_text_response_quality(
        "मैं अपने खर्चों की योजना बनाता हूं और हर महीने बचत करता हूं"
    )

    assert assessment.status == "substantive"
    assert assessment.score_adjustment_points == 0


def test_score_saturation_is_limited_to_the_extreme_tail() -> None:
    assert probability_to_score(0.968) < 850
    assert probability_to_score(0.995) == 850


def test_operational_diagnostics_have_no_post_model_score_multiplier() -> None:
    multiplier, reasons = _calculate_governance_multiplier(
        {
            "avg_response_time_ms": 100.0,
            "answer_change_rate": 1.0,
            "dropout_count": 20,
            "scenario_fast_gaming": 1.0,
            "scenario_straight_lining_ratio": 1.0,
        }
    )

    assert multiplier == 1.0
    assert reasons == []
