"""Pure deterministic execution for Phase 2 branching definitions."""

from __future__ import annotations

from itertools import product
from typing import Sequence

from backend.app.branching.model import (
    FinancialState,
    InvalidScenarioDefinition,
    InvalidTransition,
    ScenarioDefinition,
    ScenarioResult,
    TransitionEvidence,
    UnknownBranchOption,
    branching_scenario_score,
    normalize_branching_scenario_score,
    terminal_dimensions,
    validate_transition,
)


def validate_definition(definition: ScenarioDefinition) -> ScenarioDefinition:
    """Re-run structural validation at the execution boundary."""

    if not isinstance(definition, ScenarioDefinition):
        raise InvalidScenarioDefinition("expected a ScenarioDefinition")
    definition.__post_init__()
    return definition


def run_scenario(
    definition: ScenarioDefinition, option_ids: Sequence[str]
) -> ScenarioResult:
    """Execute one complete three-option path without side effects."""

    validate_definition(definition)
    if len(option_ids) != len(definition.stages):
        raise InvalidTransition("a complete scenario path requires three option IDs")
    if any(not isinstance(option_id, str) for option_id in option_ids):
        raise UnknownBranchOption("scenario option IDs must be strings")

    state = definition.starting_state
    timeline: list[TransitionEvidence] = []
    selected_ids: list[str] = []
    for stage, option_id in zip(definition.stages, option_ids, strict=True):
        options = stage.option_map()
        try:
            option = options[option_id]
        except KeyError as exc:
            raise UnknownBranchOption(
                f"unknown option '{option_id}' for stage '{stage.presentation_id}'"
            ) from exc
        before = state
        after = option.apply(before)
        if not isinstance(after, FinancialState):
            raise InvalidTransition("branch option must return a FinancialState")
        delta = validate_transition(before, after)
        timeline.append(
            TransitionEvidence(
                scenario_presentation_id=definition.scenario_presentation_id,
                stage_index=stage.stage_index,
                presentation_id=stage.presentation_id,
                selected_option_id=option.option_id,
                selected_option_label=option.label,
                state_before=before,
                state_delta=delta,
                state_after=after,
            )
        )
        selected_ids.append(option.option_id)
        state = after

    dimensions = terminal_dimensions(
        state,
        initial_liquidity=definition.initial_liquidity,
        cost_budget=definition.cost_budget,
    )
    raw_scenario_score = branching_scenario_score(dimensions)
    return ScenarioResult(
        scenario_presentation_id=definition.scenario_presentation_id,
        option_ids=tuple(selected_ids),
        starting_state=definition.starting_state,
        timeline=tuple(timeline),
        terminal_state=state,
        dimensions=dimensions,
        raw_scenario_score=raw_scenario_score,
        attainable_raw_score_min=definition.attainable_raw_score_min,
        attainable_raw_score_max=definition.attainable_raw_score_max,
        scenario_score=normalize_branching_scenario_score(
            raw_scenario_score,
            definition.attainable_raw_score_min,
            definition.attainable_raw_score_max,
        ),
    )


def enumerate_paths(definition: ScenarioDefinition) -> tuple[tuple[str, ...], ...]:
    """Return all 3 x 3 x 3 complete paths in deterministic order."""

    validate_definition(definition)
    return tuple(
        product(
            *(
                tuple(sorted(option.option_id for option in stage.options))
                for stage in definition.stages
            )
        )
    )


def evaluate_all_paths(
    definition: ScenarioDefinition,
) -> tuple[ScenarioResult, ...]:
    """Execute every complete path for exhaustive Phase 2 verification."""

    return tuple(run_scenario(definition, path) for path in enumerate_paths(definition))


__all__ = [
    "enumerate_paths",
    "evaluate_all_paths",
    "run_scenario",
    "validate_definition",
]
