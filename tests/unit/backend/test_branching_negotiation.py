"""Focused exhaustive tests for the Phase 2 negotiation scenario."""

from __future__ import annotations

from fractions import Fraction

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
from backend.app.branching.negotiation import (
    build_forecast_shortfall_negotiation_scenario,
)


def _assert_state_domain(state: FinancialState) -> None:
    assert isinstance(state, FinancialState)
    assert tuple(state.as_dict()) == STATE_FIELDS
    assert all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for value in state.as_dict().values()
    )
    assert state.required_payments_met <= state.required_payments_due


def test_definition_exposes_three_structured_stages_and_nine_unique_options() -> None:
    definition = build_forecast_shortfall_negotiation_scenario()

    assert len(definition.stages) == 3
    assert tuple(stage.stage_index for stage in definition.stages) == (1, 2, 3)
    assert all(stage.prompt for stage in definition.stages)
    assert all(len(stage.options) == 3 for stage in definition.stages)
    assert all(option.label for stage in definition.stages for option in stage.options)

    option_ids = [
        option.option_id for stage in definition.stages for option in stage.options
    ]
    assert len(option_ids) == len(set(option_ids)) == 9
    for stage in definition.stages:
        presentation = stage.presentation()
        assert presentation["stage_index"] == stage.stage_index
        assert presentation["presentation_id"] == stage.presentation_id
        assert presentation["prompt"] == stage.prompt
        assert len(presentation["options"]) == 3
        assert all(
            set(option) == {"option_id", "label"} for option in presentation["options"]
        )


def test_prompts_disclose_starting_facts_and_link_later_decisions() -> None:
    definition = build_forecast_shortfall_negotiation_scenario()
    prompts = tuple(stage.prompt for stage in definition.stages)

    for fact in ("₹12,000", "₹9,000", "₹6,000", "₹24,000", "₹30,000"):
        assert fact in prompts[0]
    assert "created by your collection decision" in prompts[1]
    assert "created by your first two decisions" in prompts[2]


def test_all_27_paths_are_reachable_and_have_valid_state_domains() -> None:
    definition = build_forecast_shortfall_negotiation_scenario()
    paths = enumerate_paths(definition)
    results = evaluate_all_paths(definition)

    assert len(paths) == len(set(paths)) == 27
    assert len(results) == 27
    assert tuple(result.option_ids for result in results) == paths

    for path, result in zip(paths, results, strict=True):
        assert result.option_ids == path
        assert result.scenario_presentation_id == definition.scenario_presentation_id
        assert result.starting_state == definition.starting_state
        assert len(result.timeline) == 3
        _assert_state_domain(result.starting_state)
        _assert_state_domain(result.terminal_state)

        previous = result.starting_state
        for expected_stage, evidence in enumerate(result.timeline, start=1):
            assert evidence.scenario_presentation_id == (
                definition.scenario_presentation_id
            )
            assert evidence.stage_index == expected_stage
            assert evidence.presentation_id == (
                definition.stages[expected_stage - 1].presentation_id
            )
            assert evidence.state_before == previous
            assert evidence.selected_option_id == path[expected_stage - 1]
            assert evidence.selected_option_label
            assert evidence.state_delta == StateDelta.from_states(
                evidence.state_before,
                evidence.state_after,
            )
            _assert_state_domain(evidence.state_before)
            _assert_state_domain(evidence.state_after)
            previous = evidence.state_after

        assert result.timeline[-1].state_after == result.terminal_state


def test_replaying_each_path_is_exactly_deterministic() -> None:
    definition = build_forecast_shortfall_negotiation_scenario()

    paths = enumerate_paths(definition)
    first_pass = tuple(run_scenario(definition, path) for path in paths)
    second_pass = tuple(run_scenario(definition, path) for path in paths)

    assert first_pass == second_pass == evaluate_all_paths(definition)
    assert all(
        result.starting_state == definition.starting_state for result in first_pass
    )


