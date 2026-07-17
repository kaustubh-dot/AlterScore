"""Phase 3 unified-score composition and explanation checks."""

from __future__ import annotations

from fractions import Fraction

import pytest

from backend.app.branching import (
    build_branching_scenarios,
    enumerate_paths,
    evaluate_all_paths,
)
from backend.app.instrument import InvalidResponse, UnknownCanonicalId, generate_form
from backend.app.unified_scoring import (
    Explanation,
    build_unified_presentation,
    legacy_demo_score,
    quantize_fraction_half_up,
    score_unified_assessment,
)


def _best_paths() -> dict[str, tuple[str, ...]]:
    return {
        scenario.scenario_presentation_id: max(
            (
                (result.scenario_score, result.option_ids)
                for result in evaluate_all_paths(scenario)
            ),
            key=lambda pair: (pair[0], pair[1]),
        )[1]
        for scenario in build_branching_scenarios()
    }


def _worst_paths() -> dict[str, tuple[str, ...]]:
    return {
        scenario.scenario_presentation_id: min(
            (
                (result.scenario_score, result.option_ids)
                for result in evaluate_all_paths(scenario)
            ),
            key=lambda pair: (pair[0], pair[1]),
        )[1]
        for scenario in build_branching_scenarios()
    }


def _responses(
    form,
    paths: dict[str, tuple[str, ...]],
    *,
    all_objectives_correct: bool = True,
    best_static: bool = True,
) -> dict[str, object]:
    responses: dict[str, object] = {}
    answer_key = form.objective_answer_key()
    for item_id, correct_answer in answer_key.items():
        if all_objectives_correct:
            responses[item_id] = correct_answer
        else:
            responses[item_id] = 0 if correct_answer != 0 else 1

    rubric = form.static_rubric()
    for item in form.static_sjt_items:
        options = rubric[item.presentation_id]
        responses[item.presentation_id] = (
            max(options, key=options.get)
            if best_static
            else min(options, key=options.get)
        )

    for scenario in build_branching_scenarios():
        path = paths[scenario.scenario_presentation_id]
        for stage, option_id in zip(scenario.stages, path, strict=True):
            responses[stage.presentation_id] = option_id
    return responses


def _behavior_responses(form, offset: int = 0) -> dict[str, str]:
    responses: dict[str, str] = {}
    for index, item in enumerate(form.behavior_profile_items):
        responses[item.presentation_id] = item.options[(index + offset) % 6].option_id
    return responses


def test_unified_presentation_has_eighteen_scored_items_and_safe_public_shape() -> None:
    form = generate_form(20260715)
    presentation = build_unified_presentation(form)

    assert len(presentation.items) == 18
    assert sum(item.item_type == "objective" for item in presentation.items) == 8
    assert sum(item.item_type == "static_sjt" for item in presentation.items) == 4
    assert sum(item.item_type == "branching" for item in presentation.items) == 6
    assert len(presentation.behavior_profile_items) == 6

    dumped = presentation.model_dump()
    serialized = str(dumped).lower()
    for forbidden in (
        "correct_answer",
        "rubric_points",
        "generation_rule",
        "rationale",
        "seed",
    ):
        assert forbidden not in serialized


def test_perfect_profile_reconciles_and_receives_maintenance_guidance() -> None:
    form = generate_form(17)
    paths = _best_paths()
    result = score_unified_assessment(
        form,
        _responses(form, paths),
        _behavior_responses(form),
        narrative="A narrative is diagnostic only.",
    )

    assert result.objective_score == Fraction(100, 1)
    assert result.judgment_components == (Fraction(100, 1),) * 6
    assert result.judgment_score == Fraction(100, 1)
    assert result.financial_decision_index == 100
    assert result.legacy_demo_score == 850
    assert all(
        scenario.score_basis == "feasible_range_normalized"
        and scenario.scenario_score == 100
        for scenario in result.explanation.branching_scenarios
    )
    assert len(result.explanation.recommendations) == 1
    assert result.explanation.recommendations[0].evidence_type == "maintenance"
    assert result.explanation.recommendations[0].evidence_ids == []
    assert len(result.explanation.objective_items) == 8
    assert len(result.explanation.static_sjt_items) == 4
    assert len(result.explanation.branching_scenarios) == 2

    dumped = result.explanation.model_dump()
    serialized = str(dumped).lower()
    for forbidden in (
        "option_id",
        "rubric_points",
        "shap",
        "repayment_probability",
        "percentile",
    ):
        assert forbidden not in serialized


