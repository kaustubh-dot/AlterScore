"""Canonical v3 assessment instrument.

This package is deliberately independent from the legacy v1 API and model
artifacts. Phase 1 owns canonical questions, deterministic generation, and
server-side normalization only; API transport and branching simulation are
introduced in later phases.
"""

from backend.app.instrument.canonical import (
    ASSESSMENT_VERSION,
    CONTRACT_VERSION,
    SCORING_POLICY_VERSION,
    BEHAVIOR_VALUES,
    OBJECTIVE_GENERATORS,
    BehaviorProfilePresentation,
    CanonicalInstrumentForm,
    InstrumentPresentation,
    InvalidResponse,
    NarrativeConfig,
    ObjectivePresentation,
    ObjectiveScore,
    OptionPresentation,
    StaticSjtPresentation,
    UnknownCanonicalId,
    generate_form,
    generate_objective_item,
    normalize_static_sjt_responses,
)

__all__ = [
    "ASSESSMENT_VERSION",
    "CONTRACT_VERSION",
    "SCORING_POLICY_VERSION",
    "BEHAVIOR_VALUES",
    "OBJECTIVE_GENERATORS",
    "BehaviorProfilePresentation",
    "CanonicalInstrumentForm",
    "InstrumentPresentation",
    "InvalidResponse",
    "NarrativeConfig",
    "ObjectivePresentation",
    "ObjectiveScore",
    "OptionPresentation",
    "StaticSjtPresentation",
    "UnknownCanonicalId",
    "generate_form",
    "generate_objective_item",
    "normalize_static_sjt_responses",
]
