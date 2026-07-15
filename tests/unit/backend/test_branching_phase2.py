"""Integrated Phase 2 exhaustive and adversarial branching checks."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from fractions import Fraction

import pytest

from backend.app.branching import (
    BranchingOption,
    BranchingStage,
    FinancialState,
    InvalidTransition,
    ScenarioDefinition,
    STATE_FIELDS,
    branching_scenario_score,
    build_branching_scenarios,
    enumerate_paths,
    evaluate_all_paths,
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


def _oracle_clamp01(value: Fraction) -> Fraction:
    return min(Fraction(1, 1), max(Fraction(0, 1), value))


def _oracle_dimensions(
    state: FinancialState, *, initial_liquidity: int, cost_budget: int
) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    unmet = state.required_payments_due - state.required_payments_met
    liquid_resources = state.cash_available + state.emergency_buffer
    unencumbered = max(0, liquid_resources - unmet)
    remaining = unmet + state.essential_expenses + state.unfunded_commitments
    obligation = (
        Fraction(100, 1)
        if state.required_payments_due == 0
        else Fraction(100, 1)
        * _oracle_clamp01(
            Fraction(state.required_payments_met, state.required_payments_due)
        )
    )
    liquidity = Fraction(100, 1) * _oracle_clamp01(
        Fraction(unencumbered, initial_liquidity)
    )
    cost = Fraction(100, 1) * _oracle_clamp01(
        Fraction(1, 1)
        - Fraction(state.borrowing_cost + state.avoidable_cost, cost_budget)
    )
    plan = (
        Fraction(100, 1)
        if remaining == 0
        else Fraction(100, 1)
        * _oracle_clamp01(Fraction(unencumbered + state.confirmed_inflows, remaining))
        / (1 + state.late_payments)
    )
    return obligation, liquidity, cost, plan


def _oracle_score(dimensions: tuple[Fraction, Fraction, Fraction, Fraction]) -> Fraction:
    obligation, liquidity, cost, plan = dimensions
    return (
        Fraction(40, 100) * obligation
        + Fraction(25, 100) * liquidity
        + Fraction(20, 100) * cost
        + Fraction(15, 100) * plan
    )


def test_both_simulations_have_exactly_54_reachable_paths() -> None:
    scenarios = build_branching_scenarios()
    assert len(scenarios) == 2
    assert len({scenario.scenario_presentation_id for scenario in scenarios}) == 2
    path_pairs: set[tuple[str, tuple[str, ...]]] = set()

    for scenario in scenarios:
        paths = enumerate_paths(scenario)
        assert len(paths) == 27
        assert len(set(paths)) == 27
        path_pairs.update(
            (scenario.scenario_presentation_id, path) for path in paths
        )
        for stage_index, stage in enumerate(scenario.stages):
            selected = {path[stage_index] for path in paths}
            assert selected == {option.option_id for option in stage.options}
            assert Counter(path[stage_index] for path in paths) == Counter(
                {option.option_id: 9 for option in stage.options}
            )

    assert len(path_pairs) == 54


def test_all_terminal_results_reconcile_exactly_to_terminal_state() -> None:
    for scenario in build_branching_scenarios():
        paths = enumerate_paths(scenario)
        results = evaluate_all_paths(scenario)
        assert len(results) == 27
        assert {result.option_ids for result in results} == set(paths)
        for path, result in zip(paths, results, strict=True):
            oracle_dimensions = _oracle_dimensions(
                result.terminal_state,
                initial_liquidity=scenario.initial_liquidity,
                cost_budget=scenario.cost_budget,
            )
            assert tuple(result.dimensions.as_dict().values()) == oracle_dimensions
            assert result.scenario_score == _oracle_score(oracle_dimensions)
            assert result.option_ids == path
            assert Fraction(0) <= result.scenario_score <= Fraction(100)
            assert all(
                Fraction(0) <= value <= Fraction(100)
                for value in result.dimensions.as_dict().values()
            )
            assert not hasattr(result, "stage_score")

    edge_cases = (
        (
            _state(cash_available=10_000, confirmed_inflows=10_000),
            1,
            1,
        ),
        (
            _state(
                cash_available=0,
                required_payments_due=4,
                required_payments_met=1,
                confirmed_inflows=100,
                essential_expenses=50,
                borrowing_cost=200,
                avoidable_cost=50,
                late_payments=2,
                unfunded_commitments=100,
            ),
            1,
            100,
        ),
    )
    for state, initial_liquidity, cost_budget in edge_cases:
        expected = _oracle_dimensions(
            state,
            initial_liquidity=initial_liquidity,
            cost_budget=cost_budget,
        )
        actual = terminal_dimensions(
            state,
            initial_liquidity=initial_liquidity,
            cost_budget=cost_budget,
        )
        assert tuple(actual.as_dict().values()) == expected
        assert branching_scenario_score(actual) == _oracle_score(expected)


def test_replay_is_deterministic_across_fresh_definitions() -> None:
    first_catalog = build_branching_scenarios()
    second_catalog = build_branching_scenarios()
    for first, second in zip(first_catalog, second_catalog, strict=True):
        assert first == second
        for path in enumerate_paths(first):
            assert run_scenario(first, path) == run_scenario(second, path)


def test_timeline_is_three_stage_replay_evidence_with_exact_deltas() -> None:
    for scenario in build_branching_scenarios():
        for result in evaluate_all_paths(scenario):
            assert len(result.timeline) == 3
            assert result.timeline[0].state_before == result.starting_state
            assert result.timeline[-1].state_after == result.terminal_state
            for index, evidence in enumerate(result.timeline):
                assert evidence.stage_index == index + 1
                assert evidence.state_after.as_dict() == {
                    field_name: getattr(evidence.state_before, field_name)
                    + getattr(evidence.state_delta, field_name)
                    for field_name in STATE_FIELDS
                }
                if index < 2:
                    assert evidence.state_after == result.timeline[index + 1].state_before


def test_linked_payment_dominance_is_strict_in_coverage_and_non_decreasing_elsewhere() -> None:
    before = FinancialState(
        cash_available=200,
        required_payments_due=100,
        required_payments_met=40,
        confirmed_inflows=10,
        essential_expenses=40,
        emergency_buffer=30,
        new_borrowing=0,
        borrowing_cost=0,
        avoidable_cost=0,
        late_payments=0,
        unfunded_commitments=20,
    )
    paid_from_cash = pay_from_cash(before, 20)
    paid_from_buffer = pay_from_buffer(before, 20)
    for after in (paid_from_cash, paid_from_buffer):
        validate_transition(before, after)
        before_dimensions = terminal_dimensions(
            before, initial_liquidity=200, cost_budget=100
        )
        after_dimensions = terminal_dimensions(
            after, initial_liquidity=200, cost_budget=100
        )
        assert after_dimensions.obligation_coverage > before_dimensions.obligation_coverage
        assert after_dimensions.liquidity_retention >= before_dimensions.liquidity_retention
        assert after_dimensions.cost_efficiency >= before_dimensions.cost_efficiency
        assert after_dimensions.plan_feasibility >= before_dimensions.plan_feasibility
        assert branching_scenario_score(after_dimensions) > branching_scenario_score(
            before_dimensions
        )


def test_every_valid_linked_payment_delta_is_monotone() -> None:
    for due in range(1, 9):
        for met in range(due):
            for source in ("cash", "buffer"):
                before = _state(
                    cash_available=12,
                    required_payments_due=due,
                    required_payments_met=met,
                    confirmed_inflows=9,
                    essential_expenses=7,
                    emergency_buffer=12,
                    avoidable_cost=1,
                    unfunded_commitments=5,
                )
                available = before.cash_available if source == "cash" else before.emergency_buffer
                for amount in range(1, min(due - met, available) + 1):
                    after = (
                        pay_from_cash(before, amount)
                        if source == "cash"
                        else pay_from_buffer(before, amount)
                    )
                    validate_transition(before, after)
                    before_dimensions = terminal_dimensions(
                        before, initial_liquidity=24, cost_budget=100
                    )
                    after_dimensions = terminal_dimensions(
                        after, initial_liquidity=24, cost_budget=100
                    )
                    assert after_dimensions.obligation_coverage > (
                        before_dimensions.obligation_coverage
                    )
                    assert all(
                        after_value >= before_value
                        for after_value, before_value in zip(
                            after_dimensions.as_dict().values(),
                            before_dimensions.as_dict().values(),
                            strict=True,
                        )
                    )
                    assert branching_scenario_score(after_dimensions) > (
                        branching_scenario_score(before_dimensions)
                    )


def test_cost_and_unfunded_commitment_increases_cannot_improve_score() -> None:
    base = FinancialState(
        cash_available=100,
        required_payments_due=20,
        required_payments_met=20,
        confirmed_inflows=20,
        essential_expenses=10,
        emergency_buffer=20,
        new_borrowing=0,
        borrowing_cost=10,
        avoidable_cost=5,
        late_payments=0,
        unfunded_commitments=10,
    )
    costlier = base.replace(borrowing_cost=11)
    less_feasible = base.replace(unfunded_commitments=11)
    base_score = branching_scenario_score(
        terminal_dimensions(base, initial_liquidity=100, cost_budget=100)
    )
    assert branching_scenario_score(
        terminal_dimensions(costlier, initial_liquidity=100, cost_budget=100)
    ) < base_score
    assert branching_scenario_score(
        terminal_dimensions(less_feasible, initial_liquidity=100, cost_budget=100)
    ) <= base_score


def test_identical_terminal_states_have_identical_dimensions_and_scores() -> None:
    cash_history = _state(
        cash_available=100,
        required_payments_due=50,
        emergency_buffer=0,
    )
    buffer_history = _state(
        cash_available=50,
        required_payments_due=50,
        emergency_buffer=50,
    )
    cash_terminal = pay_from_cash(cash_history, 50)
    buffer_terminal = pay_from_buffer(buffer_history, 50)
    assert cash_terminal == buffer_terminal

    cash_dimensions = terminal_dimensions(
        cash_terminal, initial_liquidity=100, cost_budget=100
    )
    buffer_dimensions = terminal_dimensions(
        buffer_terminal, initial_liquidity=100, cost_budget=100
    )
    assert cash_dimensions == buffer_dimensions
    assert branching_scenario_score(cash_dimensions) == branching_scenario_score(
        buffer_dimensions
    )


def test_unaccounted_new_borrowing_fails_closed() -> None:
    base = _state(
        cash_available=100,
        required_payments_due=50,
        required_payments_met=25,
        confirmed_inflows=20,
        essential_expenses=10,
        emergency_buffer=30,
        unfunded_commitments=5,
    )
    principal_only = base.replace(new_borrowing=500)
    with pytest.raises(InvalidTransition):
        validate_transition(base, principal_only)


def test_new_borrowing_principal_alone_has_no_hidden_score_bonus() -> None:
    base = _state(
        cash_available=100,
        required_payments_due=50,
        required_payments_met=25,
        confirmed_inflows=20,
        essential_expenses=10,
        emergency_buffer=30,
        unfunded_commitments=5,
    )
    principal_only = base.replace(new_borrowing=500)
    base_dimensions = terminal_dimensions(base, initial_liquidity=100, cost_budget=100)
    principal_dimensions = terminal_dimensions(
        principal_only, initial_liquidity=100, cost_budget=100
    )
    assert principal_dimensions == base_dimensions
    assert branching_scenario_score(principal_dimensions) == branching_scenario_score(
        base_dimensions
    )


def test_option_display_order_does_not_change_path_results() -> None:
    definition = build_branching_scenarios()[0]
    permuted = replace(
        definition,
        stages=tuple(
            replace(stage, options=tuple(reversed(stage.options)))
            for stage in definition.stages
        ),
    )
    assert enumerate_paths(permuted) == enumerate_paths(definition)
    assert evaluate_all_paths(permuted) == evaluate_all_paths(definition)


def _identity(state: FinancialState) -> FinancialState:
    return state


def _pay_all(state: FinancialState) -> FinancialState:
    return pay_from_cash(state, 20)


def _synthetic_stage_shift_definition(action_stage: int) -> ScenarioDefinition:
    stages = []
    for stage_index in (1, 2, 3):
        action = _pay_all if stage_index == action_stage else _identity
        stages.append(
            BranchingStage(
                stage_index=stage_index,
                presentation_id=f"synthetic-stage-{stage_index}",
                prompt=f"Synthetic stage {stage_index}",
                options=(
                    BranchingOption(
                        option_id=f"synthetic-{stage_index}-primary",
                        label=f"Primary {stage_index}",
                        apply=action,
                    ),
                    BranchingOption(
                        option_id=f"synthetic-{stage_index}-secondary",
                        label=f"Secondary {stage_index}",
                        apply=_identity,
                    ),
                    BranchingOption(
                        option_id=f"synthetic-{stage_index}-tertiary",
                        label=f"Tertiary {stage_index}",
                        apply=_identity,
                    ),
                ),
            )
        )
    return ScenarioDefinition(
        scenario_presentation_id=f"synthetic-shift-{action_stage}",
        title="Synthetic stage-shift check",
        starting_state=_state(cash_available=20, required_payments_due=20),
        initial_liquidity=20,
        cost_budget=100,
        stages=tuple(stages),
    )


def test_moving_a_transition_between_stages_does_not_change_terminal_score() -> None:
    first = _synthetic_stage_shift_definition(1)
    second = _synthetic_stage_shift_definition(2)
    first_result = run_scenario(
        first, tuple(stage.options[0].option_id for stage in first.stages)
    )
    second_result = run_scenario(
        second, tuple(stage.options[0].option_id for stage in second.stages)
    )
    assert first_result.terminal_state == second_result.terminal_state
    assert first_result.dimensions == second_result.dimensions
    assert first_result.scenario_score == second_result.scenario_score


def test_invalid_path_length_and_unknown_option_fail_closed() -> None:
    scenario = build_branching_scenarios()[0]
    with pytest.raises(InvalidTransition):
        run_scenario(scenario, (scenario.stages[0].options[0].option_id,))
    with pytest.raises(ValueError):
        run_scenario(
            scenario,
            (
                "unknown_option",
                scenario.stages[1].options[0].option_id,
                scenario.stages[2].options[0].option_id,
            ),
        )
