"""Centralized governance and platform constants for AlterScore."""

import math
from typing import Any, Final

SCORE_MIN: Final[int] = 300
SCORE_MAX: Final[int] = 850

# --- Score-mapping policy (single source of truth) -------------------------
# The borrower-facing credit score is a log-odds ("scaled score") transform of
# the model's calibrated repayment probability ``p``:
#
#     score = SCORE_BASE + SCORE_LOG_ODDS_FACTOR * ln(p / (1 - p))
#
# SCORE_BASE and SCORE_LOG_ODDS_FACTOR must NEVER be hand-edited: nudging them
# silently shifts the entire population (this is exactly how the score range
# previously collapsed into the "poor" band). Instead we fix two interpretable,
# industry-standard knobs and DERIVE the slope/intercept from them:
#
#   * SCORE_PDO  — "points to double the odds": how many score points equal a
#     2x change in the odds of repayment. This sets the spread of the scale.
#   * SCORE_ANCHOR_SCORE / SCORE_ANCHOR_ODDS — one calibration anchor: at
#     SCORE_ANCHOR_SCORE the modelled repayment odds are SCORE_ANCHOR_ODDS : 1.
#     This pins where the scale sits.
#
# This is the standard FICO/VantageScore scaling formulation. Changing PDO or
# the anchor has an obvious documented meaning; the derived constants do not.
# A score-distribution promotion gate (see promotion_gates.py) independently
# verifies that whatever mapping ships actually exercises the full 300-850
# range, so a bad override cannot reach production unnoticed.
SCORE_PDO: Final[float] = 44.0
SCORE_ANCHOR_SCORE: Final[float] = 640.0
SCORE_ANCHOR_ODDS: Final[float] = 2.0

SCORE_LOG_ODDS_FACTOR: Final[float] = SCORE_PDO / math.log(2.0)
SCORE_BASE: Final[float] = SCORE_ANCHOR_SCORE - SCORE_LOG_ODDS_FACTOR * math.log(
    SCORE_ANCHOR_ODDS
)

MAX_EXPLANATION_ITEMS: Final[int] = 6

TIP_LIBRARY: Final[dict[str, tuple[str, str]]] = {
    "numeracy_score": (
        "Strengthen financial math",
        "Practice interest, discount, and savings calculations before another assessment.",
    ),
    "financial_literacy_score": (
        "Review money basics",
        "Refreshing savings, borrowing, and inflation concepts can improve future applications.",
    ),
    "future_orientation": (
        "Show long-term planning",
        "Consistent future-oriented choices usually support stronger assessment signals.",
    ),
    "conscientiousness_score": (
        "Build planning habits",
        "Small routines around planning and follow-through can strengthen the demonstrated assessment evidence.",
    ),
    "social_capital_score": (
        "Highlight support systems",
        "Consider how community or family support shapes the choices you make in future scenarios.",
    ),
    "locus_of_control": (
        "Practice proactive problem solving",
        "Describe concrete actions you would take when a financial plan needs to change.",
    ),
    "resilience_score": (
        "Plan for setbacks",
        "Practice identifying a practical next step when circumstances become difficult.",
    ),
}

__all__ = [
    "MAX_EXPLANATION_ITEMS",
    "SCORE_ANCHOR_ODDS",
    "SCORE_ANCHOR_SCORE",
    "SCORE_BASE",
    "SCORE_LOG_ODDS_FACTOR",
    "SCORE_MAX",
    "SCORE_MIN",
    "SCORE_PDO",
    "TIP_LIBRARY",
]