def test_timeline_has_three_linked_transition_evidence_records() -> None:
    definition = build_forecast_shortfall_negotiation_scenario()

    for result in evaluate_all_paths(definition):
        assert len(result.timeline) == 3
        assert result.timeline[0].state_before == result.starting_state
        assert result.timeline[-1].state_after == result.terminal_state

        for index, evidence in enumerate(result.timeline, start=1):
            assert evidence.scenario_presentation_id == (
                definition.scenario_presentation_id
            )
            assert evidence.stage_index == index
            assert evidence.presentation_id == (
                definition.stages[index - 1].presentation_id
            )
            assert evidence.selected_option_id == result.option_ids[index - 1]
            assert evidence.selected_option_label
            assert isinstance(evidence.state_before, FinancialState)
            assert isinstance(evidence.state_after, FinancialState)
            assert evidence.state_delta == StateDelta.from_states(
                evidence.state_before,
                evidence.state_after,
            )
            for state in (evidence.state_before, evidence.state_after):
                assert tuple(state.as_dict()) == STATE_FIELDS
                assert all(
                    isinstance(value, int)
                    and not isinstance(value, bool)
                    and value >= 0
                    for value in state.as_dict().values()
                )
                assert state.required_payments_met <= state.required_payments_due
            assert evidence.state_after.as_dict() == {
                field_name: getattr(evidence.state_before, field_name)
                + getattr(evidence.state_delta, field_name)
                for field_name in STATE_FIELDS
            }
            if index < 3:
                assert evidence.state_after == result.timeline[index].state_before


def test_terminal_dimensions_and_scores_stay_within_frozen_bounds() -> None:
    definition = build_forecast_shortfall_negotiation_scenario()

    for result in evaluate_all_paths(definition):
        assert all(
            Fraction(0, 1) <= dimension <= Fraction(100, 1)
            for dimension in result.dimensions.as_dict().values()
        )
        assert isinstance(result.scenario_score, Fraction)
        assert Fraction(0, 1) <= result.scenario_score <= Fraction(100, 1)
        assert result.raw_scenario_score == branching_scenario_score(result.dimensions)


def test_collection_actions_and_payment_arrangements_are_accounted() -> None:
    definition = build_forecast_shortfall_negotiation_scenario()
    results = evaluate_all_paths(definition)
    collection_effects = {
        "collect_routine_amount": (6_000, 0),
        "collect_reconciled_amount": (12_000, 0),
        "collect_accelerated_amount": (18_000, 1_000),
    }

    assert {option.option_id for option in definition.stages[0].options} == set(
        collection_effects
    )
    assert all(
        "forecast" not in option.option_id for option in definition.stages[0].options
    )

    for result in results:
        collection = result.timeline[0]
        collected, concession = collection_effects[collection.selected_option_id]
        assert collection.state_delta.cash_available == collected
        assert collection.state_delta.confirmed_inflows == -collected
        assert collection.state_delta.avoidable_cost == concession

        arrangement = result.timeline[2]
        if arrangement.selected_option_id == "apply_all_available_cash":
            assert arrangement.state_delta.required_payments_met == min(
                arrangement.state_before.cash_available,
                arrangement.state_before.unmet_required_payments,
            )
            assert arrangement.state_delta.required_payments_met > 0
        elif arrangement.selected_option_id == "make_good_faith_payment":
            assert arrangement.state_delta.required_payments_met == 6_000
        else:
            assert arrangement.selected_option_id == "extend_due_date"
            assert arrangement.state_delta.late_payments == 1
            assert arrangement.state_delta.avoidable_cost == 500

    assert any(
        result.terminal_state.required_payments_met
        == result.terminal_state.required_payments_due
        for result in results
    )


def test_option_applications_are_pure_and_repeatable() -> None:
    definition = build_forecast_shortfall_negotiation_scenario()

    for stage in definition.stages:
        for option in stage.options:
            original = definition.starting_state
            first = option.apply(original)
            second = option.apply(original)

            assert original == definition.starting_state
            assert first == second
            _assert_state_domain(first)
