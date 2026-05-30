"""Unit tests for the v2 scenario analyzer.

Tests:
- Feature contribution mapping from known option IDs
- S1/S8 consistency score computation (match, mismatch, partial)
- Fast-pattern gaming detection
- Feature blending with existing psychometric values
- Edge cases: missing answers, unknown option IDs, neutral priors
"""

from __future__ import annotations

import pytest

from backend.ml.features.scenario_analyzer import (
    analyze_scenario_responses,
    compute_scenario_enriched_features,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _full_scenario_answers(
    s1="s1_b",
    s2="s2_b",
    s3="s3_b",
    s4="s4_b",
    s5="s5_b",
    s6="s6_c",
    s8="s8_b",
    first_click_ms=8000,
) -> dict:
    """Build a complete scenario answer payload (all scenarios answered)."""
    return {
        "scenario_s1": {
            "primary": s1,
            "least": None,
            "first_click_ms": first_click_ms,
            "change_count": 0,
        },
        "scenario_s2": {
            "primary": s2,
            "least": None,
            "first_click_ms": first_click_ms,
            "change_count": 0,
        },
        "scenario_s3": {
            "primary": s3,
            "least": None,
            "first_click_ms": first_click_ms,
            "change_count": 0,
        },
        "scenario_s4": {
            "primary": s4,
            "least": None,
            "first_click_ms": first_click_ms,
            "change_count": 0,
        },
        "scenario_s5": {
            "primary": s5,
            "least": None,
            "first_click_ms": first_click_ms,
            "change_count": 0,
        },
        "scenario_s6": {
            "primary": s6,
            "least": None,
            "first_click_ms": first_click_ms,
            "change_count": 0,
        },
        "scenario_s8": {
            "primary": s8,
            "least": None,
            "first_click_ms": first_click_ms,
            "change_count": 0,
        },
    }


def _neutral_psychometric() -> dict[str, float]:
    """Neutral (0.5) priors for all psychometric features."""
    return {
        "numeracy_score": 0.5,
        "CRT_score": 0.5,
        "financial_literacy_score": 0.5,
        "future_orientation": 0.5,
        "delay_discounting_rate": 0.5,
        "risk_attitude": 0.5,
        "risk_consistency_flag": 0.0,
        "loss_aversion_score": 0.5,
        "locus_of_control": 0.5,
        "conscientiousness_score": 0.5,
        "social_capital_score": 0.5,
        "honesty_score": 0.5,
        "resilience_score": 0.5,
        "reciprocity_norm": 0.5,
    }


# ---------------------------------------------------------------------------
# 1. Feature contribution mapping
# ---------------------------------------------------------------------------


class TestFeatureContributions:
    def test_high_conscientiousness_option_raises_conscientiousness(self):
        """Selecting s1_b (conscientiousness=1.0 primary) contributes to the feature.

        With 7 scenarios contributing at various weights, the cross-scenario average
        for conscientiousness_score won't reach 0.5 from s1_b alone since other
        scenarios contribute it only as a secondary signal at lower coded values.
        Assert it is meaningfully above the minimum floor (0.3).
        """
        answers = _full_scenario_answers(s1="s1_b")
        result = analyze_scenario_responses(answers)
        contributions = result["feature_contributions"]
        assert "conscientiousness_score" in contributions
        assert contributions["conscientiousness_score"] > 0.3

    def test_low_future_orientation_option_lowers_future_orientation(self):
        """Selecting s3_d (future_orientation=0.1) should lower future_orientation."""
        answers = _full_scenario_answers(s3="s3_d")
        result = analyze_scenario_responses(answers)
        # future_orientation should be pulled down by the windfall option
        contributions = result["feature_contributions"]
        assert "future_orientation" in contributions
        # The blended contribution will be lower than 1.0 given s3_d's low value
        assert contributions["future_orientation"] < 0.8

    def test_all_outputs_clipped_to_unit_interval(self):
        """All feature contribution values must be in [0.0, 1.0]."""
        answers = _full_scenario_answers()
        result = analyze_scenario_responses(answers)
        for feature_name, value in result["feature_contributions"].items():
            assert (
                0.0 <= value <= 1.0
            ), f"Feature '{feature_name}' out of range: {value}"

    def test_unknown_option_id_skipped_gracefully(self):
        """Unknown option IDs should be skipped without raising exceptions."""
        answers = _full_scenario_answers()
        answers["scenario_s1"] = {
            "primary": "s1_zzz",
            "least": None,
            "first_click_ms": 5000,
            "change_count": 0,
        }
        result = analyze_scenario_responses(answers)
        # Should complete without raising; s1 contribution simply skipped
        assert isinstance(result["feature_contributions"], dict)

    def test_missing_scenario_skipped_gracefully(self):
        """If a scenario is entirely missing from answers, it's skipped."""
        answers = _full_scenario_answers()
        del answers["scenario_s3"]
        result = analyze_scenario_responses(answers)
        assert isinstance(result["feature_contributions"], dict)

    def test_string_option_id_accepted(self):
        """Legacy string-format option IDs should be handled (not just dict format)."""
        answers = _full_scenario_answers()
        answers["scenario_s2"] = "s2_b"  # legacy string format
        result = analyze_scenario_responses(answers)
        assert isinstance(result["feature_contributions"], dict)


# ---------------------------------------------------------------------------
# 2. Consistency score computation
# ---------------------------------------------------------------------------


class TestConsistencyScore:
    def test_matching_s1_s8_pair_returns_high_score(self):
        """Picking s1_b and s8_b (mirrors) should return consistency = 1.0."""
        answers = _full_scenario_answers(s1="s1_b", s8="s8_b")
        result = analyze_scenario_responses(answers)
        assert result["scenario_consistency_score"] == 1.0

    def test_mismatched_s1_s8_with_same_feature_returns_partial_score(self):
        """s1_b (conscientiousness) and s8_c (also conscientiousness) = partial consistency."""
        answers = _full_scenario_answers(s1="s1_b", s8="s8_c")
        result = analyze_scenario_responses(answers)
        # Both map to conscientiousness as primary feature, so partial credit
        assert result["scenario_consistency_score"] == 0.65

    def test_fully_opposite_s1_s8_returns_low_score(self):
        """s1_a (future_orientation) vs s8_b (conscientiousness) = inconsistent."""
        answers = _full_scenario_answers(s1="s1_a", s8="s8_b")
        result = analyze_scenario_responses(answers)
        assert result["scenario_consistency_score"] == 0.0

    def test_missing_s1_returns_neutral_consistency(self):
        """If S1 is not answered, consistency should be 0.5 (neutral)."""
        answers = _full_scenario_answers()
        del answers["scenario_s1"]
        result = analyze_scenario_responses(answers)
        assert result["scenario_consistency_score"] == 0.5

    def test_missing_s8_returns_neutral_consistency(self):
        """If S8 is not answered, consistency should be 0.5 (neutral)."""
        answers = _full_scenario_answers()
        del answers["scenario_s8"]
        result = analyze_scenario_responses(answers)
        assert result["scenario_consistency_score"] == 0.5

    @pytest.mark.parametrize(
        "pair",
        [
            ("s1_a", "s8_a"),
            ("s1_b", "s8_b"),
            ("s1_c", "s8_c"),
            ("s1_d", "s8_d"),
        ],
    )
    def test_all_consistent_pairs_return_1_0(self, pair):
        """All four S1/S8 semantic mirror pairs should return 1.0 consistency."""
        s1, s8 = pair
        answers = _full_scenario_answers(s1=s1, s8=s8)
        result = analyze_scenario_responses(answers)
        assert result["scenario_consistency_score"] == 1.0


# ---------------------------------------------------------------------------
# 3. Fast-pattern gaming detection
# ---------------------------------------------------------------------------


class TestFastPatternGaming:
    def test_normal_response_times_not_flagged(self):
        """8-second average per scenario is normal — should not flag gaming."""
        answers = _full_scenario_answers(first_click_ms=8000)
        result = analyze_scenario_responses(answers)
        assert result["fast_pattern_gaming"] is False

    def test_very_fast_responses_flagged(self):
        """< 4000ms average across all scenarios should trigger gaming flag."""
        answers = _full_scenario_answers(first_click_ms=1500)
        result = analyze_scenario_responses(answers)
        assert result["fast_pattern_gaming"] is True

    def test_threshold_boundary_not_flagged(self):
        """Exactly at the 4000ms threshold should not be flagged."""
        answers = _full_scenario_answers(first_click_ms=4000)
        result = analyze_scenario_responses(answers)
        assert result["fast_pattern_gaming"] is False

    def test_missing_click_times_not_flagged(self):
        """If first_click_ms is None for all scenarios, gaming flag should be False."""
        answers = _full_scenario_answers()
        for key in answers:
            answers[key]["first_click_ms"] = None
        result = analyze_scenario_responses(answers)
        assert result["fast_pattern_gaming"] is False

    def test_fewer_than_4_click_times_not_flagged(self):
        """With fewer than 4 click times recorded, flag should not trigger."""
        answers = _full_scenario_answers(first_click_ms=500)
        # Zero out all but 3 click times
        keys = list(answers.keys())
        for key in keys[3:]:
            answers[key]["first_click_ms"] = None
        result = analyze_scenario_responses(answers)
        assert result["fast_pattern_gaming"] is False


# ---------------------------------------------------------------------------
# 4. Feature blending
# ---------------------------------------------------------------------------


class TestFeatureBlending:
    def test_blend_raises_low_prior_when_scenario_high(self):
        """If psychometric prior is 0.3 and scenario says 1.0, blend should be > 0.3."""
        base = _neutral_psychometric()
        base["conscientiousness_score"] = 0.3
        answers = _full_scenario_answers(
            s1="s1_b", s6="s6_b"
        )  # high conscientiousness picks
        enriched = compute_scenario_enriched_features(base, answers)
        assert enriched["conscientiousness_score"] > 0.3

    def test_blend_lowers_high_prior_when_scenario_low(self):
        """If psychometric prior is 0.9 and scenario says low value, blend should be < 0.9."""
        base = _neutral_psychometric()
        base["future_orientation"] = 0.9
        answers = _full_scenario_answers(s3="s3_d")  # future_orientation = 0.1
        enriched = compute_scenario_enriched_features(base, answers)
        assert enriched["future_orientation"] < 0.9

    def test_blend_respects_psychometric_dominance(self):
        """Psychometric weight is 0.60; a neutral prior (0.5) + scenario (1.0) → ~0.7."""
        base = _neutral_psychometric()
        base["conscientiousness_score"] = 0.5
        # Pick options that strongly signal conscientiousness = 1.0 across multiple scenarios
        answers = _full_scenario_answers(s1="s1_b", s6="s6_b", s3="s3_c")
        enriched = compute_scenario_enriched_features(base, answers)
        # Should be above 0.5 but not reach 1.0 since psychometric (0.5) pulls down
        assert 0.5 < enriched["conscientiousness_score"] < 1.0

    def test_numeracy_unchanged_by_scenario_blending(self):
        """Numeracy comes only from objective questions — scenarios don't contribute to it."""
        base = _neutral_psychometric()
        base["numeracy_score"] = 0.75
        answers = _full_scenario_answers()
        enriched = compute_scenario_enriched_features(base, answers)
        # Numeracy should not change since no scenario contributes to it
        assert enriched["numeracy_score"] == pytest.approx(0.75)

    def test_all_blended_values_clipped_to_unit_interval(self):
        """All blended feature values must be in [0.0, 1.0]."""
        base = _neutral_psychometric()
        answers = _full_scenario_answers()
        enriched = compute_scenario_enriched_features(base, answers)
        for feature_name, value in enriched.items():
            if isinstance(value, float):
                assert (
                    0.0 <= value <= 1.0
                ), f"Enriched feature '{feature_name}' out of range: {value}"

    def test_scenario_consistency_score_present_in_output(self):
        """compute_scenario_enriched_features should expose scenario_consistency_score."""
        base = _neutral_psychometric()
        answers = _full_scenario_answers(s1="s1_b", s8="s8_b")
        enriched = compute_scenario_enriched_features(base, answers)
        assert "scenario_consistency_score" in enriched
        assert enriched["scenario_consistency_score"] == 1.0

    def test_scenario_fast_gaming_present_in_output(self):
        """compute_scenario_enriched_features should expose scenario_fast_gaming."""
        base = _neutral_psychometric()
        answers = _full_scenario_answers(first_click_ms=1000)
        enriched = compute_scenario_enriched_features(base, answers)
        assert "scenario_fast_gaming" in enriched
        assert enriched["scenario_fast_gaming"] == 1.0


# ---------------------------------------------------------------------------
# 5. Empty / degenerate input
# ---------------------------------------------------------------------------


class TestDegenerateInput:
    def test_empty_answers_returns_empty_contributions(self):
        """Empty answers dict should return empty feature contributions."""
        result = analyze_scenario_responses({})
        assert result["feature_contributions"] == {}
        assert result["scenario_consistency_score"] == 0.5
        assert result["fast_pattern_gaming"] is False

    def test_non_scenario_keys_ignored(self):
        """Non-scenario keys in answers (e.g. numeracy_q1) should be silently ignored."""
        answers = {"numeracy_q1": 6600, "CRT_q1": 5}
        result = analyze_scenario_responses(answers)
        assert isinstance(result["feature_contributions"], dict)


# ---------------------------------------------------------------------------
# 6. Straight-lining detection
# ---------------------------------------------------------------------------


class TestStraightLining:
    def test_all_same_suffix_returns_1_0(self):
        """Selecting the exact same option suffix (e.g. 'a') in all scenarios returns ratio 1.0."""
        answers = _full_scenario_answers(
            s1="s1_a", s2="s2_a", s3="s3_a", s4="s4_a", s5="s5_a", s6="s6_a", s8="s8_a"
        )
        result = analyze_scenario_responses(answers)
        assert result["scenario_straight_lining_ratio"] == 1.0

        enriched = compute_scenario_enriched_features(_neutral_psychometric(), answers)
        assert enriched["scenario_straight_lining_ratio"] == 1.0

    def test_six_out_of_seven_same_suffix_returns_0_857(self):
        """Selecting the same suffix in 6 out of 7 scenarios returns ratio approx 0.857."""
        answers = _full_scenario_answers(
            s1="s1_a", s2="s2_a", s3="s3_a", s4="s4_a", s5="s5_a", s6="s6_a", s8="s8_b"
        )
        result = analyze_scenario_responses(answers)
        assert result["scenario_straight_lining_ratio"] == pytest.approx(6 / 7)

    def test_no_answers_returns_0_0(self):
        """Empty or degenerate answers return straight-lining ratio of 0.0."""
        result = analyze_scenario_responses({})
        assert result["scenario_straight_lining_ratio"] == 0.0
