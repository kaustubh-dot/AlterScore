"""Deterministic EMI, essential-expense, and supplier-opportunity scenario.

The scenario is intentionally a small, self-contained content definition.  An
option only returns a new :class:`FinancialState`; the shared branching engine
validates the resulting transition and derives the terminal dimensions and
score.  No option contains a score or a path-specific adjustment.
"""

from __future__ import annotations

from fractions import Fraction

from backend.app.branching.model import (
    BranchingOption,
    BranchingStage,
    FinancialState,
    InvalidTransition,
    ScenarioDefinition,
    add_late_payment,
    borrow_cash,
    pay_from_buffer,
    pay_from_cash,
)


# All amounts use the scenario's single integer monetary unit and horizon.
_EMI_AMOUNT = 400
_EMI_LATE_COST = 45
_ESSENTIAL_EXPENSES = 450
_DEFERRED_ESSENTIALS = 150
_SUPPLIER_DEPOSIT = 100
_SUPPLIER_CONFIRMED_INFLOW = 500
_SUPPLIER_BORROWING_COST = 25

_INITIAL_LIQUIDITY = 1_900
_COST_BUDGET = 250


def _pay_essential_expenses_from_cash(state: FinancialState) -> FinancialState:
    amount = state.essential_expenses
    if amount > state.cash_available:
        raise InvalidTransition("essential expenses exceed available cash")
    return state.replace(
        cash_available=state.cash_available - amount,
        essential_expenses=0,
    )


def _pay_essential_expenses_from_buffer(state: FinancialState) -> FinancialState:
    amount = state.essential_expenses
    if amount > state.emergency_buffer:
        raise InvalidTransition("essential expenses exceed emergency buffer")
    return state.replace(
        emergency_buffer=state.emergency_buffer - amount,
        essential_expenses=0,
    )


def _defer_essential_expenses(state: FinancialState) -> FinancialState:
    deferred = min(_DEFERRED_ESSENTIALS, state.essential_expenses)
    paid_now = state.essential_expenses - deferred
    if paid_now > state.cash_available:
        raise InvalidTransition(
            "non-deferred essential expenses exceed available operating cash"
        )
    return state.replace(
        cash_available=state.cash_available - paid_now,
        essential_expenses=0,
        unfunded_commitments=state.unfunded_commitments + deferred,
    )


def _accept_supplier_opportunity_with_cash(
    state: FinancialState,
) -> FinancialState:
    if _SUPPLIER_DEPOSIT > state.cash_available:
        raise InvalidTransition("supplier deposit exceeds available cash")
    return state.replace(
        cash_available=state.cash_available - _SUPPLIER_DEPOSIT,
        confirmed_inflows=state.confirmed_inflows + _SUPPLIER_CONFIRMED_INFLOW,
    )


def _decline_supplier_opportunity(state: FinancialState) -> FinancialState:
    return state


def _accept_supplier_opportunity_with_borrowing(
    state: FinancialState,
) -> FinancialState:
    borrowed = borrow_cash(
        state,
        amount=_SUPPLIER_DEPOSIT,
        cost=_SUPPLIER_BORROWING_COST,
    )
    # The borrowed amount is immediately spent on the supplier deposit.  The
    # net cash balance is therefore unchanged while borrowing and its cost
    # remain visible in their canonical fields.
    return borrowed.replace(
        cash_available=borrowed.cash_available - _SUPPLIER_DEPOSIT,
        confirmed_inflows=borrowed.confirmed_inflows + _SUPPLIER_CONFIRMED_INFLOW,
    )


def _pay_emi_from_cash(state: FinancialState) -> FinancialState:
    return pay_from_cash(state, _EMI_AMOUNT)


def _pay_emi_from_buffer(state: FinancialState) -> FinancialState:
    return pay_from_buffer(state, _EMI_AMOUNT)


def _defer_emi(state: FinancialState) -> FinancialState:
    return add_late_payment(state, avoidable_cost=_EMI_LATE_COST)


