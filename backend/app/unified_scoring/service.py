"""Pure Phase 3 composition of the canonical instrument and branch engine."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from fractions import Fraction
from typing import Any

from backend.app.branching import (
    ScenarioDefinition,
    ScenarioResult,
    build_branching_scenarios,
    run_scenario,
)
from backend.app.instrument import (
    CanonicalInstrumentForm,
    InvalidResponse,
    OptionPresentation,
    UnknownCanonicalId,
)
from backend.app.instrument.canonical import ObjectiveScore
from backend.app.unified_scoring.models import (
    BehaviorProfileSelection,
    BranchingDimensionsExplanation,
    BranchingPresentation,
    BranchingScenarioExplanation,
    BranchingTimelineExplanation,
    Explanation,
    FinancialStateExplanation,
    FormulaExplanation,
    IssuedValueExplanation,
    ObjectiveExplanation,
    RecommendationExplanation,
    StateDeltaExplanation,
    StaticSjtExplanation,
    UnifiedInstrumentPresentation,
    UnifiedScoreResult,
)


LIMITATIONS: tuple[str, ...] = (
    "This educational score measures demonstrated financial knowledge and judgment, not repayment likelihood or creditworthiness.",
    "Branching scenario scores compare the selected path with the worst and best paths attainable in that same scenario.",
    "Behavior profile and narrative are unscored and do not affect the result.",
    "AlterScore is a portfolio demonstration, not a lending, underwriting, or human-validated psychometric system.",
)

BRANCHING_WEAK_SCORE_THRESHOLD = Fraction(60, 1)

_CONCEPT_EXPLANATIONS: dict[str, str] = {
    "cash_flow": "Cash remaining is opening cash plus inflow minus expenses.",
    "simple_interest": "Simple interest is calculated from principal, rate, and time without compounding.",
    "borrowing_cost_comparison": "Comparing total repayment reveals the cost difference beyond the headline rate.",
    "discount_price": "A discounted sale price is the marked price less the percentage discount.",
    "inflation_price": "Inflation raises the current price by the stated percentage.",
    "due_date_shortfall": "A shortfall is the amount due less the amount already available.",
    "repayment_total": "Total repayment includes principal, interest, and the one-time fee.",
    "emergency_buffer": "An emergency buffer multiplies essential monthly costs by the planned months of coverage.",
}


class UnifiedScoringError(ValueError):
    """Raised when a complete Phase 3 submission cannot be scored."""


def round_fraction_half_up(value: Fraction) -> int:
    """Round a non-negative exact fraction to a whole integer, half up."""

    if not isinstance(value, Fraction) or value < 0:
        raise ValueError("half-up rounding requires a non-negative Fraction")
    quotient, remainder = divmod(value.numerator, value.denominator)
    return quotient + int(2 * remainder >= value.denominator)


def quantize_fraction_half_up(value: Fraction, decimal_places: int = 2) -> Decimal:
    """Quantize a non-negative exact fraction without binary floating point."""

    if not isinstance(value, Fraction) or value < 0:
        raise ValueError("quantization requires a non-negative Fraction")
    if isinstance(decimal_places, bool) or not isinstance(decimal_places, int):
        raise ValueError("decimal_places must be an integer")
    if decimal_places < 0:
        raise ValueError("decimal_places must be non-negative")
    scale = 10**decimal_places
    scaled = round_fraction_half_up(value * scale)
    return Decimal(scaled).scaleb(-decimal_places)


def legacy_demo_score(financial_decision_index: int) -> int:
    """Apply the frozen illustrative 300-to-850 transformation."""

    if (
        isinstance(financial_decision_index, bool)
        or not isinstance(financial_decision_index, int)
        or not 0 <= financial_decision_index <= 100
    ):
        raise ValueError("financial_decision_index must be an integer in 0..100")
    transformed = Fraction(11, 2) * financial_decision_index + Fraction(1, 2)
    return 300 + transformed.numerator // transformed.denominator


def _fraction_string(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _decimal2(value: Fraction) -> Decimal:
    return quantize_fraction_half_up(value, 2)


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise InvalidResponse(f"{field_name} must be an object")
    return value


def _validate_exact_keys(
    mapping: Mapping[str, object], expected: frozenset[str], field_name: str
) -> None:
    actual = frozenset(mapping)
    unknown = actual - expected
    missing = expected - actual
    if unknown:
        unknown_id = sorted(str(value) for value in unknown)[0]
        raise UnknownCanonicalId(
            f"Unknown canonical item ID '{unknown_id}' in {field_name}."
        )
    if missing:
        missing_id = sorted(str(value) for value in missing)[0]
        raise InvalidResponse(
            f"Missing required item ID '{missing_id}' in {field_name}."
        )


def _branching_definitions() -> tuple[ScenarioDefinition, ...]:
    definitions = build_branching_scenarios()
    if len(definitions) != 2:
        raise UnifiedScoringError("the canonical scorer requires two scenarios")
    return definitions


def build_branching_presentations() -> tuple[BranchingPresentation, ...]:
    """Build the six public-safe branch-stage presentations in stable order."""

    presentations: list[BranchingPresentation] = []
    for scenario in _branching_definitions():
        for stage in scenario.stages:
            presentations.append(
                BranchingPresentation(
                    presentation_id=stage.presentation_id,
                    scenario_presentation_id=scenario.scenario_presentation_id,
                    stage_index=stage.stage_index,
                    prompt=stage.prompt,
                    options=[
                        OptionPresentation(**option.presentation())
                        for option in stage.options
                    ],
                )
            )
    return tuple(presentations)


def build_unified_presentation(
    form: CanonicalInstrumentForm,
) -> UnifiedInstrumentPresentation:
    """Combine the Phase 1 instrument with the six Phase 2 stage prompts."""

    if not isinstance(form, CanonicalInstrumentForm):
        raise InvalidResponse("form must be a CanonicalInstrumentForm")
    base = form.to_public_model()
    return UnifiedInstrumentPresentation(
        items=[*base.items, *build_branching_presentations()],
        behavior_profile_items=base.behavior_profile_items,
        narrative=base.narrative,
    )


def _objective_values(item: Any) -> dict[str, int]:
    return {issued.name: issued.value for issued in item.issued_values}


def _number(value: int) -> str:
    return f"{value:,}"


def _worked_calculation(item: Any) -> str:
    values = _objective_values(item)
    answer = item.correct_answer
    concept = item.concept
    if concept == "cash_flow":
        expression = f"{_number(values['opening_cash'])} + {_number(values['inflow'])} - {_number(values['expenses'])}"
    elif concept == "simple_interest":
        expression = f"{_number(values['principal'])} × {values['annual_rate_percent']} × {values['term_years']} ÷ 100"
    elif concept == "borrowing_cost_comparison":
        expression = f"{_number(values['offer_b_total_repayment'])} - {_number(values['offer_a_total_repayment'])}"
    elif concept == "discount_price":
        expression = f"{_number(values['marked_price'])} - {_number(values['discount'])}"
    elif concept == "inflation_price":
        expression = f"{_number(values['current_price'])} × (100 + {values['inflation_rate_percent']}) ÷ 100"
    elif concept == "due_date_shortfall":
        expression = f"{_number(values['due_amount'])} - {_number(values['available_amount'])}"
    elif concept == "repayment_total":
        expression = f"{_number(values['principal'])} + {_number(values['interest'])} + {_number(values['fee'])}"
    elif concept == "emergency_buffer":
        expression = f"{_number(values['monthly_essential_costs'])} × {values['buffer_months']}"
    else:
        raise UnifiedScoringError(f"no worked calculation exists for '{concept}'")
    return f"{expression} = {_number(answer)} INR"


def _objective_explanations(
    form: CanonicalInstrumentForm, responses: Mapping[str, int]
) -> list[ObjectiveExplanation]:
    return [
        ObjectiveExplanation(
            presentation_id=item.presentation_id,
            concept=item.concept,
            issued_values=[
                IssuedValueExplanation(
                    name=issued.name,
                    value=issued.value,
                    unit=issued.unit,
                )
                for issued in item.issued_values
            ],
            submitted_answer=responses[item.presentation_id],
            correct_answer=item.correct_answer,
            is_correct=responses[item.presentation_id] == item.correct_answer,
            worked_calculation=_worked_calculation(item),
            concept_explanation=_CONCEPT_EXPLANATIONS[item.concept],
        )
        for item in form.objective_items
    ]


def _static_explanations(
    form: CanonicalInstrumentForm, responses: Mapping[str, str]
) -> list[StaticSjtExplanation]:
    explanations: list[StaticSjtExplanation] = []
    for item in form.static_sjt_items:
        selected_id = responses[item.presentation_id]
        selected = next(option for option in item.options if option.option_id == selected_id)
        principle = item.principle
        explanations.append(
            StaticSjtExplanation(
                presentation_id=item.presentation_id,
                selected_option_label=selected.label,
                principle=principle,
                protects=f"This decision is assessed against the need to {principle}.",
                risks=(
                    "Check whether the action leaves the stated obligation, "
                    "cost, or timing trade-off unresolved."
                ),
                stronger_principle=f"Stronger principle: {principle[0].upper()}{principle[1:]}",
            )
        )
    return explanations


def _state_explanation(state: Any) -> FinancialStateExplanation:
    return FinancialStateExplanation(**state.as_dict())


def _branching_explanation(
    definition: ScenarioDefinition, result: ScenarioResult
) -> BranchingScenarioExplanation:
    timeline = [
        BranchingTimelineExplanation(
            stage_index=evidence.stage_index,
            presentation_id=evidence.presentation_id,
            selected_option_label=evidence.selected_option_label,
            state_before=_state_explanation(evidence.state_before),
            state_delta=StateDeltaExplanation(**evidence.state_delta.as_dict()),
            state_after=_state_explanation(evidence.state_after),
        )
        for evidence in result.timeline
    ]
    return BranchingScenarioExplanation(
        scenario_presentation_id=definition.scenario_presentation_id,
        starting_state=_state_explanation(definition.starting_state),
        timeline=timeline,
        terminal_state=_state_explanation(result.terminal_state),
        dimensions=BranchingDimensionsExplanation(
            **{
                name: _decimal2(value)
                for name, value in result.dimensions.as_dict().items()
            }
        ),
        score_basis="feasible_range_normalized",
        scenario_score=_decimal2(result.scenario_score),
    )


def _recommendations(
    objective_items: list[ObjectiveExplanation],
    definitions: tuple[ScenarioDefinition, ...],
    branching_results: tuple[ScenarioResult, ...],
) -> list[RecommendationExplanation]:
    recommendations: list[RecommendationExplanation] = []
    for item in objective_items:
        if not item.is_correct:
            recommendations.append(
                RecommendationExplanation(
                    recommendation=(
                        f"Review the {item.concept.replace('_', ' ')} calculation "
                        "and check each quantity before submitting an answer."
                    ),
                    evidence_type="objective",
                    evidence_ids=[item.presentation_id],
                )
            )
    for definition, result in zip(definitions, branching_results, strict=True):
        if result.scenario_score < BRANCHING_WEAK_SCORE_THRESHOLD:
            weakest_dimension = min(
                result.dimensions.as_dict().items(), key=lambda pair: pair[1]
            )[0].replace("_", " ")
            recommendations.append(
                RecommendationExplanation(
                    recommendation=(
                        f"Review the {definition.title.lower()} decisions, "
                        f"especially the terminal {weakest_dimension} dimension."
                    ),
                    evidence_type="branching",
                    evidence_ids=[definition.scenario_presentation_id],
                )
            )
    if not recommendations:
        recommendations.append(
            RecommendationExplanation(
                recommendation=(
                    "Maintain the current approach by checking total costs, "
                    "timing, required payments, and emergency buffers before acting."
                ),
                evidence_type="maintenance",
            )
        )
    return recommendations


def _build_explanation(
    form: CanonicalInstrumentForm,
    objective_result: ObjectiveScore,
    objective_responses: Mapping[str, int],
    static_responses: Mapping[str, str],
    definitions: tuple[ScenarioDefinition, ...],
    branching_results: tuple[ScenarioResult, ...],
    objective_contribution: Fraction,
    judgment_contribution: Fraction,
    judgment_score: Fraction,
    weighted_total: Fraction,
    financial_decision_index: int,
    legacy_score: int,
) -> Explanation:
    objective_items = _objective_explanations(form, objective_responses)
    return Explanation(
        formula=FormulaExplanation(
            objective_score=_decimal2(objective_result.score),
            judgment_score=_decimal2(judgment_score),
            objective_contribution_exact=_fraction_string(objective_contribution),
            judgment_contribution_exact=_fraction_string(judgment_contribution),
            weighted_total_exact=_fraction_string(weighted_total),
            financial_decision_index=financial_decision_index,
            legacy_demo_score=legacy_score,
        ),
        objective_items=objective_items,
        static_sjt_items=_static_explanations(form, static_responses),
        branching_scenarios=[
            _branching_explanation(definition, result)
            for definition, result in zip(definitions, branching_results, strict=True)
        ],
        recommendations=_recommendations(objective_items, definitions, branching_results),
    )


def score_unified_assessment(
    form: CanonicalInstrumentForm,
    responses: Mapping[str, object] | object,
    behavior_profile: Mapping[str, object] | object,
    narrative: str | None = None,
) -> UnifiedScoreResult:
    """Score one complete 18-item submission with no side effects.

    The input contains the eight objective IDs, four static-SJT IDs, and the
    six branching stage presentation IDs. Behavior and narrative are validated
    for shape but never enter any score or recommendation decision.
    """

    if not isinstance(form, CanonicalInstrumentForm):
        raise InvalidResponse("form must be a CanonicalInstrumentForm")
    response_mapping = _require_mapping(responses, "responses")
    definitions = _branching_definitions()
    branch_stage_ids = frozenset(
        stage.presentation_id for definition in definitions for stage in definition.stages
    )
    if len(branch_stage_ids) != 6:
        raise UnifiedScoringError("branching stage presentation IDs must be unique")
    canonical_ids = form.canonical_item_ids()
    if branch_stage_ids & canonical_ids:
        raise UnifiedScoringError(
            "branching stage IDs cannot collide with objective or static IDs"
        )
    expected_ids = canonical_ids | branch_stage_ids
    _validate_exact_keys(response_mapping, expected_ids, "responses")

    canonical_responses = {
        item_id: response_mapping[item_id] for item_id in canonical_ids
    }
    validated_combined, validated_behavior, _ = form.validate_submission(
        canonical_responses,
        behavior_profile,
        narrative,
    )
    objective_ids = frozenset(item.presentation_id for item in form.objective_items)
    static_ids = frozenset(item.presentation_id for item in form.static_sjt_items)
    objective_responses = {
        item_id: validated_combined[item_id] for item_id in objective_ids
    }
    static_responses = {item_id: validated_combined[item_id] for item_id in static_ids}
    if not all(isinstance(value, int) for value in objective_responses.values()):
        raise InvalidResponse("objective responses must be integers")
    if not all(isinstance(value, str) for value in static_responses.values()):
        raise InvalidResponse("static responses must be option IDs")

    branching_results: list[ScenarioResult] = []
    for definition in definitions:
        path: list[str] = []
        for stage in definition.stages:
            option_id = response_mapping[stage.presentation_id]
            if not isinstance(option_id, str):
                raise InvalidResponse(
                    f"Response for '{stage.presentation_id}' must be an option ID."
                )
            path.append(option_id)
        branching_results.append(run_scenario(definition, tuple(path)))

    objective_result = form.score_objective_responses(objective_responses)
    static_scores = tuple(
        form.static_sjt_score(item.presentation_id, static_responses[item.presentation_id])
        for item in form.static_sjt_items
    )
    branching_scores = tuple(result.scenario_score for result in branching_results)
    judgment_components = (*static_scores, *branching_scores)
    judgment_score = sum(judgment_components, Fraction(0, 1)) / len(judgment_components)
    objective_contribution = Fraction(55, 100) * objective_result.score
    judgment_contribution = Fraction(45, 100) * judgment_score
    weighted_total = objective_contribution + judgment_contribution
    financial_decision_index = round_fraction_half_up(weighted_total)
    legacy_score = legacy_demo_score(financial_decision_index)

    behavior_selections = tuple(
        BehaviorProfileSelection(
            presentation_id=item.presentation_id,
            selected_value=next(
                option.label
                for option in item.options
                if option.option_id == validated_behavior[item.presentation_id]
            ),
        )
        for item in form.behavior_profile_items
    )
    explanation = _build_explanation(
        form,
        objective_result,
        objective_responses,
        static_responses,
        definitions,
        tuple(branching_results),
        objective_contribution,
        judgment_contribution,
        judgment_score,
        weighted_total,
        financial_decision_index,
        legacy_score,
    )
    return UnifiedScoreResult(
        objective_score=objective_result.score,
        judgment_score=judgment_score,
        judgment_components=judgment_components,
        financial_decision_index=financial_decision_index,
        legacy_demo_score=legacy_score,
        behavior_profile=behavior_selections,
        limitations=LIMITATIONS,
        explanation=explanation,
        branching_results=tuple(branching_results),
    )


score_assessment = score_unified_assessment


__all__ = [
    "BRANCHING_WEAK_SCORE_THRESHOLD",
    "LIMITATIONS",
    "UnifiedScoringError",
    "build_branching_presentations",
    "build_unified_presentation",
    "legacy_demo_score",
    "quantize_fraction_half_up",
    "round_fraction_half_up",
    "score_assessment",
    "score_unified_assessment",
]
