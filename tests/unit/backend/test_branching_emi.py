"""Focused exhaustive tests for the EMI/supplier branching scenario."""

from __future__ import annotations

from fractions import Fraction

from backend.app.branching.emi import build_emi_supplier_scenario
from backend.app.branching.engine import (
    enumerate_paths,
    evaluate_all_paths,
    run_scenario,
)
from backend.app.branching.model import (
    STATE_FIELDS,
    FinancialState,
    StateDelta,
    branching_scenario_score,
)


def _assert_state_domain(state: FinancialState) -> None:
    assert isinstance(state, FinancialState)
    for field_name in STATE_FIELDS:
        value = getattr(state, field_name)
        assert isinstance(value, int)
        assert not isinstance(value, bool)
        assert value >= 0
    assert state.required_payments_met <= state.required_payments_due


def test_definition_has_three_structured_stages_and_nine_unique_options() -> None:
    definition = build_emi_supplier_scenario()

    assert len(definition.stages) == 3
    assert [stage.stage_index for stage in definition.stages] == [1, 2, 3]
    assert all(stage.prompt for stage in definition.stages)
    assert all(len(stage.options) == 3 for stage in definition.stages)
    assert len(
        {
            option.option_id
            for stage in definition.stages
            for option in stage.options
        }
    ) == 9

    for stage in definition.stages:
        presentation = stage.presentation()
        assert presentation["stage_index"] == stage.stage_index
        assert presentation["presentation_id"] == stage.presentation_id
        assert presentation["prompt"] == stage.prompt
        assert len(presentation["options"]) == 3
        assert all(
            set(option) == {"option_id", "label"}
            for option in presentation["options"]
        )


def test_all_27_paths_are_reachable_with_valid_timeline_states_and_scores() -> None:
    definition = build_emi_supplier_scenario()
    paths = enumerate_paths(definition)
    results = evaluate_all_paths(definition)

    assert len(paths) == 27
    assert len(set(paths)) == 27
    assert len(results) == 27

    for path, result in zip(paths, results, strict=True):
        assert result.option_ids == path
        assert result.scenario_presentation_id == definition.scenario_presentation_id
        assert result.starting_state == definition.starting_state
        assert len(result.timeline) == 3
        _assert_state_domain(result.starting_state)
        _assert_state_domain(result.terminal_state)

        previous = result.starting_state
        for expected_stage, evidence in enumerate(result.timeline, start=1):
            stage = definition.stages[expected_stage - 1]
            assert evidence.scenario_presentation_id == definition.scenario_presentation_id
            assert evidence.stage_index == expected_stage
            assert evidence.presentation_id == stage.presentation_id
            assert evidence.state_before == previous
            assert evidence.selected_option_id == path[expected_stage - 1]
            assert evidence.selected_option_id in stage.option_map()
            assert evidence.selected_option_label
            assert evidence.state_delta == StateDelta.from_states(
                evidence.state_before,
                evidence.state_after,
            )
            _assert_state_domain(evidence.state_before)
            _assert_state_domain(evidence.state_after)
            previous = evidence.state_after

        assert result.timeline[-1].state_after == result.terminal_state
        assert all(
            isinstance(value, Fraction)
            and Fraction(0) <= value <= Fraction(100)
            for value in result.dimensions.as_dict().values()
        )
        assert isinstance(result.scenario_score, Fraction)
        assert Fraction(0) <= result.scenario_score <= Fraction(100)
        assert result.scenario_score == branching_scenario_score(result.dimensions)


def test_every_complete_path_replays_to_the_same_result() -> None:
    definition = build_emi_supplier_scenario()
    paths = enumerate_paths(definition)

    first_pass = tuple(run_scenario(definition, path) for path in paths)
    second_pass = tuple(run_scenario(definition, path) for path in paths)

    assert first_pass == second_pass
    assert first_pass == evaluate_all_paths(definition)


def test_option_applications_are_pure_and_repeatable() -> None:
    definition = build_emi_supplier_scenario()

    for stage in definition.stages:
        for option in stage.options:
            original = definition.starting_state
            first = option.apply(original)
            second = option.apply(original)
            assert original == definition.starting_state
            assert first == second
            _assert_state_domain(first)
