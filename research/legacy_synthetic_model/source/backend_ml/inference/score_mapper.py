"""Probability-to-score mapping helpers for AlterScore runtime scoring."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


from backend.app.core.constants import (
    SCORE_BASE,
    SCORE_LOG_ODDS_FACTOR,
    SCORE_MAX,
    SCORE_MIN,
)

SCORE_MAPPING_METHOD_LOG_ODDS = "log_odds"


@dataclass(frozen=True)
class ScoreMappingConfig:
    method: str = SCORE_MAPPING_METHOD_LOG_ODDS
    score_base: float = SCORE_BASE
    log_odds_factor: float = SCORE_LOG_ODDS_FACTOR
    probability_clip_min: float = 0.01
    probability_clip_max: float = 0.99
    score_min: int = SCORE_MIN
    score_max: int = SCORE_MAX
    calibration: str = "none"


DEFAULT_SCORE_MAPPING_CONFIG = ScoreMappingConfig()


def probability_to_score(
    prob_repay: float,
    mapping_config: Mapping[str, Any] | ScoreMappingConfig | None = None,
) -> int:
    """Map repayment probability to the documented 300-850 score range."""

    return int(score_mapping_debug(prob_repay, mapping_config)["final_credit_score"])


def score_mapping_debug(
    prob_repay: float,
    mapping_config: Mapping[str, Any] | ScoreMappingConfig | None = None,
) -> dict[str, Any]:
    """Return score-mapping internals for debug traces and tests."""

    config = resolve_score_mapping_config(mapping_config)
    if config.method != SCORE_MAPPING_METHOD_LOG_ODDS:
        raise ValueError(f"Unsupported score mapping method: {config.method}.")

    probability = float(
        np.clip(
            prob_repay,
            config.probability_clip_min,
            config.probability_clip_max,
        )
    )
    log_odds = float(np.log(probability / (1.0 - probability)))
    raw_score = config.score_base + (log_odds * config.log_odds_factor)
    final_credit_score = int(np.clip(raw_score, config.score_min, config.score_max))
    return {
        "method": config.method,
        "calibration": config.calibration,
        "raw_repayment_probability": float(prob_repay),
        "clipped_probability_for_score_mapping": probability,
        "log_odds": log_odds,
        "score_base": config.score_base,
        "log_odds_factor": config.log_odds_factor,
        "raw_score_before_clamp": raw_score,
        "score_min": config.score_min,
        "score_max": config.score_max,
        "final_credit_score": final_credit_score,
    }


def resolve_score_mapping_config(
    mapping_config: Mapping[str, Any] | ScoreMappingConfig | None = None,
) -> ScoreMappingConfig:
    """Resolve manifest score-mapping parameters with conservative defaults."""

    if mapping_config is None:
        return DEFAULT_SCORE_MAPPING_CONFIG
    if isinstance(mapping_config, ScoreMappingConfig):
        _validate_score_mapping_config(mapping_config)
        return mapping_config

    resolved = ScoreMappingConfig(
        method=_mapping_string(mapping_config, "method", SCORE_MAPPING_METHOD_LOG_ODDS),
        score_base=_mapping_float(mapping_config, "score_base", SCORE_BASE),
        log_odds_factor=_mapping_float(
            mapping_config,
            "log_odds_factor",
            SCORE_LOG_ODDS_FACTOR,
        ),
        probability_clip_min=_mapping_float(
            mapping_config,
            "probability_clip_min",
            0.01,
        ),
        probability_clip_max=_mapping_float(
            mapping_config,
            "probability_clip_max",
            0.99,
        ),
        score_min=_mapping_int(mapping_config, "score_min", SCORE_MIN),
        score_max=_mapping_int(mapping_config, "score_max", SCORE_MAX),
        calibration=_mapping_string(mapping_config, "calibration", "none"),
    )
    _validate_score_mapping_config(resolved)
    return resolved


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


def _mapping_float(
    mapping: Mapping[str, Any],
    key: str,
    default: float,
) -> float:
    value = mapping.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"score_mapping.{key} must be numeric.") from exc


def _mapping_int(
    mapping: Mapping[str, Any],
    key: str,
    default: int,
) -> int:
    value = mapping.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"score_mapping.{key} must be an integer.") from exc


def _mapping_string(
    mapping: Mapping[str, Any],
    key: str,
    default: str,
) -> str:
    value = mapping.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"score_mapping.{key} must be a non-empty string.")
    return value.strip()


def _validate_score_mapping_config(config: ScoreMappingConfig) -> None:
    if config.method != SCORE_MAPPING_METHOD_LOG_ODDS:
        raise ValueError(f"Unsupported score mapping method: {config.method}.")
    if config.log_odds_factor <= 0.0:
        raise ValueError("score_mapping.log_odds_factor must be positive.")
    if not (0.0 < config.probability_clip_min < config.probability_clip_max < 1.0):
        raise ValueError(
            "score_mapping probability clips must satisfy 0 < min < max < 1."
        )
    if config.score_min >= config.score_max:
        raise ValueError("score_mapping.score_min must be lower than score_max.")


__all__ = [
    "DEFAULT_SCORE_MAPPING_CONFIG",
    "SCORE_MAPPING_METHOD_LOG_ODDS",
    "ScoreMappingConfig",
    "compute_percentile",
    "probability_to_score",
    "resolve_score_mapping_config",
    "score_mapping_debug",
]