def test_mixed_profile_uses_unrounded_six_component_judgment_mean() -> None:
    form = generate_form(23)
    scenarios = build_branching_scenarios()
    paths = {
        scenario.scenario_presentation_id: enumerate_paths(scenario)[0]
        for scenario in scenarios
    }
    result = score_unified_assessment(
        form,
        _responses(
            form,
            paths,
            all_objectives_correct=False,
            best_static=False,
        ),
        _behavior_responses(form, offset=3),
    )

    expected_judgment = sum(result.judgment_components, Fraction(0, 1)) / 6
    expected_weighted = (
        Fraction(55, 100) * result.objective_score
        + Fraction(45, 100) * expected_judgment
    )
    expected_index = (expected_weighted.numerator // expected_weighted.denominator) + int(
        2 * (expected_weighted.numerator % expected_weighted.denominator)
        >= expected_weighted.denominator
    )
    assert result.judgment_score == expected_judgment
    assert result.financial_decision_index == expected_index
    assert result.legacy_demo_score == legacy_demo_score(expected_index)
    assert result.explanation.formula.weighted_total_exact == (
        f"{expected_weighted.numerator}/{expected_weighted.denominator}"
    )
    assert result.explanation.formula.judgment_score == quantize_fraction_half_up(
        expected_judgment
    )


def test_lowest_valid_submission_has_no_neutral_imputation_and_stays_bounded() -> None:
    form = generate_form(29)
    scenarios = build_branching_scenarios()
    paths = {
        scenario.scenario_presentation_id: enumerate_paths(scenario)[-1]
        for scenario in scenarios
    }
    result = score_unified_assessment(
        form,
        _responses(
            form,
            paths,
            all_objectives_correct=False,
            best_static=False,
        ),
        _behavior_responses(form, offset=5),
        narrative="",
    )

    assert result.objective_score == Fraction(0, 1)
    assert all(item.is_correct is False for item in result.explanation.objective_items)
    assert 0 <= result.judgment_score <= 100
    assert 0 <= result.financial_decision_index <= 100
    assert 300 <= result.legacy_demo_score <= 850


def test_domain_imbalanced_profiles_keep_objective_and_judgment_separate() -> None:
    form = generate_form(37)
    objective_strong = score_unified_assessment(
        form,
        _responses(
            form,
            _worst_paths(),
            all_objectives_correct=True,
            best_static=False,
        ),
        _behavior_responses(form),
    )
    judgment_strong = score_unified_assessment(
        form,
        _responses(
            form,
            _best_paths(),
            all_objectives_correct=False,
            best_static=True,
        ),
        _behavior_responses(form, offset=2),
    )

    assert objective_strong.objective_score == Fraction(100, 1)
    assert judgment_strong.objective_score == Fraction(0, 1)
    assert objective_strong.judgment_score < judgment_strong.judgment_score
    assert objective_strong.explanation.formula.objective_score == quantize_fraction_half_up(
        objective_strong.objective_score
    )
    assert judgment_strong.explanation.formula.objective_score == quantize_fraction_half_up(
        judgment_strong.objective_score
    )


def test_legacy_scale_covers_all_101_canonical_indices() -> None:
    assert [legacy_demo_score(index) for index in range(101)] == [
        300 + (Fraction(11, 2) * index + Fraction(1, 2)).numerator
        // (Fraction(11, 2) * index + Fraction(1, 2)).denominator
        for index in range(101)
    ]
    assert legacy_demo_score(0) == 300
    assert legacy_demo_score(1) == 306
    assert legacy_demo_score(50) == 575
    assert legacy_demo_score(99) == 845
    assert legacy_demo_score(100) == 850


def test_missing_and_extra_scored_ids_fail_closed() -> None:
    form = generate_form(31)
    responses = _responses(form, _best_paths())
    behavior = _behavior_responses(form)

    missing = dict(responses)
    missing.pop(next(iter(form.objective_answer_key())))
    with pytest.raises(InvalidResponse):
        score_unified_assessment(form, missing, behavior)

    extra = dict(responses)
    extra["unknown_phase3_item"] = 1
    with pytest.raises(UnknownCanonicalId):
        score_unified_assessment(form, extra, behavior)

    missing_branch = dict(responses)
    missing_branch.pop(build_branching_scenarios()[0].stages[0].presentation_id)
    with pytest.raises(InvalidResponse):
        score_unified_assessment(form, missing_branch, behavior)


@pytest.mark.parametrize("bad_value", [True, 1.5, None, -1])
def test_invalid_objective_values_fail_closed(bad_value: object) -> None:
    form = generate_form(37)
    responses = _responses(form, _best_paths())
    responses[next(iter(form.objective_answer_key()))] = bad_value
    with pytest.raises(InvalidResponse):
        score_unified_assessment(form, responses, _behavior_responses(form))


