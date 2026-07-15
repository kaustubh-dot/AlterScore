"""Tests for the shared Phase 2 state and exact terminal-score contract."""

from __future__ import annotations

from fractions import Fraction

import pytest

from backend.app.branching import (
    FinancialState,
    InvalidScenarioDefinition,
    InvalidState,
    InvalidTransition,
    STATE_FIELDS,
    BranchingStage,
    ScenarioDefinition,
    branching_scenario_score,
    pay_from_buffer,
    pay_from_cash,
    run_scenario,
    terminal_dimensions,
    validate_transition,
)


def _state(**overrides: int) -> FinancialState:
    values = dict.fromkeys(STATE_FIELDS, 0)
    values.update(overrides)
    return FinancialState(**values)


def test_state_domains_are_non_negative_integer_and_bounded() -> None:
    with pytest.raises(InvalidState):
        _state(cash_available=-1)
    with pytest.raises(InvalidState):
        _state(cash_available=True)
    with pytest.raises(InvalidState):
        _state(required_payments_due=10, required_payments_met=11)

    state = _state(cash_available=10, required_payments_due=4, required_payments_met=2)
    assert tuple(state.as_dict()) == STATE_FIELDS
    assert state.unmet_required_payments == 2
    assert state.liquid_resources == 10
    assert state.unencumbered_liquidity == 8
    assert state.remaining_plan_need == 2


def test_terminal_dimensions_and_score_use_exact_fractions() -> None:
    state = _state(
        cash_available=50,
        required_payments_due=100,
        required_payments_met=40,
        confirmed_inflows=20,
        essential_expenses=10,
        emergency_buffer=0,
        borrowing_cost=30,
        avoidable_cost=20,
        late_payments=1,
        unfunded_commitments=10,
    )
    dimensions = terminal_dimensions(state, initial_liquidity=100, cost_budget=100)
    assert dimensions.obligation_coverage == Fraction(40, 1)
    assert dimensions.liquidity_retention == Fraction(0, 1)
    assert dimensions.cost_efficiency == Fraction(50, 1)
    assert dimensions.plan_feasibility == Fraction(25, 2)
    assert branching_scenario_score(dimensions) == Fraction(223, 8)
    assert all(isinstance(value, Fraction) for value in dimensions.as_dict().values())


def test_zero_denominators_and_clamping_are_deterministic() -> None:
    complete = _state(
        cash_available=10_000,
        required_payments_due=0,
        required_payments_met=0,
        confirmed_inflows=10_000,
    )
    dimensions = terminal_dimensions(
        complete, initial_liquidity=1, cost_budget=1
    )
    assert dimensions.obligation_coverage == Fraction(100, 1)
    assert dimensions.liquidity_retention == Fraction(100, 1)
    assert dimensions.cost_efficiency == Fraction(100, 1)
    assert dimensions.plan_feasibility == Fraction(100, 1)


def test_linked_payment_conservation_accepts_cash_or_buffer_payment() -> None:
    before = _state(
        cash_available=50,
        required_payments_due=100,
        required_payments_met=20,
        emergency_buffer=10,
    )
    cash_after = pay_from_cash(before, 30)
    buffer_after = pay_from_buffer(before, 10)
    assert validate_transition(before, cash_after).required_payments_met == 30
    assert validate_transition(before, buffer_after).required_payments_met == 10


