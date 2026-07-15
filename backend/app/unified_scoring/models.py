"""Frozen Phase 3 presentation and unsigned-result models.

These models describe the deterministic scorer's output without exposing an
HTTP response, signing primitive, attempt token, or legacy model dependency.
Phase 4 will own transport, canonical signing, and digest serialization.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Annotated, Literal, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    field_validator,
    model_validator,
)

from backend.app.branching import ScenarioResult
from backend.app.instrument import (
    BEHAVIOR_VALUES,
    BehaviorProfilePresentation,
    NarrativeConfig,
    ObjectivePresentation,
    OptionPresentation,
    StaticSjtPresentation,
)


class SchemaModel(BaseModel):
    """Local strict base so Phase 3 remains independent of API schemas."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        protected_namespaces=(),
    )


Decimal2: TypeAlias = Annotated[
    Decimal,
    Field(
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        max_digits=5,
        decimal_places=2,
    ),
    PlainSerializer(float, return_type=float, when_used="json"),
]


def canonical_fraction_string(value: str) -> str:
    """Validate and return the canonical representation of a rational value."""

    if not isinstance(value, str) or "/" not in value:
        raise ValueError("fraction values must use numerator/denominator syntax")
    numerator_text, denominator_text = value.split("/", 1)
    if not numerator_text or not denominator_text:
        raise ValueError("fraction values must contain two integers")
    try:
        numerator = int(numerator_text, 10)
        denominator = int(denominator_text, 10)
    except ValueError as exc:
        raise ValueError("fraction values must contain base-10 integers") from exc
    if denominator <= 0:
        raise ValueError("fraction denominators must be positive")
    canonical = Fraction(numerator, denominator)
    if f"{canonical.numerator}/{canonical.denominator}" != value:
        raise ValueError("fraction values must be reduced and canonical")
    return value


def _quantize_fraction_half_up(value: Fraction, decimal_places: int = 2) -> Decimal:
    """Return the exact non-negative fraction rounded half-up for display."""

    scale = 10**decimal_places
    quotient, remainder = divmod(
        value.numerator * scale,
        value.denominator,
    )
    return Decimal(quotient + int(2 * remainder >= value.denominator)).scaleb(
        -decimal_places
    )


def _fraction_from_canonical_string(value: str) -> Fraction:
    """Parse a fraction string after its canonical syntax has been checked."""

    canonical_fraction_string(value)
    numerator_text, denominator_text = value.split("/", 1)
    return Fraction(int(numerator_text, 10), int(denominator_text, 10))


class BranchingPresentation(SchemaModel):
    """Public-safe presentation of one path-independent branching stage."""

    presentation_id: str = Field(..., min_length=1)
    item_type: Literal["branching"] = "branching"
    scenario_presentation_id: str = Field(..., min_length=1)
    stage_index: int = Field(..., ge=1, le=3)
    prompt: str = Field(..., min_length=1)
    response_kind: Literal["single_choice"] = "single_choice"
    required: Literal[True] = True
    options: list[OptionPresentation] = Field(..., min_length=3, max_length=3)


class UnifiedInstrumentPresentation(SchemaModel):
    """The complete scored/unscored Phase 3 instrument presentation."""

    items: list[
        ObjectivePresentation | StaticSjtPresentation | BranchingPresentation
    ] = Field(..., min_length=18, max_length=18)
    behavior_profile_items: list[BehaviorProfilePresentation] = Field(
        ..., min_length=6, max_length=6
    )
    narrative: NarrativeConfig


class IssuedValueExplanation(SchemaModel):
    """One safe numeric value used to work an objective item."""

    name: str = Field(..., min_length=1)
    value: int
    unit: str = Field(..., min_length=1)


class ObjectiveExplanation(SchemaModel):
    """Worked explanation for one generated objective item."""

    presentation_id: str = Field(..., min_length=1)
    concept: str = Field(..., min_length=1)
    issued_values: list[IssuedValueExplanation] = Field(..., min_length=1)
    submitted_answer: int
    correct_answer: int
    is_correct: bool
    worked_calculation: str = Field(..., min_length=1)
    concept_explanation: str = Field(..., min_length=1)


class StaticSjtExplanation(SchemaModel):
    """Principle-level explanation that does not expose the hidden rubric."""

    presentation_id: str = Field(..., min_length=1)
    selected_option_label: str = Field(..., min_length=1)
    principle: str = Field(..., min_length=1)
    protects: str = Field(..., min_length=1)
    risks: str = Field(..., min_length=1)
    stronger_principle: str = Field(..., min_length=1)


