"""Backend-owned canonical instrument for the v3 scoring rebuild.

Public presentation models contain only material that may be sent to a
respondent. Generated answer keys, scoring bounds, rubrics, generation
values, and rationales live in private frozen dataclasses and are never
obtained through public serialization.

This pure Python module has no dependency on the legacy feature pipeline,
XGBoost, persisted model artifacts, request state, or FastAPI routes.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import random
from types import MappingProxyType
from typing import Callable, Literal, Mapping, Sequence, TypeAlias

from pydantic import Field

from backend.app.schemas.common import SchemaModel


CONTRACT_VERSION = "2.0"
ASSESSMENT_VERSION = "india-en-3.0.0"
SCORING_POLICY_VERSION = "readiness-rubric-1.1.0"

ObjectiveItemType: TypeAlias = Literal["objective"]
StaticSjtItemType: TypeAlias = Literal["static_sjt"]
BehaviorProfileItemType: TypeAlias = Literal["behavior_profile"]


class OptionPresentation(SchemaModel):
    """A public option; it contains no scoring information."""

    option_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)


class ObjectivePresentation(SchemaModel):
    """The exact public shape of an objective item."""

    presentation_id: str = Field(..., min_length=1)
    item_type: ObjectiveItemType = "objective"
    prompt: str = Field(..., min_length=1)
    response_kind: Literal["integer"] = "integer"
    required: Literal[True] = True


class StaticSjtPresentation(SchemaModel):
    """The exact public shape of a static situational item."""

    presentation_id: str = Field(..., min_length=1)
    item_type: StaticSjtItemType = "static_sjt"
    prompt: str = Field(..., min_length=1)
    response_kind: Literal["single_choice"] = "single_choice"
    required: Literal[True] = True
    options: list[OptionPresentation] = Field(..., min_length=4, max_length=4)


class BehaviorProfilePresentation(SchemaModel):
    """A public, unscored self-reflection item."""

    presentation_id: str = Field(..., min_length=1)
    item_type: BehaviorProfileItemType = "behavior_profile"
    prompt: str = Field(..., min_length=1)
    response_kind: Literal["single_choice"] = "single_choice"
    required: Literal[True] = True
    options: list[OptionPresentation] = Field(..., min_length=6, max_length=6)


class NarrativeConfig(SchemaModel):
    """Optional unscored narrative configuration."""

    enabled: bool
    prompt: str = Field(..., min_length=1)
    max_length: Literal[1000] = 1000


class InstrumentPresentation(SchemaModel):
    """Sanitized Phase 1 instrument presentation.

    Branching items are intentionally absent until Phase 2. This model is not
    an API response; it is the safe serialization boundary used by later
    phases.
    """

    items: list[ObjectivePresentation | StaticSjtPresentation] = Field(
        ..., min_length=12, max_length=12
    )
    behavior_profile_items: list[BehaviorProfilePresentation] = Field(
        ..., min_length=6, max_length=6
    )
    narrative: NarrativeConfig


@dataclass(frozen=True)
class IssuedValue:
    """A server-only value that supports later worked explanations."""

    name: str
    value: int
    unit: str


@dataclass(frozen=True)
class _ObjectiveItem:
    presentation_id: str
    concept: str
    prompt: str
    issued_values: tuple[IssuedValue, ...]
    correct_answer: int
    answer_min: int
    answer_max: int
    generation_rule: str
    rationale: str

    def public_presentation(self) -> ObjectivePresentation:
        return ObjectivePresentation(
            presentation_id=self.presentation_id, prompt=self.prompt
        )


@dataclass(frozen=True)
class _StaticOption:
    option_id: str
    label: str
    rubric_points: int
    rationale: str


@dataclass(frozen=True)
class _StaticSjtItem:
    presentation_id: str
    prompt: str
    options: tuple[_StaticOption, ...]
    principle: str
    rationale: str

    def public_presentation(self) -> StaticSjtPresentation:
        return StaticSjtPresentation(
            presentation_id=self.presentation_id,
            prompt=self.prompt,
            options=[
                OptionPresentation(option_id=option.option_id, label=option.label)
                for option in self.options
            ],
        )

    def rubric_for(self, option_id: str) -> int:
        for option in self.options:
            if option.option_id == option_id:
                return option.rubric_points
        raise UnknownCanonicalId(
            f"Unknown option ID '{option_id}' for item '{self.presentation_id}'."
        )


@dataclass(frozen=True)
class _BehaviorOption:
    option_id: str
    label: str


@dataclass(frozen=True)
class _BehaviorProfileItem:
    presentation_id: str
    prompt: str
    options: tuple[_BehaviorOption, ...]

    def public_presentation(self) -> BehaviorProfilePresentation:
        return BehaviorProfilePresentation(
            presentation_id=self.presentation_id,
            prompt=self.prompt,
            options=[
                OptionPresentation(option_id=option.option_id, label=option.label)
                for option in self.options
            ],
        )


class UnknownCanonicalId(ValueError):
    """Raised when an item or option is not in the issued instrument."""


class InvalidResponse(ValueError):
    """Raised when a response has the wrong type or range."""


@dataclass(frozen=True)
class ObjectiveScore:
    """Exact objective result; the score is never represented as a float."""

    correct_count: int
    total_count: int
    score: Fraction
    is_correct: Mapping[str, bool]


def _validate_seed(seed: int) -> int:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be a non-negative integer")
    if seed < 0:
        raise ValueError("seed must be a non-negative integer")
    return seed


def _rng_for(seed: int, namespace: str) -> random.Random:
    seed = _validate_seed(seed)
    digest = hashlib.sha256(f"{seed}:{namespace}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:16], byteorder="big"))


def _money(value: int) -> str:
    return f"₹{value:,}"


def _value(name: str, value: int, unit: str = "INR") -> IssuedValue:
    return IssuedValue(name=name, value=value, unit=unit)


def _objective(
    *,
    presentation_id: str,
    concept: str,
    prompt: str,
    issued_values: Sequence[IssuedValue],
    correct_answer: int,
    generation_rule: str,
    rationale: str,
) -> _ObjectiveItem:
    if not isinstance(correct_answer, int) or isinstance(correct_answer, bool):
        raise AssertionError("objective answer must be an integer")
    if correct_answer < 0 or correct_answer > 10_000_000:
        raise AssertionError("objective answer outside the safe generation range")
    return _ObjectiveItem(
        presentation_id=presentation_id,
        concept=concept,
        prompt=prompt,
        issued_values=tuple(issued_values),
        correct_answer=correct_answer,
        answer_min=0,
        answer_max=10_000_000,
        generation_rule=generation_rule,
        rationale=rationale,
    )


def _cash_flow(seed: int, presentation_id: str) -> _ObjectiveItem:
    rng = _rng_for(seed, "cash_flow")
    opening = rng.randint(25, 150) * 100
    inflow = rng.randint(5, 100) * 100
    total = opening + inflow
    expenses = rng.randint(3, (total // 100) - 1) * 100
    answer = total - expenses
    return _objective(
        presentation_id=presentation_id,
        concept="cash_flow",
        prompt=(
            f"A household starts the month with {_money(opening)}, receives "
            f"{_money(inflow)}, and spends {_money(expenses)}. How many rupees "
            "remain at month-end?"
        ),
        issued_values=(
            _value("opening_cash", opening),
            _value("inflow", inflow),
            _value("expenses", expenses),
        ),
        correct_answer=answer,
        generation_rule="opening_cash + inflow - expenses",
        rationale="Tests exact month-end cash-flow arithmetic.",
    )


def _simple_interest(seed: int, presentation_id: str) -> _ObjectiveItem:
    rng = _rng_for(seed, "simple_interest")
    principal = rng.randint(50, 500) * 100
    rate = rng.choice((5, 8, 10, 12, 15))
    years = rng.choice((1, 2, 3, 4))
    interest = principal * rate * years // 100
    return _objective(
        presentation_id=presentation_id,
        concept="simple_interest",
        prompt=(
            f"A principal of {_money(principal)} earns simple interest at "
            f"{rate}% per year for {years} year(s). How many rupees of interest "
            "are earned?"
        ),
        issued_values=(
            _value("principal", principal),
            _value("annual_rate_percent", rate, "%"),
            _value("term_years", years, "years"),
        ),
        correct_answer=interest,
        generation_rule="principal * annual_rate_percent * term_years / 100",
        rationale="Tests simple-interest calculation with an exact integer result.",
    )


def _borrowing_cost(seed: int, presentation_id: str) -> _ObjectiveItem:
    rng = _rng_for(seed, "borrowing_cost")
    principal = rng.randint(80, 500) * 100
    term = rng.choice((1, 2, 3))
    rate_a = rng.choice((6, 8, 10))
    rate_b = rate_a + rng.choice((1, 2, 3))
    fee_a = rng.randint(2, 20) * 100
    fee_b = fee_a + rng.randint(2, 20) * 100
    total_a = principal + (principal * rate_a * term // 100) + fee_a
    total_b = principal + (principal * rate_b * term // 100) + fee_b
    difference = total_b - total_a
    if difference <= 0:
        raise AssertionError("borrowing-cost offers must not tie")
    return _objective(
        presentation_id=presentation_id,
        concept="borrowing_cost_comparison",
        prompt=(
            f"For a {_money(principal)} loan over {term} year(s), Offer A charges "
            f"{rate_a}% simple interest and a {_money(fee_a)} fee. Offer B charges "
            f"{rate_b}% simple interest and a {_money(fee_b)} fee. By how many "
            "rupees is Offer B's total repayment higher than Offer A's?"
        ),
        issued_values=(
            _value("principal", principal),
            _value("term_years", term, "years"),
            _value("offer_a_rate_percent", rate_a, "%"),
            _value("offer_a_fee", fee_a),
            _value("offer_b_rate_percent", rate_b, "%"),
            _value("offer_b_fee", fee_b),
            _value("offer_a_total_repayment", total_a),
            _value("offer_b_total_repayment", total_b),
        ),
        correct_answer=difference,
        generation_rule="offer_b_total_repayment - offer_a_total_repayment",
        rationale="Tests comparison of total borrowing cost without a tied result.",
    )


def _discount_price(seed: int, presentation_id: str) -> _ObjectiveItem:
    rng = _rng_for(seed, "discount_price")
    marked_price = rng.randint(50, 800) * 100
    discount_rate = rng.choice((5, 10, 15, 20, 25))
    discount = marked_price * discount_rate // 100
    sale_price = marked_price - discount
    return _objective(
        presentation_id=presentation_id,
        concept="discount_price",
        prompt=(
            f"An item marked at {_money(marked_price)} is offered at a "
            f"{discount_rate}% discount. What is its sale price in rupees?"
        ),
        issued_values=(
            _value("marked_price", marked_price),
            _value("discount_rate_percent", discount_rate, "%"),
            _value("discount", discount),
        ),
        correct_answer=sale_price,
        generation_rule="marked_price - (marked_price * discount_rate_percent / 100)",
        rationale="Tests exact percentage discount arithmetic.",
    )


def _inflation_price(seed: int, presentation_id: str) -> _ObjectiveItem:
    rng = _rng_for(seed, "inflation_price")
    current_price = rng.randint(50, 800) * 100
    inflation_rate = rng.choice((5, 10, 15, 20))
    future_price = current_price * (100 + inflation_rate) // 100
    return _objective(
        presentation_id=presentation_id,
        concept="inflation_price",
        prompt=(
            f"An item costs {_money(current_price)} today. If its price rises by "
            f"{inflation_rate}% over the next year, what will the price be in "
            "rupees?"
        ),
        issued_values=(
            _value("current_price", current_price),
            _value("inflation_rate_percent", inflation_rate, "%"),
        ),
        correct_answer=future_price,
        generation_rule="current_price * (100 + inflation_rate_percent) / 100",
        rationale="Tests purchasing-power arithmetic using an exact integer price.",
    )


def _due_shortfall(seed: int, presentation_id: str) -> _ObjectiveItem:
    rng = _rng_for(seed, "due_shortfall")
    due_amount = rng.randint(50, 500) * 100
    available = rng.randint(1, (due_amount // 100) - 1) * 100
    shortfall = due_amount - available
    return _objective(
        presentation_id=presentation_id,
        concept="due_date_shortfall",
        prompt=(
            f"A payment of {_money(due_amount)} is due. You have {_money(available)} "
            "set aside for it. How many rupees are still needed?"
        ),
        issued_values=(
            _value("due_amount", due_amount),
            _value("available_amount", available),
        ),
        correct_answer=shortfall,
        generation_rule="due_amount - available_amount",
        rationale="Tests exact shortfall calculation without tolerance credit.",
    )


def _repayment_total(seed: int, presentation_id: str) -> _ObjectiveItem:
    rng = _rng_for(seed, "repayment_total")
    principal = rng.randint(100, 600) * 100
    rate = rng.choice((6, 8, 10, 12))
    years = rng.choice((1, 2, 3))
    fee = rng.randint(2, 25) * 100
    interest = principal * rate * years // 100
    total = principal + interest + fee
    return _objective(
        presentation_id=presentation_id,
        concept="repayment_total",
        prompt=(
            f"A {_money(principal)} loan charges {rate}% simple interest per year "
            f"for {years} year(s), plus a one-time fee of {_money(fee)}. What is "
            "the total repayment in rupees?"
        ),
        issued_values=(
            _value("principal", principal),
            _value("annual_rate_percent", rate, "%"),
            _value("term_years", years, "years"),
            _value("fee", fee),
            _value("interest", interest),
        ),
        correct_answer=total,
        generation_rule="principal + interest + fee",
        rationale="Tests total repayment including interest and a fixed fee.",
    )


def _emergency_buffer(seed: int, presentation_id: str) -> _ObjectiveItem:
    rng = _rng_for(seed, "emergency_buffer")
    monthly_essentials = rng.randint(25, 400) * 100
    months = rng.choice((3, 4, 6))
    required_buffer = monthly_essentials * months
    return _objective(
        presentation_id=presentation_id,
        concept="emergency_buffer",
        prompt=(
            f"A household spends {_money(monthly_essentials)} each month on "
            f"essential costs. How many rupees are needed for an emergency buffer "
            f"covering {months} month(s)?"
        ),
        issued_values=(
            _value("monthly_essential_costs", monthly_essentials),
            _value("buffer_months", months, "months"),
        ),
        correct_answer=required_buffer,
        generation_rule="monthly_essential_costs * buffer_months",
        rationale="Tests feasibility of a clearly bounded emergency reserve.",
    )


ObjectiveGenerator: TypeAlias = Callable[[int, str], _ObjectiveItem]

OBJECTIVE_GENERATORS: Mapping[str, ObjectiveGenerator] = MappingProxyType(
    {
        "cash_flow": _cash_flow,
        "simple_interest": _simple_interest,
        "borrowing_cost_comparison": _borrowing_cost,
        "discount_price": _discount_price,
        "inflation_price": _inflation_price,
        "due_date_shortfall": _due_shortfall,
        "repayment_total": _repayment_total,
        "emergency_buffer": _emergency_buffer,
    }
)


def generate_objective_item(
    generator_name: str, seed: int, presentation_id: str | None = None
) -> _ObjectiveItem:
    """Generate one server-side objective item from a named generator."""

    try:
        generator = OBJECTIVE_GENERATORS[generator_name]
    except KeyError as exc:
        raise UnknownCanonicalId(
            f"Unknown objective generator '{generator_name}'."
        ) from exc
    if presentation_id is None:
        presentation_id = generator_name
    return generator(_validate_seed(seed), presentation_id)


def _static_option(
    option_id: str, label: str, rubric_points: int, rationale: str
) -> _StaticOption:
    if rubric_points not in {0, 1, 2, 3}:
        raise AssertionError("static SJT rubric must be an integer from 0 to 3")
    return _StaticOption(option_id, label, rubric_points, rationale)


_STATIC_DEFINITIONS: tuple[tuple[str, str, str, tuple[_StaticOption, ...]], ...] = (
    (
        "static_sjt_01",
        "A customer owes you ₹18,000 and is 14 days late. Rent of ₹12,000 is due in 5 days, and current cash is ₹15,000. What is the strongest first action?",
        "protect an upcoming required expense while resolving an uncertain receivable",
        (
            _static_option(
                "sjt01_a",
                "Reserve the ₹12,000 rent amount before relying on the late receivable.",
                3,
                "Protects a known near-term obligation from an uncertain inflow.",
            ),
            _static_option(
                "sjt01_b",
                "Spend the ₹15,000 because the customer owes more than the rent.",
                0,
                "Treats an uncertain receivable as available cash.",
            ),
            _static_option(
                "sjt01_c",
                "Borrow ₹12,000 immediately without confirming the receivable date.",
                1,
                "Creates a new cost before checking the incoming payment.",
            ),
            _static_option(
                "sjt01_d",
                "Contact the customer today to confirm a collection date, but leave the rent amount unreserved until they reply.",
                2,
                "Reduces receivable uncertainty but leaves the known rent obligation exposed in the meantime.",
            ),
        ),
    ),
    (
        "static_sjt_02",
        "You receive a ₹40,000 windfall. A high-cost debt of ₹18,000 is overdue, monthly essentials are ₹20,000, and you have no emergency buffer. What is the strongest action?",
        "reduce an expensive overdue obligation while preserving a minimum buffer",
        (
            _static_option(
                "sjt02_a",
                "Pay the ₹18,000 overdue debt and keep ₹22,000 for essentials and a buffer.",
                3,
                "Addresses high cost while retaining roughly one month of essentials.",
            ),
            _static_option(
                "sjt02_b",
                "Spend all ₹40,000 on a discretionary purchase.",
                0,
                "Leaves the overdue high-cost debt and no buffer.",
            ),
            _static_option(
                "sjt02_c",
                "Keep all ₹40,000 in cash and make no payment plan.",
                1,
                "Preserves cash but leaves an expensive overdue obligation unresolved.",
            ),
            _static_option(
                "sjt02_d",
                "Pay ₹10,000 now and review the remaining ₹8,000 next month.",
                2,
                "Reduces the debt but leaves a costly overdue balance despite available funds.",
            ),
        ),
    ),
    (
        "static_sjt_03",
        "A product loses ₹5,000 each month and the business has ₹35,000 cash. The fixed cash runway is 7 months if nothing changes. What is the strongest action?",
        "stop a known loss before the fixed runway is exhausted",
        (
            _static_option(
                "sjt03_a",
                "Continue unchanged because ₹35,000 covers seven months.",
                0,
                "Uses up the runway without addressing the loss.",
            ),
            _static_option(
                "sjt03_b",
                "Seek a ₹35,000 loan first, then reconsider the monthly loss after the runway doubles.",
                1,
                "Adds debt and delays correcting the known recurring loss.",
            ),
            _static_option(
                "sjt03_c",
                "Start reducing the ₹5,000 monthly loss now and set an early stop-or-change milestone.",
                3,
                "Acts on the recurring loss while preserving time and cash to adapt.",
            ),
            _static_option(
                "sjt03_d",
                "Pause new spending and review the product in 30 days before choosing a loss-reduction change.",
                2,
                "Protects some runway and creates a near-term decision point, but delays the corrective change.",
            ),
        ),
    ),
    (
        "static_sjt_04",
        "A ₹60,000 loan has a ₹1,500 fee and a ₹5,500 monthly payment for 12 months. Another has a ₹500 fee and a ₹5,800 payment for 12 months; only ₹5,600 monthly cash flow is available. What is the strongest comparison?",
        "compare total cost with the payment timing that cash flow can support",
        (
            _static_option(
                "sjt04_a",
                "Choose the ₹5,800 payment because its fee is ₹1,000 lower.",
                0,
                "Focuses on the fee and exceeds the available monthly cash flow.",
            ),
            _static_option(
                "sjt04_b",
                "Choose the ₹5,500 payment after confirming the ₹67,500 total repayment fits the budget.",
                3,
                "Uses the lower payment and checks the complete cost.",
            ),
            _static_option(
                "sjt04_c",
                "Choose either offer because both payments are close to ₹5,600.",
                1,
                "Treats a shortfall as harmless without checking affordability.",
            ),
            _static_option(
                "sjt04_d",
                "Prefer the ₹5,500 payment because it fits monthly cash flow, but do not compare total repayment.",
                2,
                "Checks payment affordability but leaves the complete borrowing cost untested.",
            ),
        ),
    ),
)


BEHAVIOR_VALUES: tuple[str, ...] = (
    "Never",
    "Rarely",
    "Sometimes",
    "Often",
    "Always",
    "Not applicable",
)

_BEHAVIOR_PROMPTS: tuple[str, ...] = (
    "I compare total repayment before choosing a borrowing option.",
    "I keep some cash available for unexpected essential expenses.",
    "I review due dates before committing to a payment plan.",
    "I check whether a repayment fits a cautious income estimate.",
    "I ask for clarification when a financial term is unclear.",
    "I track essential spending against a plan.",
)

_NARRATIVE = NarrativeConfig(
    enabled=True,
    prompt="If you wish, briefly describe one money decision you want to understand better.",
    max_length=1000,
)


def _build_static_items(seed: int) -> tuple[_StaticSjtItem, ...]:
    items: list[_StaticSjtItem] = []
    for item_id, prompt, principle, options in _STATIC_DEFINITIONS:
        shuffled = list(options)
        _rng_for(seed, f"static-options:{item_id}").shuffle(shuffled)
        items.append(
            _StaticSjtItem(
                presentation_id=item_id,
                prompt=prompt,
                options=tuple(shuffled),
                principle=principle,
                rationale="Select the single action that best balances cost, obligation, and feasibility.",
            )
        )
    return tuple(items)


def _build_behavior_items(seed: int) -> tuple[_BehaviorProfileItem, ...]:
    items: list[_BehaviorProfileItem] = []
    for index, prompt in enumerate(_BEHAVIOR_PROMPTS, start=1):
        options = [
            _BehaviorOption(
                option_id=f"behavior_{label.lower().replace(' ', '_')}",
                label=label,
            )
            for label in BEHAVIOR_VALUES
        ]
        _rng_for(seed, f"behavior-options:{index}").shuffle(options)
        items.append(
            _BehaviorProfileItem(
                presentation_id=f"behavior_{index:02d}",
                prompt=prompt,
                options=tuple(options),
            )
        )
    return tuple(items)


def _build_objective_items(seed: int) -> tuple[_ObjectiveItem, ...]:
    items: list[_ObjectiveItem] = []
    for index, (_, generator) in enumerate(OBJECTIVE_GENERATORS.items(), start=1):
        items.append(generator(seed, f"objective_{index:02d}"))
    return tuple(items)


def _validate_instrument_integrity(
    objective_items: Sequence[_ObjectiveItem],
    static_items: Sequence[_StaticSjtItem],
    behavior_items: Sequence[_BehaviorProfileItem],
    narrative: NarrativeConfig,
) -> None:
    """Fail closed if a canonical definition becomes structurally invalid."""

    if len(objective_items) != 8 or len(static_items) != 4 or len(behavior_items) != 6:
        raise AssertionError("canonical instrument counts are invalid")

    objective_ids = [item.presentation_id for item in objective_items]
    if len(set(objective_ids)) != len(objective_ids):
        raise AssertionError("objective presentation IDs must be unique")
    for item in objective_items:
        if not item.prompt.strip() or not item.issued_values:
            raise AssertionError("objective prompts and issued values are required")
        value_names = [value.name for value in item.issued_values]
        if len(set(value_names)) != len(value_names):
            raise AssertionError("objective issued value names must be unique")
        if (
            item.answer_min > item.correct_answer
            or item.correct_answer > item.answer_max
        ):
            raise AssertionError("objective answer is outside its private bounds")

    static_ids = [item.presentation_id for item in static_items]
    if len(set(static_ids)) != len(static_ids):
        raise AssertionError("static SJT presentation IDs must be unique")
    for item in static_items:
        option_ids = [option.option_id for option in item.options]
        labels = [option.label for option in item.options]
        points = [option.rubric_points for option in item.options]
        if len(option_ids) != 4 or len(set(option_ids)) != 4:
            raise AssertionError("each static SJT must have four unique option IDs")
        if len(set(labels)) != 4 or set(points) != {0, 1, 2, 3}:
            raise AssertionError(
                "each static SJT must have four distinct rubric levels"
            )

    behavior_ids = [item.presentation_id for item in behavior_items]
    if len(set(behavior_ids)) != len(behavior_ids):
        raise AssertionError("behavior presentation IDs must be unique")
    all_presentation_ids = [*objective_ids, *static_ids, *behavior_ids]
    if len(set(all_presentation_ids)) != len(all_presentation_ids):
        raise AssertionError("presentation IDs must be unique across all item types")
    expected_labels = set(BEHAVIOR_VALUES)
    for item in behavior_items:
        labels = [option.label for option in item.options]
        option_ids = [option.option_id for option in item.options]
        if (
            set(labels) != expected_labels
            or len(option_ids) != 6
            or len(set(option_ids)) != 6
        ):
            raise AssertionError(
                "each behavior item must expose the six canonical values"
            )

    if narrative.max_length != 1000 or not narrative.prompt.strip():
        raise AssertionError(
            "narrative configuration must use the public 1000-character limit"
        )


@dataclass(frozen=True)
class CanonicalInstrumentForm:
    """One deterministic server-side form and its scoring authority."""

    seed: int
    objective_items: tuple[_ObjectiveItem, ...]
    static_sjt_items: tuple[_StaticSjtItem, ...]
    behavior_profile_items: tuple[_BehaviorProfileItem, ...]
    narrative: NarrativeConfig

    def to_public_model(self) -> InstrumentPresentation:
        """Return a model containing only public-safe fields."""

        return InstrumentPresentation(
            items=[
                *(item.public_presentation() for item in self.objective_items),
                *(item.public_presentation() for item in self.static_sjt_items),
            ],
            behavior_profile_items=[
                item.public_presentation() for item in self.behavior_profile_items
            ],
            narrative=self.narrative,
        )

    def serialize_public(self) -> dict[str, object]:
        """Serialize without seed, answer keys, bounds, rules, or rubrics."""

        return self.to_public_model().model_dump(mode="json")

    public_payload = serialize_public
    to_public_dict = serialize_public

    def objective_answer_key(self) -> dict[str, int]:
        """Return a defensive server-side copy of the exact objective key."""

        return {
            item.presentation_id: item.correct_answer for item in self.objective_items
        }

    def static_rubric(self) -> dict[str, dict[str, int]]:
        """Return a defensive server-side copy of the static SJT rubric."""

        return {
            item.presentation_id: {
                option.option_id: option.rubric_points for option in item.options
            }
            for item in self.static_sjt_items
        }

    def canonical_item_ids(self) -> frozenset[str]:
        return frozenset(
            item.presentation_id
            for item in (*self.objective_items, *self.static_sjt_items)
        )

    def behavior_item_ids(self) -> frozenset[str]:
        return frozenset(item.presentation_id for item in self.behavior_profile_items)

    def all_item_ids(self) -> frozenset[str]:
        return self.canonical_item_ids() | self.behavior_item_ids()

    def canonical_option_ids(self) -> frozenset[str]:
        return frozenset(
            option.option_id
            for item in self.static_sjt_items
            for option in item.options
        )

    def behavior_option_ids(self) -> frozenset[str]:
        return frozenset(
            option.option_id
            for item in self.behavior_profile_items
            for option in item.options
        )

    def _objective_by_id(self) -> dict[str, _ObjectiveItem]:
        return {item.presentation_id: item for item in self.objective_items}

    def _static_by_id(self) -> dict[str, _StaticSjtItem]:
        return {item.presentation_id: item for item in self.static_sjt_items}

    def _behavior_by_id(self) -> dict[str, _BehaviorProfileItem]:
        return {item.presentation_id: item for item in self.behavior_profile_items}

    @staticmethod
    def _require_mapping(
        value: Mapping[str, object] | object, field_name: str
    ) -> Mapping[str, object]:
        if not isinstance(value, Mapping):
            raise InvalidResponse(f"{field_name} must be an object")
        return value

    def _validate_exact_keys(
        self,
        responses: Mapping[str, object],
        expected: frozenset[str],
        field_name: str,
    ) -> None:
        actual = frozenset(responses)
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

    def validate_objective_responses(
        self, responses: Mapping[str, object] | object
    ) -> dict[str, int]:
        """Validate objective IDs, integer types, and safe bounds."""

        mapping = self._require_mapping(responses, "responses")
        objectives = self._objective_by_id()
        self._validate_exact_keys(mapping, frozenset(objectives), "responses")
        validated: dict[str, int] = {}
        for item_id, raw_value in mapping.items():
            if not isinstance(item_id, str) or item_id not in objectives:
                raise UnknownCanonicalId(f"Unknown canonical item ID '{item_id}'.")
            if isinstance(raw_value, bool) or not isinstance(raw_value, int):
                raise InvalidResponse(f"Response for '{item_id}' must be an integer.")
            item = objectives[item_id]
            if not item.answer_min <= raw_value <= item.answer_max:
                raise InvalidResponse(
                    f"Response for '{item_id}' is outside the allowed integer range."
                )
            validated[item_id] = raw_value
        return validated

    def validate_static_sjt_responses(
        self, responses: Mapping[str, object] | object
    ) -> dict[str, str]:
        """Validate static item IDs and issued option IDs only."""

        mapping = self._require_mapping(responses, "responses")
        static_items = self._static_by_id()
        self._validate_exact_keys(mapping, frozenset(static_items), "responses")
        validated: dict[str, str] = {}
        for item_id, raw_option_id in mapping.items():
            if not isinstance(item_id, str) or item_id not in static_items:
                raise UnknownCanonicalId(f"Unknown canonical item ID '{item_id}'.")
            if not isinstance(raw_option_id, str):
                raise InvalidResponse(f"Response for '{item_id}' must be an option ID.")
            item = static_items[item_id]
            if raw_option_id not in {option.option_id for option in item.options}:
                raise UnknownCanonicalId(
                    f"Unknown option ID '{raw_option_id}' for item '{item_id}'."
                )
            validated[item_id] = raw_option_id
        return validated

    def validate_behavior_profile(
        self, responses: Mapping[str, object] | object
    ) -> dict[str, str]:
        """Validate unscored behavior profile item and option IDs."""

        mapping = self._require_mapping(responses, "behavior_profile")
        behavior_items = self._behavior_by_id()
        self._validate_exact_keys(
            mapping, frozenset(behavior_items), "behavior_profile"
        )
        validated: dict[str, str] = {}
        for item_id, raw_option_id in mapping.items():
            if not isinstance(item_id, str) or item_id not in behavior_items:
                raise UnknownCanonicalId(f"Unknown behavior item ID '{item_id}'.")
            if not isinstance(raw_option_id, str):
                raise InvalidResponse(
                    f"Behavior response for '{item_id}' must be an option ID."
                )
            item = behavior_items[item_id]
            if raw_option_id not in {option.option_id for option in item.options}:
                raise UnknownCanonicalId(
                    f"Unknown behavior option ID '{raw_option_id}' for item '{item_id}'."
                )
            validated[item_id] = raw_option_id
        return validated

    def validate_submission(
        self,
        responses: Mapping[str, object] | object,
        behavior_profile: Mapping[str, object] | object,
        narrative: str | None = None,
    ) -> tuple[dict[str, int | str], dict[str, str], str | None]:
        """Validate a Phase 1 submission without scoring profile or narrative."""

        response_mapping = self._require_mapping(responses, "responses")
        self._validate_exact_keys(
            response_mapping, self.canonical_item_ids(), "responses"
        )
        objective_ids = frozenset(item.presentation_id for item in self.objective_items)
        objective_values = self.validate_objective_responses(
            {
                key: value
                for key, value in response_mapping.items()
                if key in objective_ids
            }
        )
        static_values = self.validate_static_sjt_responses(
            {
                key: value
                for key, value in response_mapping.items()
                if key not in objective_ids
            }
        )
        behavior_values = self.validate_behavior_profile(behavior_profile)
        if narrative is not None:
            if not isinstance(narrative, str):
                raise InvalidResponse("narrative must be a string or null")
            if len(narrative) > self.narrative.max_length:
                raise InvalidResponse("narrative exceeds the maximum length")
        combined: dict[str, int | str] = {**objective_values, **static_values}
        return combined, behavior_values, narrative

    def normalize_static_sjt_responses(
        self, responses: Mapping[str, object] | object
    ) -> dict[str, int]:
        """Map each selected static option to its exact private 0-to-3 rubric."""

        validated = self.validate_static_sjt_responses(responses)
        items = self._static_by_id()
        return {
            item_id: items[item_id].rubric_for(option_id)
            for item_id, option_id in validated.items()
        }

    def static_sjt_score(self, item_id: str, option_id: str) -> Fraction:
        """Return one static item's exact 0-to-100 score."""

        items = self._static_by_id()
        if item_id not in items:
            raise UnknownCanonicalId(f"Unknown canonical item ID '{item_id}'.")
        points = items[item_id].rubric_for(option_id)
        return Fraction(100 * points, 3)

    def score_objective_responses(
        self, responses: Mapping[str, object] | object
    ) -> ObjectiveScore:
        """Score with exact equality; no tolerance or legacy parser is used."""

        validated = self.validate_objective_responses(responses)
        key = self.objective_answer_key()
        is_correct = {item_id: validated[item_id] == key[item_id] for item_id in key}
        correct_count = sum(is_correct.values())
        return ObjectiveScore(
            correct_count=correct_count,
            total_count=len(key),
            score=Fraction(100 * correct_count, len(key)),
            is_correct=MappingProxyType(is_correct),
        )

    def objective_score(self, responses: Mapping[str, object] | object) -> Fraction:
        """Convenience wrapper returning the exact objective score fraction."""

        return self.score_objective_responses(responses).score


def generate_form(seed: int) -> CanonicalInstrumentForm:
    """Build the complete Phase 1 deterministic instrument for ``seed``."""

    seed = _validate_seed(seed)
    objective_items = _build_objective_items(seed)
    static_items = _build_static_items(seed)
    behavior_items = _build_behavior_items(seed)
    _validate_instrument_integrity(
        objective_items, static_items, behavior_items, _NARRATIVE
    )
    return CanonicalInstrumentForm(
        seed=seed,
        objective_items=objective_items,
        static_sjt_items=static_items,
        behavior_profile_items=behavior_items,
        narrative=_NARRATIVE,
    )


def normalize_static_sjt_responses(
    form: CanonicalInstrumentForm, responses: Mapping[str, object] | object
) -> dict[str, int]:
    """Module-level helper for exact static SJT normalization."""

    return form.normalize_static_sjt_responses(responses)


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