def test_linked_payment_conservation_rejects_worse_or_mixed_transitions() -> None:
    before = _state(
        cash_available=50,
        required_payments_due=100,
        required_payments_met=20,
        confirmed_inflows=10,
        essential_expenses=10,
        emergency_buffer=20,
        new_borrowing=5,
        borrowing_cost=2,
        avoidable_cost=3,
        late_payments=1,
        unfunded_commitments=10,
    )
    too_much_cash = before.replace(
        cash_available=0,
        required_payments_met=50,
    )
    with pytest.raises(InvalidTransition):
        validate_transition(before, too_much_cash)

    mixed_due = before.replace(
        cash_available=40,
        required_payments_due=90,
        required_payments_met=30,
    )
    with pytest.raises(InvalidTransition):
        validate_transition(before, mixed_due)

    payment_with_cost = before.replace(
        cash_available=40,
        required_payments_met=30,
        borrowing_cost=1,
    )
    with pytest.raises(InvalidTransition):
        validate_transition(before, payment_with_cost)

    payment_with_late = before.replace(
        cash_available=40,
        required_payments_met=30,
        late_payments=2,
    )
    with pytest.raises(InvalidTransition):
        validate_transition(before, payment_with_late)

    payment_with_avoidable_cost = before.replace(
        cash_available=40,
        required_payments_met=30,
        avoidable_cost=4,
    )
    with pytest.raises(InvalidTransition):
        validate_transition(before, payment_with_avoidable_cost)

    payment_with_lower_inflow = before.replace(
        cash_available=40,
        required_payments_met=30,
        confirmed_inflows=9,
    )
    with pytest.raises(InvalidTransition):
        validate_transition(before, payment_with_lower_inflow)

    payment_with_more_essentials = before.replace(
        cash_available=40,
        required_payments_met=30,
        essential_expenses=11,
    )
    with pytest.raises(InvalidTransition):
        validate_transition(before, payment_with_more_essentials)

    payment_with_more_unfunded = before.replace(
        cash_available=40,
        required_payments_met=30,
        unfunded_commitments=11,
    )
    with pytest.raises(InvalidTransition):
        validate_transition(before, payment_with_more_unfunded)

    decreasing_cumulative = before.replace(
        required_payments_met=19,
    )
    with pytest.raises(InvalidTransition):
        validate_transition(before, decreasing_cumulative)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("required_payments_due", 99),
        ("required_payments_met", 19),
        ("new_borrowing", 4),
        ("borrowing_cost", 1),
        ("avoidable_cost", 2),
        ("late_payments", 0),
    ),
)
def test_cumulative_fields_cannot_decrease(field_name: str, value: int) -> None:
    before = _state(
        required_payments_due=100,
        required_payments_met=20,
        new_borrowing=5,
        borrowing_cost=2,
        avoidable_cost=3,
        late_payments=1,
    )
    with pytest.raises(InvalidTransition):
        validate_transition(before, before.replace(**{field_name: value}))


def test_branching_definition_rejects_mutable_containers_and_boolean_stage_index() -> None:
    from backend.app.branching.scenarios import build_branching_scenarios

    definition = build_branching_scenarios()[0]
    stage = definition.stages[0]
    with pytest.raises(InvalidScenarioDefinition):
        BranchingStage(
            stage_index=True,
            presentation_id=stage.presentation_id,
            prompt=stage.prompt,
            options=stage.options,
        )
    with pytest.raises(InvalidScenarioDefinition):
        BranchingStage(
            stage_index=stage.stage_index,
            presentation_id=stage.presentation_id,
            prompt=stage.prompt,
            options=list(stage.options),
        )
    with pytest.raises(InvalidScenarioDefinition):
        ScenarioDefinition(
            scenario_presentation_id=definition.scenario_presentation_id,
            title=definition.title,
            starting_state=definition.starting_state,
            initial_liquidity=definition.initial_liquidity,
            cost_budget=definition.cost_budget,
            stages=list(definition.stages),
        )


def test_branching_definition_rejects_malformed_metadata_and_children() -> None:
    from backend.app.branching.scenarios import build_branching_scenarios

    definition = build_branching_scenarios()[0]
    stage = definition.stages[0]
    with pytest.raises(InvalidScenarioDefinition):
        BranchingStage(
            stage_index=stage.stage_index,
            presentation_id=42,
            prompt=stage.prompt,
            options=stage.options,
        )
    with pytest.raises(InvalidScenarioDefinition):
        BranchingStage(
            stage_index=stage.stage_index,
            presentation_id=stage.presentation_id,
            prompt=42,
            options=stage.options,
        )
    with pytest.raises(InvalidScenarioDefinition):
        BranchingStage(
            stage_index=stage.stage_index,
            presentation_id=stage.presentation_id,
            prompt=stage.prompt,
            options=(stage.options[0], object(), stage.options[2]),
        )
    with pytest.raises(InvalidScenarioDefinition):
        ScenarioDefinition(
            scenario_presentation_id=42,
            title=definition.title,
            starting_state=definition.starting_state,
            initial_liquidity=definition.initial_liquidity,
            cost_budget=definition.cost_budget,
            stages=definition.stages,
        )
    with pytest.raises(InvalidScenarioDefinition):
        ScenarioDefinition(
            scenario_presentation_id=definition.scenario_presentation_id,
            title=definition.title,
            starting_state=definition.starting_state,
            initial_liquidity=definition.initial_liquidity,
            cost_budget=definition.cost_budget,
            stages=(definition.stages[0], object(), definition.stages[2]),
        )

    object.__setattr__(stage, "prompt", 42)
    with pytest.raises(InvalidScenarioDefinition):
        run_scenario(
            definition,
            tuple(current.options[0].option_id for current in definition.stages),
        )