class FinancialStateExplanation(SchemaModel):
    """Non-negative canonical state values safe for the consumed result."""

    cash_available: int = Field(..., ge=0)
    required_payments_due: int = Field(..., ge=0)
    required_payments_met: int = Field(..., ge=0)
    confirmed_inflows: int = Field(..., ge=0)
    essential_expenses: int = Field(..., ge=0)
    emergency_buffer: int = Field(..., ge=0)
    new_borrowing: int = Field(..., ge=0)
    borrowing_cost: int = Field(..., ge=0)
    avoidable_cost: int = Field(..., ge=0)
    late_payments: int = Field(..., ge=0)
    unfunded_commitments: int = Field(..., ge=0)

    @model_validator(mode="after")
    def _payment_bound(self) -> "FinancialStateExplanation":
        if self.required_payments_met > self.required_payments_due:
            raise ValueError("required_payments_met cannot exceed required_payments_due")
        return self


class StateDeltaExplanation(SchemaModel):
    """Signed field changes for one branching transition."""

    cash_available: int
    required_payments_due: int
    required_payments_met: int
    confirmed_inflows: int
    essential_expenses: int
    emergency_buffer: int
    new_borrowing: int
    borrowing_cost: int
    avoidable_cost: int
    late_payments: int
    unfunded_commitments: int


class BranchingDimensionsExplanation(SchemaModel):
    """Quantized terminal dimensions; exact score math remains in the scorer."""

    obligation_coverage: Decimal2
    liquidity_retention: Decimal2
    cost_efficiency: Decimal2
    plan_feasibility: Decimal2


class BranchingTimelineExplanation(SchemaModel):
    """One safe replay record without opaque option IDs or hidden rubric data."""

    stage_index: int = Field(..., ge=1, le=3)
    presentation_id: str = Field(..., min_length=1)
    selected_option_label: str = Field(..., min_length=1)
    state_before: FinancialStateExplanation
    state_delta: StateDeltaExplanation
    state_after: FinancialStateExplanation


class BranchingScenarioExplanation(SchemaModel):
    """Complete terminal evidence for one branching simulation."""

    scenario_presentation_id: str = Field(..., min_length=1)
    starting_state: FinancialStateExplanation
    timeline: list[BranchingTimelineExplanation] = Field(
        ..., min_length=3, max_length=3
    )
    terminal_state: FinancialStateExplanation
    dimensions: BranchingDimensionsExplanation
    scenario_score: Decimal2


class FormulaExplanation(SchemaModel):
    """Exact reconciliation fields for the final weighted index."""

    objective_score: Decimal2
    judgment_score: Decimal2
    objective_weight: Literal["0.55"] = "0.55"
    judgment_weight: Literal["0.45"] = "0.45"
    objective_contribution_exact: str = Field(..., min_length=3)
    judgment_contribution_exact: str = Field(..., min_length=3)
    weighted_total_exact: str = Field(..., min_length=3)
    financial_decision_index: int = Field(..., ge=0, le=100)
    legacy_demo_score: int = Field(..., ge=300, le=850)

    _canonical_contribution = field_validator(
        "objective_contribution_exact",
        "judgment_contribution_exact",
        "weighted_total_exact",
    )(canonical_fraction_string)


class RecommendationExplanation(SchemaModel):
    """Deterministic recommendation linked to a real scored weakness."""

    recommendation: str = Field(..., min_length=1)
    evidence_type: Literal["objective", "branching", "maintenance"]
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _evidence_boundary(self) -> "RecommendationExplanation":
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("recommendation evidence IDs must be unique")
        if self.evidence_type == "maintenance" and self.evidence_ids:
            raise ValueError("maintenance recommendations cannot cite weaknesses")
        if self.evidence_type != "maintenance" and not self.evidence_ids:
            raise ValueError("weakness recommendations require evidence IDs")
        return self


class Explanation(SchemaModel):
    """The complete unsigned Phase 3 explanation object."""

    formula: FormulaExplanation
    objective_items: list[ObjectiveExplanation] = Field(
        ..., min_length=8, max_length=8
    )
    static_sjt_items: list[StaticSjtExplanation] = Field(
        ..., min_length=4, max_length=4
    )
    branching_scenarios: list[BranchingScenarioExplanation] = Field(
        ..., min_length=2, max_length=2
    )
    recommendations: list[RecommendationExplanation] = Field(default_factory=list)


class BehaviorProfileSelection(SchemaModel):
    """Unscored selected behavior label returned by the pure scorer."""

    presentation_id: str = Field(..., min_length=1)
    selected_value: str = Field(..., min_length=1)


