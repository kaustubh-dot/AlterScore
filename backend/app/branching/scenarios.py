"""Canonical Phase 2 branching-simulation catalog."""

from __future__ import annotations

from backend.app.branching.emi import build_emi_supplier_scenario
from backend.app.branching.model import InvalidScenarioDefinition, ScenarioDefinition
from backend.app.branching.negotiation import (
    build_forecast_shortfall_negotiation_scenario,
)


def build_branching_scenarios() -> tuple[ScenarioDefinition, ScenarioDefinition]:
    """Return the two frozen three-stage simulations in canonical order."""

    scenarios = (
        build_emi_supplier_scenario(),
        build_forecast_shortfall_negotiation_scenario(),
    )
    scenario_ids = [scenario.scenario_presentation_id for scenario in scenarios]
    if len(set(scenario_ids)) != len(scenario_ids):
        raise InvalidScenarioDefinition("branching scenario IDs must be unique")
    return scenarios


__all__ = ["build_branching_scenarios"]
