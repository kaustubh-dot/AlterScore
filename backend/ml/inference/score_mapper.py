"""Probability-to-score mapping helpers for AlterScore runtime scoring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np


def probability_to_score(prob_repay: float) -> int:
    """Map repayment probability to the documented 300-850 score range."""

    probability = float(np.clip(prob_repay, 0.01, 0.99))
    log_odds = np.log(probability / (1.0 - probability))
    score = 560.0 + (log_odds * 85.0)
    return int(np.clip(score, 300, 850))


def get_risk_band(score: int) -> str:
    """Return the documented borrower-facing risk band."""

    if score >= 750:
        return "excellent"
    if score >= 650:
        return "good"
    if score >= 550:
        return "fair"
    return "poor"


def get_loan_eligibility(score: int) -> dict[str, Any]:
    """Return a bounded loan-eligibility stub aligned with the response schema."""

    risk_band = get_risk_band(score)
    if risk_band == "excellent":
        return {
            "band": risk_band,
            "amount_min": 30000,
            "amount_max": 75000,
            "description": "Eligible for larger starter microloans subject to lender policy.",
        }
    if risk_band == "good":
        return {
            "band": risk_band,
            "amount_min": 10000,
            "amount_max": 30000,
            "description": "Eligible for a moderate starter loan subject to lender policy.",
        }
    if risk_band == "fair":
        return {
            "band": risk_band,
            "amount_min": 5000,
            "amount_max": 12000,
            "description": "Eligible for a smaller starter loan with moderate risk.",
        }
    return {
        "band": risk_band,
        "amount_min": 0,
        "amount_max": 5000,
        "description": "Limited eligibility; financial coaching is recommended before larger borrowing.",
    }


def compute_percentile(
    score: int,
    percentile_payload: Mapping[str, Any] | None = None,
) -> int:
    """Compute percentile from a saved lookup payload or a safe linear fallback."""

    clipped_score = int(np.clip(score, 300, 850))
    resolved_percentile = _lookup_percentile(clipped_score, percentile_payload)
    if resolved_percentile is not None:
        return int(np.clip(resolved_percentile, 0, 100))

    linear_percentile = round(((clipped_score - 300) / 550.0) * 100.0)
    return int(np.clip(linear_percentile, 0, 100))


def _lookup_percentile(
    score: int,
    percentile_payload: Mapping[str, Any] | None,
) -> int | None:
    if percentile_payload is None:
        return None

    for key in ("score_to_percentile", "percentile_table"):
        nested_mapping = percentile_payload.get(key)
        if isinstance(nested_mapping, Mapping):
            nested_value = _extract_mapping_value(nested_mapping, score)
            if nested_value is not None:
                return nested_value

    direct_value = _extract_mapping_value(percentile_payload, score)
    if direct_value is not None:
        return direct_value

    scores = percentile_payload.get("scores")
    percentiles = percentile_payload.get("percentiles")
    if _is_numeric_sequence(scores) and _is_numeric_sequence(percentiles):
        if len(scores) == len(percentiles) and len(scores) > 1:
            return int(
                np.interp(
                    score,
                    np.asarray(scores, dtype=float),
                    np.asarray(percentiles, dtype=float),
                )
            )

    return None


def _extract_mapping_value(
    values: Mapping[str, Any] | Mapping[int, Any],
    score: int,
) -> int | None:
    for candidate_key in (score, str(score)):
        if candidate_key not in values:
            continue
        try:
            return int(values[candidate_key])
        except (TypeError, ValueError):
            return None
    return None


def _is_numeric_sequence(values: Any) -> bool:
    return isinstance(values, Sequence) and not isinstance(values, (str, bytes))


__all__ = [
    "compute_percentile",
    "get_loan_eligibility",
    "get_risk_band",
    "probability_to_score",
]