def build_emi_supplier_scenario() -> ScenarioDefinition:
    """Return a fresh deterministic definition for the first Phase 2 branch."""

    return ScenarioDefinition(
        scenario_presentation_id="branching_emi_supplier_opportunity",
        title="EMI, essential expenses, and a supplier opportunity",
        starting_state=FinancialState(
            cash_available=1_000,
            required_payments_due=_EMI_AMOUNT,
            required_payments_met=0,
            confirmed_inflows=250,
            essential_expenses=_ESSENTIAL_EXPENSES,
            emergency_buffer=900,
            new_borrowing=0,
            borrowing_cost=0,
            avoidable_cost=0,
            late_payments=0,
            unfunded_commitments=200,
        ),
        initial_liquidity=_INITIAL_LIQUIDITY,
        cost_budget=_COST_BUDGET,
        attainable_raw_score_min=Fraction(3393, 95),
        attainable_raw_score_max=Fraction(1725, 19),
        stages=(
            BranchingStage(
                stage_index=1,
                presentation_id="branching_emi_stage",
                prompt=(
                    "You start with 1,000 units of operating cash, a 900-unit "
                    "emergency buffer, a confirmed 250-unit inflow, 450 units "
                    "of essential expenses, and 200 units of other unfunded "
                    "commitments. A 400-unit EMI is due now. Choose how to "
                    "handle it before planning the rest of the horizon."
                ),
                options=(
                    BranchingOption(
                        option_id="emi_pay_from_cash",
                        label="Pay the EMI from operating cash.",
                        apply=_pay_emi_from_cash,
                    ),
                    BranchingOption(
                        option_id="emi_pay_from_buffer",
                        label="Pay the EMI from the emergency buffer.",
                        apply=_pay_emi_from_buffer,
                    ),
                    BranchingOption(
                        option_id="emi_defer_with_late_cost",
                        label="Defer the EMI and accept a late-payment cost.",
                        apply=_defer_emi,
                    ),
                ),
            ),
            BranchingStage(
                stage_index=2,
                presentation_id="branching_essential_expenses_stage",
                prompt=(
                    "Using the state created by your EMI decision, 450 units of "
                    "essential expenses remain. Paying from cash or the buffer "
                    "uses all 450 units; the deferral option pays 300 units from "
                    "operating cash now and carries 150 units forward."
                ),
                options=(
                    BranchingOption(
                        option_id="essentials_pay_from_cash",
                        label="Pay the essential expenses from operating cash.",
                        apply=_pay_essential_expenses_from_cash,
                    ),
                    BranchingOption(
                        option_id="essentials_pay_from_buffer",
                        label="Pay the essential expenses from the emergency buffer.",
                        apply=_pay_essential_expenses_from_buffer,
                    ),
                    BranchingOption(
                        option_id="essentials_defer_to_commitment",
                        label=(
                            "Pay 300 units from operating cash and carry 150 units "
                            "as an unfunded commitment."
                        ),
                        apply=_defer_essential_expenses,
                    ),
                ),
            ),
            BranchingStage(
                stage_index=3,
                presentation_id="branching_supplier_opportunity_stage",
                prompt=(
                    "Using the state created by your first two decisions, a supplier "
                    "opportunity needs a 100-unit deposit and contractually confirms "
                    "a 500-unit inflow next period."
                ),
                options=(
                    BranchingOption(
                        option_id="supplier_accept_with_cash",
                        label="Fund the supplier deposit with available cash.",
                        apply=_accept_supplier_opportunity_with_cash,
                    ),
                    BranchingOption(
                        option_id="supplier_decline",
                        label="Decline the opportunity and preserve liquidity.",
                        apply=_decline_supplier_opportunity,
                    ),
                    BranchingOption(
                        option_id="supplier_accept_with_borrowing",
                        label="Borrow for the deposit and accept the opportunity.",
                        apply=_accept_supplier_opportunity_with_borrowing,
                    ),
                ),
            ),
        ),
    )


def get_emi_supplier_scenario() -> ScenarioDefinition:
    """Compatibility-friendly callable for later scenario integration."""

    return build_emi_supplier_scenario()


__all__ = [
    "build_emi_supplier_scenario",
    "get_emi_supplier_scenario",
]
