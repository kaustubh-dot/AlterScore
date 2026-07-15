"""Deterministic forecast-shortfall and counterparty-negotiation scenario.

The scenario is deliberately expressed only in terms of the shared Phase 2
state and transition helpers.  Each option is a pure function of the state it
receives, so the engine can replay any complete path without hidden state or a
hand-authored terminal score.
"""

from __future__ import annotations

from backend.app.branching.model import (
    BranchingOption,
    BranchingStage,
    FinancialState,
    ScenarioDefinition,
    add_late_payment,
    borrow_cash,
    pay_from_buffer,
    pay_from_cash,
    receive_confirmed_inflow,
)


SCENARIO_PRESENTATION_ID = "forecast_shortfall_counterparty_negotiation"
SCENARIO_TITLE = "Forecast payment shortfall and negotiate with the counterparty"

_ROUTINE_COLLECTION = 6_000
_RECONCILED_COLLECTION = 12_000
_ACCELERATED_COLLECTION = 18_000
_EARLY_SETTLEMENT_CONCESSION = 1_000
_OPERATING_CASH_PAYMENT = 10_000
_BUFFER_PAYMENT = 8_000
_BRIDGE_BORROWING = 12_000
_BRIDGE_BORROWING_COST = 1_800
_GOOD_FAITH_PAYMENT = 6_000
_EXTENSION_COST = 500

_STARTING_CASH = 12_000
_REQUIRED_PAYMENT = 30_000
_CONFIRMED_COUNTERPARTY_INFLOW = 24_000
_ESSENTIAL_EXPENSES = 9_000
_EMERGENCY_BUFFER = 9_000
_UNFUNDED_COMMITMENTS = 6_000
_INITIAL_LIQUIDITY = 21_000
_COST_BUDGET = 6_000


def _collect_routine_amount(state: FinancialState) -> FinancialState:
    """Collect the amount secured through routine follow-up."""

    return receive_confirmed_inflow(state, _ROUTINE_COLLECTION)


def _collect_reconciled_amount(state: FinancialState) -> FinancialState:
    """Collect the amount secured by reconciling the counterparty account."""

    return receive_confirmed_inflow(state, _RECONCILED_COLLECTION)


def _collect_accelerated_amount(state: FinancialState) -> FinancialState:
    """Secure earlier collection while recording the concession paid for it."""

    collected = receive_confirmed_inflow(state, _ACCELERATED_COLLECTION)
    return collected.replace(
        avoidable_cost=collected.avoidable_cost + _EARLY_SETTLEMENT_CONCESSION
    )


def _pay_from_operating_cash(state: FinancialState) -> FinancialState:
    """Meet part of the obligation from cash already on hand."""

    return pay_from_cash(state, _OPERATING_CASH_PAYMENT)


def _pay_from_emergency_buffer(state: FinancialState) -> FinancialState:
    """Meet part of the obligation while drawing down the emergency buffer."""

    return pay_from_buffer(state, _BUFFER_PAYMENT)


def _borrow_bridge_amount(state: FinancialState) -> FinancialState:
    """Add a priced bridge facility without pretending it is a payment."""

    return borrow_cash(
        state,
        _BRIDGE_BORROWING,
        cost=_BRIDGE_BORROWING_COST,
    )


def _apply_all_available_cash(state: FinancialState) -> FinancialState:
    """Apply all available operating cash to the remaining required payment."""

    return pay_from_cash(
        state,
        min(state.cash_available, state.unmet_required_payments),
    )


def _make_good_faith_payment(state: FinancialState) -> FinancialState:
    """Make a smaller immediate payment while retaining operating liquidity."""

    return pay_from_cash(
        state,
        min(
            _GOOD_FAITH_PAYMENT,
            state.cash_available,
            state.unmet_required_payments,
        ),
    )


def _extend_due_date(state: FinancialState) -> FinancialState:
    """Record the cost of accepting a seven-day counterparty extension."""

    return add_late_payment(state, avoidable_cost=_EXTENSION_COST)