def test_behavior_narrative_and_mapping_order_do_not_change_score() -> None:
    form = generate_form(41)
    responses = _responses(form, _best_paths())
    behavior = _behavior_responses(form)
    first = score_unified_assessment(
        form,
        responses,
        behavior,
        narrative="First diagnostic narrative.",
    )
    reversed_responses = dict(reversed(tuple(responses.items())))
    changed_behavior = _behavior_responses(form, offset=2)
    second = score_unified_assessment(
        form,
        reversed_responses,
        changed_behavior,
        narrative="A completely different diagnostic narrative.",
    )

    assert first.objective_score == second.objective_score
    assert first.judgment_score == second.judgment_score
    assert first.financial_decision_index == second.financial_decision_index
    assert first.legacy_demo_score == second.legacy_demo_score
    assert first.explanation == second.explanation
    assert responses == dict(responses)


def test_explanation_replays_terminal_states_and_has_exact_safe_fields() -> None:
    form = generate_form(53)
    result = score_unified_assessment(
        form,
        _responses(form, _best_paths()),
        _behavior_responses(form),
    )

    assert isinstance(result.explanation, Explanation)
    for scenario_result, scenario_explanation in zip(
        result.branching_results,
        result.explanation.branching_scenarios,
        strict=True,
    ):
        assert scenario_explanation.timeline[-1].state_after == (
            scenario_explanation.terminal_state
        )
        assert len(scenario_explanation.timeline) == 3
        for index, evidence in enumerate(scenario_explanation.timeline):
            assert evidence.stage_index == index + 1
            assert evidence.state_after.model_dump() == {
                field: getattr(evidence.state_before, field)
                + getattr(evidence.state_delta, field)
                for field in evidence.state_before.model_fields
            }
            if index < 2:
                assert evidence.state_after == scenario_explanation.timeline[index + 1].state_before
        assert scenario_explanation.terminal_state == (
            scenario_explanation.timeline[-1].state_after
        )
        assert scenario_explanation.scenario_presentation_id == (
            scenario_result.scenario_presentation_id
        )


def test_recommendations_reference_only_actual_weaknesses() -> None:
    form = generate_form(61)
    scenarios = build_branching_scenarios()
    paths = {
        scenario.scenario_presentation_id: enumerate_paths(scenario)[-1]
        for scenario in scenarios
    }
    result = score_unified_assessment(
        form,
        _responses(form, paths, all_objectives_correct=False),
        _behavior_responses(form),
    )

    objective_ids = {
        item.presentation_id for item in form.objective_items
    }
    branching_ids = {
        scenario.scenario_presentation_id for scenario in scenarios
    }
    recommendations = result.explanation.recommendations
    assert recommendations
    for recommendation in recommendations:
        if recommendation.evidence_type == "objective":
            assert set(recommendation.evidence_ids) <= objective_ids
            assert all(
                not item.is_correct
                for item in result.explanation.objective_items
                if item.presentation_id in recommendation.evidence_ids
            )
        elif recommendation.evidence_type == "branching":
            assert set(recommendation.evidence_ids) <= branching_ids
        else:
            assert recommendation.evidence_ids == []


def test_all_eight_generated_objectives_have_worked_explanations() -> None:
    for seed in range(12):
        form = generate_form(seed)
        result = score_unified_assessment(
            form,
            _responses(form, _best_paths()),
            _behavior_responses(form),
        )
        answer_key = form.objective_answer_key()
        assert len(result.explanation.objective_items) == 8
        for item in result.explanation.objective_items:
            assert item.correct_answer == answer_key[item.presentation_id]
            assert item.submitted_answer == item.correct_answer
            assert item.is_correct is True
            assert item.worked_calculation
            assert item.concept_explanation


def test_every_one_of_the_54_branching_paths_replays_inside_unified_scorer() -> None:
    form = generate_form(71)
    behavior = _behavior_responses(form)
    scenarios = build_branching_scenarios()
    completed = 0
    for scenario in scenarios:
        for path in enumerate_paths(scenario):
            paths = {
                other.scenario_presentation_id: enumerate_paths(other)[0]
                for other in scenarios
            }
            paths[scenario.scenario_presentation_id] = path
            result = score_unified_assessment(
                form,
                _responses(form, paths),
                behavior,
            )
            assert result.branching_results[
                next(
                    index
                    for index, item in enumerate(scenarios)
                    if item.scenario_presentation_id
                    == scenario.scenario_presentation_id
                )
            ].option_ids == path
            completed += 1
    assert completed == 54


def test_scoring_is_deterministic_and_does_not_mutate_inputs() -> None:
    form = generate_form(83)
    responses = _responses(form, _best_paths())
    behavior = _behavior_responses(form)
    response_copy = dict(responses)
    behavior_copy = dict(behavior)
    first = score_unified_assessment(form, responses, behavior, narrative="Optional")
    second = score_unified_assessment(form, responses, behavior, narrative="Optional")

    assert first == second
    assert responses == response_copy
    assert behavior == behavior_copy
