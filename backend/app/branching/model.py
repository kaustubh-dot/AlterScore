"""Shared Phase 2 branching state and scoring contract.

This module is the integration-owned boundary for both branching simulations.
It contains no network or frontend code. State transitions are immutable,
validated, and replayable so later explanation work can consume the exact
timeline without adding scoring rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Callable, Mapping, TypeAlias


STATE_FIELDS: tuple[str, ...] = (
    "cash_available",
    "required_payments_due",
    "required_payments_met",
    "confirmed_inflows",
    "essential_expenses",
    "emergency_buffer",
    "new_borrowing",
    "borrowing_cost",
    "avoidable_cost",
    "late_payments",
    "unfunded_commitments",
)


class InvalidState(ValueError):
    """Raised when a canonical financial state violates its domain."""


class InvalidTransition(ValueError):
    """Raised when a transition violates cumulative or payment invariants."""


class InvalidScenarioDefinition(ValueError):
    """Raised when a branching definition is structurally invalid."""


class UnknownBranchOption(ValueError):
    """Raised when a path selects an option not issued by its stage."""


@dataclass(frozen=True, slots=True)
class FinancialState:
    """The complete eleven-field canonical state for one scenario horizon."""

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

    def __post_init__(self) -> None:
        for field_name in STATE_FIELDS:
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise InvalidState(f"{field_name} must be a non-negative integer")
            if value < 0:
                raise InvalidState(f"{field_name} must be a non-negative integer")
        if self.required_payments_met > self.required_payments_due:
            raise InvalidState(
                "required_payments_met cannot exceed required_payments_due"
            )

    def replace(self, **changes: int) -> "FinancialState":
        """Return a validated immutable state with selected fields changed."""

        unknown = set(changes) - set(STATE_FIELDS)
        if unknown:
            raise InvalidState(f"Unknown state field(s): {sorted(unknown)}")
        return replace(self, **changes)

    @property
    def unmet_required_payments(self) -> int:
        return self.required_payments_due - self.required_payments_met

    @property
    def liquid_resources(self) -> int:
        return self.cash_available + self.emergency_buffer

    @property
    def unencumbered_liquidity(self) -> int:
        return max(0, self.liquid_resources - self.unmet_required_payments)

    @property
    def remaining_plan_need(self) -> int:
        return (
            self.unmet_required_payments
            + self.essential_expenses
            + self.unfunded_commitments
        )

    def as_dict(self) -> dict[str, int]:
        """Return fields in the frozen canonical order."""

        return {field_name: getattr(self, field_name) for field_name in STATE_FIELDS}


# Short aliases make the shared contract convenient for simulation modules.
State: TypeAlias = FinancialState
CanonicalState: TypeAlias = FinancialState


@dataclass(frozen=True, slots=True)
class StateDelta:
    """Signed field-by-field difference between two canonical states."""

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

    @classmethod
    def from_states(cls, before: FinancialState, after: FinancialState) -> "StateDelta":
        return cls(
            **{
                field_name: getattr(after, field_name) - getattr(before, field_name)
                for field_name in STATE_FIELDS
            }
        )

    def as_dict(self) -> dict[str, int]:
        return {field_name: getattr(self, field_name) for field_name in STATE_FIELDS}


@dataclass(frozen=True, slots=True)
class TerminalDimensions:
    """Exact 0-to-100 terminal dimensions."""

    obligation_coverage: Fraction
    liquidity_retention: Fraction
    cost_efficiency: Fraction
    plan_feasibility: Fraction

    def __post_init__(self) -> None:
        for field_name in (
            "obligation_coverage",
            "liquidity_retention",
            "cost_efficiency",
            "plan_feasibility",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, Fraction) or not 0 <= value <= 100:
                raise InvalidState(f"{field_name} must be a Fraction in 0..100")

    def as_dict(self) -> dict[str, Fraction]:
        return {
            "obligation_coverage": self.obligation_coverage,
            "liquidity_retention": self.liquidity_retention,
            "cost_efficiency": self.cost_efficiency,
            "plan_feasibility": self.plan_feasibility,
        }


@dataclass(frozen=True, slots=True)
class BranchingOption:
    """One pure option transition in a stage."""

    option_id: str
    label: str
    apply: Callable[[FinancialState], FinancialState] = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.option_id, str) or not self.option_id:
            raise InvalidScenarioDefinition("branch option IDs must be non-empty strings")
        if not isinstance(self.label, str) or not self.label:
            raise InvalidScenarioDefinition("branch option labels must be non-empty strings")
        if not callable(self.apply):
            raise InvalidScenarioDefinition("branch option apply must be callable")

    def presentation(self) -> dict[str, str]:
        return {"option_id": self.option_id, "label": self.label}


@dataclass(frozen=True, slots=True)
class BranchingStage:
    """A path-independent stage with exactly three plausible options."""

    stage_index: int
    presentation_id: str
    prompt: str
    options: tuple[BranchingOption, ...]

    def __post_init__(self) -> None:
        if (
            isinstance(self.stage_index, bool)
            or not isinstance(self.stage_index, int)
            or self.stage_index not in {1, 2, 3}
        ):
            raise InvalidScenarioDefinition("stage_index must be 1, 2, or 3")
        if not isinstance(self.presentation_id, str) or not self.presentation_id:
            raise InvalidScenarioDefinition(
                "stage presentation IDs must be non-empty strings"
            )
        if not isinstance(self.prompt, str) or not self.prompt:
            raise InvalidScenarioDefinition("stage prompts must be non-empty strings")
        if not isinstance(self.options, tuple):
            raise InvalidScenarioDefinition("stage options must be an immutable tuple")
        if len(self.options) != 3:
            raise InvalidScenarioDefinition("each branching stage must have three options")
        if any(not isinstance(option, BranchingOption) for option in self.options):
            raise InvalidScenarioDefinition("stage options must be BranchingOption values")
        for option in self.options:
            option.__post_init__()
        option_ids = [option.option_id for option in self.options]
        if len(set(option_ids)) != 3:
            raise InvalidScenarioDefinition("stage option IDs must be unique")
        labels = [option.label for option in self.options]
        if len(set(labels)) != 3:
            raise InvalidScenarioDefinition("stage option labels must be unique")

    def option_map(self) -> Mapping[str, BranchingOption]:
        return {option.option_id: option for option in self.options}

    def presentation(self) -> dict[str, object]:
        return {
            "presentation_id": self.presentation_id,
            "stage_index": self.stage_index,
            "prompt": self.prompt,
            "options": [option.presentation() for option in self.options],
        }


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    """A complete deterministic three-stage branching simulation."""

    scenario_presentation_id: str
    title: str
    starting_state: FinancialState
    initial_liquidity: int
    cost_budget: int
    attainable_raw_score_min: Fraction
    attainable_raw_score_max: Fraction
    stages: tuple[BranchingStage, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.scenario_presentation_id, str)
            or not self.scenario_presentation_id
        ):
            raise InvalidScenarioDefinition("scenario IDs must be non-empty strings")
        if not isinstance(self.title, str) or not self.title:
            raise InvalidScenarioDefinition("scenario titles must be non-empty strings")
        for name, value in (
            ("initial_liquidity", self.initial_liquidity),
            ("cost_budget", self.cost_budget),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise InvalidScenarioDefinition(f"{name} must be a positive integer")
        for name, value in (
            ("attainable_raw_score_min", self.attainable_raw_score_min),
            ("attainable_raw_score_max", self.attainable_raw_score_max),
        ):
            if not isinstance(value, Fraction) or not 0 <= value <= 100:
                raise InvalidScenarioDefinition(
                    f"{name} must be an exact Fraction in 0..100"
                )
        if self.attainable_raw_score_max <= self.attainable_raw_score_min:
            raise InvalidScenarioDefinition(
                "attainable raw score maximum must exceed the minimum"
            )
        if not isinstance(self.stages, tuple):
            raise InvalidScenarioDefinition("scenario stages must be an immutable tuple")
        if len(self.stages) != 3:
            raise InvalidScenarioDefinition("each scenario must have three stages")
        if any(not isinstance(stage, BranchingStage) for stage in self.stages):
            raise InvalidScenarioDefinition("scenario stages must be BranchingStage values")
        for stage in self.stages:
            stage.__post_init__()
        if not isinstance(self.starting_state, FinancialState):
            raise InvalidScenarioDefinition("starting_state must be a FinancialState")
        if tuple(stage.stage_index for stage in self.stages) != (1, 2, 3):
            raise InvalidScenarioDefinition("scenario stages must be ordered 1, 2, 3")
        stage_ids = [stage.presentation_id for stage in self.stages]
        if len(set(stage_ids)) != len(stage_ids):
            raise InvalidScenarioDefinition("stage presentation IDs must be unique")
        option_ids = [
            option.option_id for stage in self.stages for option in stage.options
        ]
        if len(set(option_ids)) != len(option_ids):
            raise InvalidScenarioDefinition("scenario option IDs must be globally unique")


@dataclass(frozen=True, slots=True)
class TransitionEvidence:
    """Structured replay evidence for one selected stage option."""

    scenario_presentation_id: str
    stage_index: int
    presentation_id: str
    selected_option_id: str
    selected_option_label: str
    state_before: FinancialState
    state_delta: StateDelta
    state_after: FinancialState


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    """Deterministic terminal result and full three-stage timeline."""

    scenario_presentation_id: str
    option_ids: tuple[str, ...]
    starting_state: FinancialState
    timeline: tuple[TransitionEvidence, ...]
    terminal_state: FinancialState
    dimensions: TerminalDimensions
    raw_scenario_score: Fraction
    attainable_raw_score_min: Fraction
    attainable_raw_score_max: Fraction
    scenario_score: Fraction

    def __post_init__(self) -> None:
        if len(self.option_ids) != 3 or len(self.timeline) != 3:
            raise InvalidState("scenario results must contain exactly three stages")
        for name in (
            "raw_scenario_score",
            "attainable_raw_score_min",
            "attainable_raw_score_max",
            "scenario_score",
        ):
            value = getattr(self, name)
            if not isinstance(value, Fraction) or not 0 <= value <= 100:
                raise InvalidState(f"{name} must be an exact Fraction in 0..100")
        expected = normalize_branching_scenario_score(
            self.raw_scenario_score,
            self.attainable_raw_score_min,
            self.attainable_raw_score_max,
        )
        if self.scenario_score != expected:
            raise InvalidState(
                "scenario_score must be the exact feasible-range normalization"
            )


def clamp01(value: Fraction | int) -> Fraction:
    """Clamp an exact rational to the closed unit interval."""

    exact = value if isinstance(value, Fraction) else Fraction(value, 1)
    return min(Fraction(1, 1), max(Fraction(0, 1), exact))


def terminal_dimensions(
    state: FinancialState, *, initial_liquidity: int, cost_budget: int
) -> TerminalDimensions:
    """Derive all four dimensions using the frozen exact formulas."""

    if (
        isinstance(initial_liquidity, bool)
        or not isinstance(initial_liquidity, int)
        or initial_liquidity <= 0
    ):
        raise InvalidState("initial_liquidity must be a positive integer")
    if isinstance(cost_budget, bool) or not isinstance(cost_budget, int) or cost_budget <= 0:
        raise InvalidState("cost_budget must be a positive integer")

    if state.required_payments_due == 0:
        obligation_coverage = Fraction(100, 1)
    else:
        obligation_coverage = Fraction(100, 1) * clamp01(
            Fraction(state.required_payments_met, state.required_payments_due)
        )

    liquidity_retention = Fraction(100, 1) * clamp01(
        Fraction(state.unencumbered_liquidity, initial_liquidity)
    )
    cost_efficiency = Fraction(100, 1) * clamp01(
        Fraction(1, 1)
        - Fraction(state.borrowing_cost + state.avoidable_cost, cost_budget)
    )
    if state.remaining_plan_need == 0:
        plan_feasibility = Fraction(100, 1)
    else:
        plan_feasibility = (
            Fraction(100, 1)
            * clamp01(
                Fraction(
                    state.unencumbered_liquidity + state.confirmed_inflows,
                    state.remaining_plan_need,
                )
            )
            / (1 + state.late_payments)
        )
    return TerminalDimensions(
        obligation_coverage=obligation_coverage,
        liquidity_retention=liquidity_retention,
        cost_efficiency=cost_efficiency,
        plan_feasibility=plan_feasibility,
    )


def branching_scenario_score(dimensions: TerminalDimensions) -> Fraction:
    """Calculate the raw terminal score with the fixed dimension weights."""

    return (
        Fraction(40, 100) * dimensions.obligation_coverage
        + Fraction(25, 100) * dimensions.liquidity_retention
        + Fraction(20, 100) * dimensions.cost_efficiency
        + Fraction(15, 100) * dimensions.plan_feasibility
    )


def normalize_branching_scenario_score(
    raw_score: Fraction,
    attainable_min: Fraction,
    attainable_max: Fraction,
) -> Fraction:
    """Map one attainable raw score onto the closed 0-to-100 policy scale."""

    for name, value in (
        ("raw_score", raw_score),
        ("attainable_min", attainable_min),
        ("attainable_max", attainable_max),
    ):
        if not isinstance(value, Fraction) or not 0 <= value <= 100:
            raise InvalidState(f"{name} must be an exact Fraction in 0..100")
    if attainable_max <= attainable_min:
        raise InvalidState("attainable_max must exceed attainable_min")
    if not attainable_min <= raw_score <= attainable_max:
        raise InvalidState("raw_score must be inside the attainable range")
    return Fraction(100, 1) * (
        raw_score - attainable_min
    ) / (attainable_max - attainable_min)


def validate_transition(
    before: FinancialState,
    after: FinancialState,
) -> StateDelta:
    """Validate a cumulative transition and the linked-payment invariant.

    ``required_payments_met`` is cumulative. When a transition pays an
    additional amount, it must leave the obligation unchanged, consume no
    more liquid resources than the amount paid, and must not worsen the other
    financial dimensions named by the frozen conservation rule.
    """

    if not isinstance(before, FinancialState) or not isinstance(after, FinancialState):
        raise InvalidTransition("transition endpoints must be FinancialState values")
    delta = StateDelta.from_states(before, after)
    if delta.required_payments_due < 0:
        raise InvalidTransition("required_payments_due cannot decrease")
    if delta.required_payments_met < 0:
        raise InvalidTransition("required_payments_met cannot decrease")
    for field_name in ("new_borrowing", "borrowing_cost", "avoidable_cost", "late_payments"):
        if getattr(delta, field_name) < 0:
            raise InvalidTransition(f"cumulative field cannot decrease: {field_name}")
    if delta.new_borrowing > 0 and not (
        delta.cash_available > 0
        or delta.borrowing_cost > 0
        or delta.required_payments_met > 0
    ):
        raise InvalidTransition(
            "new borrowing must be reflected in cash, borrowing cost, or payment state"
        )

    if delta.required_payments_met > 0:
        paid = delta.required_payments_met
        if after.required_payments_due != before.required_payments_due:
            raise InvalidTransition(
                "a linked payment transition cannot also change required_payments_due"
            )
        liquid_consumed = before.liquid_resources - after.liquid_resources
        received_inflow = max(0, -delta.confirmed_inflows)
        funded_by_new_borrowing = max(0, delta.new_borrowing)
        retained_borrowed_liquidity = max(0, delta.cash_available) + max(
            0, delta.emergency_buffer
        )
        if delta.new_borrowing > paid + retained_borrowed_liquidity:
            raise InvalidTransition(
                "new borrowing must be fully reflected in linked payment or retained liquidity"
            )
        if liquid_consumed > paid:
            raise InvalidTransition(
                "liquid resources decreased by more than the required payment"
            )
        if liquid_consumed + received_inflow + funded_by_new_borrowing < paid:
            raise InvalidTransition(
                "linked payment is not funded by liquid resources or new funds"
            )
        if after.confirmed_inflows < before.confirmed_inflows:
            raise InvalidTransition("a linked payment cannot reduce confirmed inflows")
        if after.essential_expenses > before.essential_expenses:
            raise InvalidTransition("a linked payment cannot increase essential expenses")
        if after.unfunded_commitments > before.unfunded_commitments:
            raise InvalidTransition(
                "a linked payment cannot increase unfunded commitments"
            )
        if after.borrowing_cost > before.borrowing_cost:
            raise InvalidTransition("a linked payment cannot add borrowing cost")
        if after.avoidable_cost > before.avoidable_cost:
            raise InvalidTransition("a linked payment cannot add avoidable cost")
        if after.late_payments > before.late_payments:
            raise InvalidTransition("a linked payment cannot add a late payment")
    return delta


def pay_from_cash(state: FinancialState, amount: int) -> FinancialState:
    """Pay an exact required amount from available cash."""

    _validate_payment_amount(state, amount, state.cash_available)
    return state.replace(
        cash_available=state.cash_available - amount,
        required_payments_met=state.required_payments_met + amount,
    )


def pay_from_buffer(state: FinancialState, amount: int) -> FinancialState:
    """Pay an exact required amount from the separately tracked buffer."""

    _validate_payment_amount(state, amount, state.emergency_buffer)
    return state.replace(
        emergency_buffer=state.emergency_buffer - amount,
        required_payments_met=state.required_payments_met + amount,
    )


def receive_confirmed_inflow(state: FinancialState, amount: int) -> FinancialState:
    """Move a confirmed but not-yet-received inflow into available cash."""

    _validate_nonnegative_amount(amount, "amount")
    if amount > state.confirmed_inflows:
        raise InvalidTransition("received inflow exceeds confirmed inflows")
    return state.replace(
        cash_available=state.cash_available + amount,
        confirmed_inflows=state.confirmed_inflows - amount,
    )


def borrow_cash(state: FinancialState, amount: int, cost: int) -> FinancialState:
    """Add new borrowing to cash and its exact cost once."""

    _validate_nonnegative_amount(amount, "amount")
    _validate_nonnegative_amount(cost, "cost")
    if amount == 0:
        raise InvalidTransition("new borrowing amount must be positive")
    return state.replace(
        cash_available=state.cash_available + amount,
        new_borrowing=state.new_borrowing + amount,
        borrowing_cost=state.borrowing_cost + cost,
    )


def add_late_payment(state: FinancialState, *, avoidable_cost: int = 0) -> FinancialState:
    """Record one late payment and any separately stated avoidable cost."""

    _validate_nonnegative_amount(avoidable_cost, "avoidable_cost")
    return state.replace(
        late_payments=state.late_payments + 1,
        avoidable_cost=state.avoidable_cost + avoidable_cost,
    )


def _validate_nonnegative_amount(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InvalidTransition(f"{field_name} must be a non-negative integer")


def _validate_payment_amount(
    state: FinancialState, amount: int, available_source: int
) -> None:
    _validate_nonnegative_amount(amount, "amount")
    if amount == 0:
        raise InvalidTransition("payment amount must be positive")
    if amount > state.unmet_required_payments:
        raise InvalidTransition("payment exceeds unpaid required amount")
    if amount > available_source:
        raise InvalidTransition("payment exceeds the selected liquid source")


__all__ = [
    "STATE_FIELDS",
    "BranchingOption",
    "BranchingStage",
    "CanonicalState",
    "FinancialState",
    "InvalidScenarioDefinition",
    "InvalidState",
    "InvalidTransition",
    "ScenarioDefinition",
    "ScenarioResult",
    "State",
    "StateDelta",
    "TerminalDimensions",
    "TransitionEvidence",
    "UnknownBranchOption",
    "add_late_payment",
    "borrow_cash",
    "branching_scenario_score",
    "normalize_branching_scenario_score",
    "clamp01",
    "pay_from_buffer",
    "pay_from_cash",
    "receive_confirmed_inflow",
    "terminal_dimensions",
    "validate_transition",
]
