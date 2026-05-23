"""Probability-to-score mapping helpers for AlterScore runtime scoring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np


from backend.app.core.constants import RISK_BANDS, SCORE_MIN, SCORE_MAX


def probability_to_score(prob_repay: float) -> int:
    """Map repayment probability to the documented 300-850 score range."""

    probability = float(np.clip(prob_repay, 0.01, 0.99))
    log_odds = np.log(probability / (1.0 - probability))
    score = 560.0 + (log_odds * 85.0)
    return int(np.clip(score, SCORE_MIN, SCORE_MAX))


def get_risk_band(score: int) -> str:
    """Return the documented borrower-facing risk band."""

    for band_key, band_info in RISK_BANDS.items():
        if band_info["min_score"] <= score <= band_info["max_score"]:
            return band_key
    return "poor"


def get_loan_eligibility(score: int) -> dict[str, Any]:
    """Return bounded loan-eligibility guidance aligned with the response schema."""

    risk_band = get_risk_band(score)
    info = RISK_BANDS.get(risk_band, RISK_BANDS["poor"])
    return {
        "band": risk_band,
        "amount_min": info["amount_min"],
        "amount_max": info["amount_max"],
        "description": info["description"],
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

    nested_models = percentile_payload.get("models")
    default_model_name = percentile_payload.get("default_model_name")
    if isinstance(nested_models, Mapping) and isinstance(default_model_name, str):
        nested_payload = nested_models.get(default_model_name)
        if isinstance(nested_payload, Mapping):
            nested_value = _lookup_percentile(score, nested_payload)
            if nested_value is not None:
                return nested_value

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