@dataclass(frozen=True, slots=True)
class UnifiedScoreResult:
    """Exact internal score plus the unsigned, safe explanation."""

    objective_score: Fraction
    judgment_score: Fraction
    judgment_components: tuple[Fraction, ...]
    financial_decision_index: int
    legacy_demo_score: int
    behavior_profile: tuple[BehaviorProfileSelection, ...]
    limitations: tuple[str, ...]
    explanation: Explanation
    branching_results: tuple[ScenarioResult, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.objective_score, Fraction)
            or not 0 <= self.objective_score <= 100
        ):
            raise ValueError("objective_score must be an exact Fraction in 0..100")
        if (
            not isinstance(self.judgment_score, Fraction)
            or not 0 <= self.judgment_score <= 100
        ):
            raise ValueError("judgment_score must be an exact Fraction in 0..100")
        if len(self.judgment_components) != 6 or any(
            not isinstance(component, Fraction) or not 0 <= component <= 100
            for component in self.judgment_components
        ):
            raise ValueError("six exact judgment components are required")
        if (
            isinstance(self.financial_decision_index, bool)
            or not isinstance(self.financial_decision_index, int)
            or not 0 <= self.financial_decision_index <= 100
        ):
            raise ValueError("financial_decision_index must be an integer in 0..100")
        if (
            isinstance(self.legacy_demo_score, bool)
            or not isinstance(self.legacy_demo_score, int)
            or not 300 <= self.legacy_demo_score <= 850
        ):
            raise ValueError("legacy_demo_score must be an integer in 300..850")
        if len(self.behavior_profile) != 6 or len(self.branching_results) != 2:
            raise ValueError("complete behavior and branching results are required")
        if any(
            selection.selected_value not in BEHAVIOR_VALUES
            for selection in self.behavior_profile
        ):
            raise ValueError("behavior selections must use the canonical labels")
        if not self.limitations or len(set(self.limitations)) != len(self.limitations):
            raise ValueError("unique limitations are required")
        expected_judgment = sum(self.judgment_components, Fraction(0, 1)) / 6
        if self.judgment_score != expected_judgment:
            raise ValueError("judgment_score must equal the six-component mean")
        weighted_total = (
            Fraction(55, 100) * self.objective_score
            + Fraction(45, 100) * self.judgment_score
        )
        quotient, remainder = divmod(
            weighted_total.numerator, weighted_total.denominator
        )
        expected_index = quotient + int(2 * remainder >= weighted_total.denominator)
        if self.financial_decision_index != expected_index:
            raise ValueError("financial_decision_index does not reconcile with weights")
        expected_legacy = (
            300
            + (
                Fraction(11, 2) * self.financial_decision_index + Fraction(1, 2)
            ).numerator
            // (
                Fraction(11, 2) * self.financial_decision_index + Fraction(1, 2)
            ).denominator
        )
        if self.legacy_demo_score != expected_legacy:
            raise ValueError("legacy_demo_score does not reconcile with the index")
        if self.explanation.formula.financial_decision_index != self.financial_decision_index:
            raise ValueError("explanation index must reconcile with the result")
        if self.explanation.formula.legacy_demo_score != self.legacy_demo_score:
            raise ValueError("explanation legacy score must reconcile with the result")
        formula = self.explanation.formula
        if formula.objective_score != _quantize_fraction_half_up(self.objective_score):
            raise ValueError("explanation objective_score must reconcile with the result")
        if formula.judgment_score != _quantize_fraction_half_up(self.judgment_score):
            raise ValueError("explanation judgment_score must reconcile with the result")
        expected_objective_contribution = Fraction(55, 100) * self.objective_score
        expected_judgment_contribution = Fraction(45, 100) * self.judgment_score
        if _fraction_from_canonical_string(
            formula.objective_contribution_exact
        ) != expected_objective_contribution:
            raise ValueError(
                "explanation objective contribution must reconcile with the result"
            )
        if _fraction_from_canonical_string(
            formula.judgment_contribution_exact
        ) != expected_judgment_contribution:
            raise ValueError(
                "explanation judgment contribution must reconcile with the result"
            )
        if _fraction_from_canonical_string(
            formula.weighted_total_exact
        ) != expected_objective_contribution + expected_judgment_contribution:
            raise ValueError(
                "explanation weighted total must reconcile with the contributions"
            )


__all__ = [
    "BehaviorProfileSelection",
    "BranchingDimensionsExplanation",
    "BranchingPresentation",
    "BranchingScenarioExplanation",
    "BranchingTimelineExplanation",
    "Decimal2",
    "Explanation",
    "FinancialStateExplanation",
    "FormulaExplanation",
    "IssuedValueExplanation",
    "ObjectiveExplanation",
    "RecommendationExplanation",
    "StateDeltaExplanation",
    "StaticSjtExplanation",
    "UnifiedInstrumentPresentation",
    "UnifiedScoreResult",
    "canonical_fraction_string",
]
