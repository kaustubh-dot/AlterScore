"""Centralized governance and platform constants for AlterScore."""

from typing import Any, Final

SCORE_MIN: Final[int] = 300
SCORE_MAX: Final[int] = 850

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
    "SCORE_MAX",
    "SCORE_MIN",
    "TIP_LIBRARY",
]
