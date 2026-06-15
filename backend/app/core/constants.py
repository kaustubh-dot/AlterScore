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
SCORE_PDO: Final[float] = 45.0
SCORE_ANCHOR_SCORE: Final[float] = 640.0
SCORE_ANCHOR_ODDS: Final[float] = 2.0

SCORE_LOG_ODDS_FACTOR: Final[float] = SCORE_PDO / math.log(2.0)
SCORE_BASE: Final[float] = SCORE_ANCHOR_SCORE - SCORE_LOG_ODDS_FACTOR * math.log(
    SCORE_ANCHOR_ODDS
)

RISK_BANDS: Final[dict[str, dict[str, Any]]] = {
    "excellent": {
        "label": "Excellent",
        "min_score": 750,
        "max_score": 850,
        "amount_min": 30000,
        "amount_max": 75000,
        "description": "Eligible for larger starter microloans subject to lender policy.",
    },
    "good": {
        "label": "Good",
        "min_score": 650,
        "max_score": 749,
        "amount_min": 10000,
        "amount_max": 30000,
        "description": "Eligible for a moderate starter loan subject to lender policy.",
    },
    "fair": {
        "label": "Fair",
        "min_score": 550,
        "max_score": 649,
        "amount_min": 5000,
        "amount_max": 12000,
        "description": "Eligible for a smaller starter loan with moderate risk.",
    },
    "poor": {
        "label": "Poor",
        "min_score": 300,
        "max_score": 549,
        "amount_min": 0,
        "amount_max": 5000,
        "description": "Limited eligibility; financial coaching is recommended before larger borrowing.",
    },
}

MAX_EXPLANATION_ITEMS: Final[int] = 6

TIP_LIBRARY: Final[dict[str, tuple[str, str]]] = {
    "numeracy_score": (
        "Strengthen financial math",
        "Practice interest, discount, and savings calculations before applying again.",
    ),
    "financial_literacy_score": (
        "Review money basics",
        "Refreshing savings, borrowing, and inflation concepts can improve future applications.",
    ),
    "future_orientation": (
        "Show long-term planning",
        "Consistent future-oriented choices usually support stronger repayment signals.",
    ),
    "conscientiousness_score": (
        "Build repayment habits",
        "Small routines around planning and follow-through can improve creditworthiness signals.",
    ),
    "social_capital_score": (
        "Highlight support systems",
        "Documenting community or family repayment support can strengthen future applications.",
    ),
    "text_agency_score": (
        "Use action-oriented explanations",
        "Describe concrete steps you take to manage setbacks and repayment plans.",
    ),
}

__all__ = [
    "MAX_EXPLANATION_ITEMS",
    "RISK_BANDS",
    "SCORE_ANCHOR_ODDS",
    "SCORE_ANCHOR_SCORE",
    "SCORE_BASE",
    "SCORE_LOG_ODDS_FACTOR",
    "SCORE_MAX",
    "SCORE_MIN",
    "SCORE_PDO",
    "TIP_LIBRARY",
]