def build_forecast_shortfall_negotiation_scenario() -> ScenarioDefinition:
    """Build the deterministic three-stage counterparty scenario.

    The opening state contains ₹12,000 of cash, a ₹9,000 emergency buffer,
    and a confirmed but not-yet-received ₹24,000 counterparty inflow against
    ₹30,000 of required payments. Stage one records the cash actually
    secured through one of three collection actions, not a self-reported
    forecast. Stage two chooses a funding response, and stage three chooses
    a payment arrangement or extension with the counterparty.
    """

    starting_state = FinancialState(
        cash_available=_STARTING_CASH,
        required_payments_due=_REQUIRED_PAYMENT,
        required_payments_met=0,
        confirmed_inflows=_CONFIRMED_COUNTERPARTY_INFLOW,
        essential_expenses=_ESSENTIAL_EXPENSES,
        emergency_buffer=_EMERGENCY_BUFFER,
        new_borrowing=0,
        borrowing_cost=0,
        avoidable_cost=0,
        late_payments=0,
        unfunded_commitments=_UNFUNDED_COMMITMENTS,
    )

    return ScenarioDefinition(
        scenario_presentation_id=SCENARIO_PRESENTATION_ID,
        title=SCENARIO_TITLE,
        starting_state=starting_state,
        initial_liquidity=_INITIAL_LIQUIDITY,
        cost_budget=_COST_BUDGET,
        stages=(
            BranchingStage(
                stage_index=1,
                presentation_id="payment_forecast",
                prompt=(
                    "The counterparty owes ₹24,000. Before the ₹30,000 "
                    "obligation is due, which collection action do you take to "
                    "secure cash?"
                ),
                options=(
                    BranchingOption(
                        option_id="collect_routine_amount",
                        label=(
                            "Use routine follow-up and collect ₹6,000 now."
                        ),
                        apply=_collect_routine_amount,
                    ),
                    BranchingOption(
                        option_id="collect_reconciled_amount",
                        label=(
                            "Reconcile the account and collect ₹12,000 now."
                        ),
                        apply=_collect_reconciled_amount,
                    ),
                    BranchingOption(
                        option_id="collect_accelerated_amount",
                        label=(
                            "Offer a ₹1,000 early-settlement concession to "
                            "collect ₹18,000 now."
                        ),
                        apply=_collect_accelerated_amount,
                    ),
                ),
            ),
            BranchingStage(
                stage_index=2,
                presentation_id="shortfall_response",
                prompt=(
                    "Before the obligation date, how do you cover the "
                    "forecast shortfall while protecting essential expenses?"
                ),
                options=(
                    BranchingOption(
                        option_id="pay_from_cash",
                        label="Pay ₹10,000 from operating cash",
                        apply=_pay_from_operating_cash,
                    ),
                    BranchingOption(
                        option_id="pay_from_buffer",
                        label="Pay ₹8,000 from the emergency buffer",
                        apply=_pay_from_emergency_buffer,
                    ),
                    BranchingOption(
                        option_id="borrow_bridge",
                        label=(
                            "Borrow ₹12,000 through a bridge facility costing "
                            "₹1,800"
                        ),
                        apply=_borrow_bridge_amount,
                    ),
                ),
            ),
            BranchingStage(
                stage_index=3,
                presentation_id="counterparty_negotiation",
                prompt=(
                    "At the due date, which payment arrangement do you put to "
                    "the counterparty?"
                ),
                options=(
                    BranchingOption(
                        option_id="apply_all_available_cash",
                        label=(
                            "Apply all available operating cash to the remaining "
                            "required payment."
                        ),
                        apply=_apply_all_available_cash,
                    ),
                    BranchingOption(
                        option_id="make_good_faith_payment",
                        label=(
                            "Make a ₹6,000 good-faith payment and retain the "
                            "remaining operating cash."
                        ),
                        apply=_make_good_faith_payment,
                    ),
                    BranchingOption(
                        option_id="extend_due_date",
                        label=(
                            "Grant a seven-day extension and record one late "
                            "payment with a ₹500 follow-up cost"
                        ),
                        apply=_extend_due_date,
                    ),
                ),
            ),
        ),
    )


__all__ = [
    "SCENARIO_PRESENTATION_ID",
    "SCENARIO_TITLE",
    "build_forecast_shortfall_negotiation_scenario",
]
