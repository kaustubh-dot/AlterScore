"""Scenario-based answer analyzer for AlterScore v2 behavioral assessment.

Converts raw scenario option selections into psychometric feature contributions
using pre-coded option signal values, and computes a cross-scenario consistency
score to enrich the cognitive_consistency_index.

Design constraints:
- Outputs only feed into EXISTING feature names (no new model features in Phase 1).
- All output values are clipped to [0.0, 1.0].
- The consistency score is returned separately and blended into derived features.
- This module is pure-Python with no model-loading side effects.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scenario option codebook
# Each option carries (primary_feature, primary_value, secondary_feature, secondary_value).
# Values are pre-coded [0.0, 1.0] from content design review.
#
# Layout: { option_id: (primary_feature, primary_value, secondary_feature, secondary_value) }
# ---------------------------------------------------------------------------

_OPTION_CODEBOOK: Final[dict[str, tuple[str, float, str, float]]] = {
    # S1 — EMI vs. supplier opportunity
    "s1_a": ("future_orientation", 0.70, "conscientiousness_score", 0.30),
    "s1_b": ("conscientiousness_score", 1.00, "future_orientation", 0.50),
    "s1_c": ("conscientiousness_score", 0.80, "future_orientation", 0.80),
    "s1_d": ("social_capital_score", 0.80, "conscientiousness_score", 0.60),
    # S2 — Silent client / rent pressure
    "s2_a": ("locus_of_control", 0.80, "resilience_score", 0.60),
    "s2_b": ("locus_of_control", 1.00, "conscientiousness_score", 0.90),
    "s2_c": ("social_capital_score", 0.90, "locus_of_control", 0.60),
    "s2_d": ("locus_of_control", 0.20, "resilience_score", 0.30),
    # S3 — Windfall allocation
    "s3_a": ("future_orientation", 0.50, "loss_aversion_score", 0.70),
    "s3_b": ("future_orientation", 1.00, "conscientiousness_score", 0.90),
    "s3_c": ("conscientiousness_score", 1.00, "future_orientation", 0.80),
    "s3_d": ("future_orientation", 0.10, "conscientiousness_score", 0.20),
    # S4 — Business loss decision
    "s4_a": ("loss_aversion_score", 0.30, "resilience_score", 0.40),
    "s4_b": ("resilience_score", 0.90, "conscientiousness_score", 0.90),
    "s4_c": ("future_orientation", 0.60, "loss_aversion_score", 0.10),
    "s4_d": ("resilience_score", 1.00, "locus_of_control", 0.90),
    # S5 — Neighbour loan ask
    "s5_a": ("social_capital_score", 0.90, "reciprocity_norm", 1.00),
    "s5_b": ("honesty_score", 0.90, "social_capital_score", 0.70),
    "s5_c": ("conscientiousness_score", 0.80, "honesty_score", 0.60),
    "s5_d": ("honesty_score", 1.00, "locus_of_control", 0.80),
    # S6 — Family wedding pressure
    "s6_a": ("locus_of_control", 0.20, "future_orientation", 0.30),
    "s6_b": ("conscientiousness_score", 0.90, "locus_of_control", 0.70),
    "s6_c": ("honesty_score", 1.00, "locus_of_control", 0.90),
    "s6_d": ("locus_of_control", 1.00, "future_orientation", 0.90),
    # S8 — Consistency trap (mirrors S1 semantically)
    "s8_a": ("future_orientation", 0.70, "conscientiousness_score", 0.30),
    "s8_b": ("conscientiousness_score", 1.00, "future_orientation", 0.50),
    "s8_c": ("conscientiousness_score", 0.80, "future_orientation", 0.80),
    "s8_d": ("social_capital_score", 0.80, "conscientiousness_score", 0.60),
}

# Consistency trap pair: S8 option → equivalent S1 option
_CONSISTENCY_MIRROR: Final[dict[str, str]] = {
    "s8_a": "s1_a",
    "s8_b": "s1_b",
    "s8_c": "s1_c",
    "s8_d": "s1_d",
}

# Scenario question IDs mapped to their option prefix (for flexible lookup)
_SCENARIO_IDS: Final[list[str]] = [
    "scenario_s1",
    "scenario_s2",
    "scenario_s3",
    "scenario_s4",
    "scenario_s5",
    "scenario_s6",
    "scenario_s8",
]

# Primary feature weight vs. secondary feature weight when aggregating
_PRIMARY_WEIGHT: Final[float] = 0.65
_SECONDARY_WEIGHT: Final[float] = 0.35

# Scenario minimum first-click time for gaming detection (milliseconds)
# Responses faster than this across ALL scenarios trigger the fast-pattern flag.
_FAST_CLICK_THRESHOLD_MS: Final[float] = 2000.0


def analyze_scenario_responses(
    answers: Mapping[str, Any],
) -> dict[str, Any]:
    """Analyze all scenario question responses and return feature enrichments.

    Returns a dict with:
      - feature_contributions: dict[feature_name, float] — weighted contributions
        from all scenario options, ready to be merged with psychometric features.
      - scenario_consistency_score: float [0.0, 1.0] — how consistent S1/S8 choices are.
      - fast_pattern_gaming: bool — True if avg first-click < threshold (speed-gaming signal).
      - scenario_resolution_times: list[float] — per-scenario first-click times in ms.
    """
    answer_values = _coerce_mapping(answers)

    # Accumulate weighted contributions and weights per feature
    feature_accumulator: dict[str, float] = {}
    weight_accumulator: dict[str, float] = {}
    first_click_times: list[float] = []

    for scenario_id in _SCENARIO_IDS:
        raw = answer_values.get(scenario_id)
        if raw is None:
            continue

        option_id, first_click_ms = _extract_option_id(raw, scenario_id)
        if first_click_ms is not None:
            first_click_times.append(first_click_ms)

        if option_id is None or option_id not in _OPTION_CODEBOOK:
            logger.debug(
                "Scenario analyzer: unknown option_id '%s' for '%s'",
                option_id,
                scenario_id,
            )
            continue

        primary_feature, primary_value, secondary_feature, secondary_value = (
            _OPTION_CODEBOOK[option_id]
        )

        for feature, value, weight in (
            (primary_feature, primary_value, _PRIMARY_WEIGHT),
            (secondary_feature, secondary_value, _SECONDARY_WEIGHT),
        ):
            feature_accumulator[feature] = (
                feature_accumulator.get(feature, 0.0) + value * weight
            )
            weight_accumulator[feature] = weight_accumulator.get(feature, 0.0) + weight

    # True weighted average blended with 0.5 prior (60/40 ratio) to match training
    feature_contributions: dict[str, float] = {}
    for feature_name, sum_weighted in feature_accumulator.items():
        sum_weights = weight_accumulator.get(feature_name, 0.0)
        if sum_weights > 0:
            weighted_avg = sum_weighted / sum_weights
            blended_avg = 0.20 + 0.60 * weighted_avg
            feature_contributions[feature_name] = float(min(max(blended_avg, 0.0), 1.0))

    # Consistency check: S1 vs S8
    scenario_consistency_score = _compute_consistency_score(answer_values)

    # Fast-pattern gaming flag
    fast_pattern_gaming = _check_fast_pattern(first_click_times)

    # Straight-lining check
    scenario_straight_lining_ratio = _compute_straight_lining_ratio(answer_values)

    return {
        "feature_contributions": feature_contributions,
        "scenario_consistency_score": scenario_consistency_score,
        "fast_pattern_gaming": fast_pattern_gaming,
        "scenario_straight_lining_ratio": scenario_straight_lining_ratio,
        "scenario_resolution_times": first_click_times,
    }


def compute_scenario_enriched_features(
    psychometric_features: dict[str, float],
    answers: Mapping[str, Any],
) -> dict[str, float]:
    """Merge scenario feature contributions into existing psychometric features.

    Blending strategy (Phase 1 — no retraining):
    - Features with a REAL psychometric measurement (numeracy, CRT, financial
      literacy, honesty): kept exactly as-is from answer_parser. Scenario
      signals do not override objective measurement.
    - Features with NO direct v2 question (locus, conscientiousness, resilience,
      future_orientation, etc.): the answer_parser returns 0.5 as a neutral
      prior. For these, we use the scenario-derived value directly (100% weight),
      since there is no real measurement to preserve.

    This ensures good scenario choices produce high feature values, matching the
    distribution the model was trained on.
    """
    analysis = analyze_scenario_responses(answers)
    contributions = analysis["feature_contributions"]
    consistency = analysis["scenario_consistency_score"]

    # Features that come from objective questions — never overridden by scenarios
    OBJECTIVE_FEATURES = frozenset(
        {
            "numeracy_score",
            "CRT_score",
            "financial_literacy_score",
            "honesty_score",
            "risk_consistency_flag",  # no direct v2 question but not scenario-driven either
        }
    )

    # Neutral prior sentinel: answer_parser sets 0.5 for features without a direct question
    NEUTRAL_PRIOR = 0.5

    enriched = dict(psychometric_features)
    for feature_name, scenario_value in contributions.items():
        if feature_name in OBJECTIVE_FEATURES:
            # Never override objective measurements with scenario signals
            continue

        existing_value = float(enriched.get(feature_name, NEUTRAL_PRIOR))

        if abs(existing_value - NEUTRAL_PRIOR) < 1e-9:
            # No real measurement behind this value — use scenario directly
            enriched[feature_name] = float(min(max(scenario_value, 0.0), 1.0))
        else:
            # Real measurement exists (future Phase 2 compatibility) — blend conservatively
            blended = 0.65 * existing_value + 0.35 * scenario_value
            enriched[feature_name] = float(min(max(blended, 0.0), 1.0))

    # Expose governance signals for downstream use
    enriched["scenario_consistency_score"] = consistency
    enriched["scenario_fast_gaming"] = float(analysis["fast_pattern_gaming"])
    enriched["scenario_straight_lining_ratio"] = float(
        analysis["scenario_straight_lining_ratio"]
    )

    return enriched


def _compute_consistency_score(answer_values: dict[str, Any]) -> float:
    """Compute S1/S8 consistency score.

    Returns 1.0 if the S8 pick mirrors S1 semantically, 0.0 for a complete
    mismatch. Returns 0.5 (neutral) if either question is unanswered.
    """
    s1_raw = answer_values.get("scenario_s1")
    s8_raw = answer_values.get("scenario_s8")

    if s1_raw is None or s8_raw is None:
        return 0.5  # neutral when consistency trap not completed

    s1_option, _ = _extract_option_id(s1_raw, "scenario_s1")
    s8_option, _ = _extract_option_id(s8_raw, "scenario_s8")

    if s1_option is None or s8_option is None:
        return 0.5

    # Check if S8 option mirrors the S1 option (same behavioral preference)
    expected_s1 = _CONSISTENCY_MIRROR.get(s8_option)
    if expected_s1 is None:
        return 0.5

    if expected_s1 == s1_option:
        return 1.0  # fully consistent

    # Partial consistency: check if both options map to same primary feature
    s1_entry = _OPTION_CODEBOOK.get(s1_option)
    s8_entry = _OPTION_CODEBOOK.get(s8_option)
    if s1_entry and s8_entry and s1_entry[0] == s8_entry[0]:
        return 0.65  # same dominant behavioral tendency, different expression

    return 0.0  # genuinely inconsistent


def _compute_straight_lining_ratio(answer_values: dict[str, Any]) -> float:
    """Compute the maximum straight-lining ratio across the scenario responses.

    Returns the fraction of scenario answers that share the same option suffix
    (e.g., '_a', '_b', '_c', '_d'). Returns 0.0 if no options are answered.
    """
    suffixes = []
    for scenario_id in _SCENARIO_IDS:
        raw = answer_values.get(scenario_id)
        if raw is None:
            continue
        option_id, _ = _extract_option_id(raw, scenario_id)
        if option_id and "_" in option_id:
            suffix = option_id.split("_")[-1]
            suffixes.append(suffix)

    if not suffixes:
        return 0.0

    # Count the occurrence of each suffix
    counts: dict[str, int] = {}
    for s in suffixes:
        counts[s] = counts.get(s, 0) + 1

    max_count = max(counts.values())
    return float(max_count / len(suffixes))


def _check_fast_pattern(first_click_times: list[float]) -> bool:
    """Return True if the average scenario resolution time is below the threshold.

    Only flag if we have at least 4 scenario resolution times (robust signal).
    """
    if len(first_click_times) < 4:
        return False
    avg = sum(first_click_times) / len(first_click_times)
    return avg < _FAST_CLICK_THRESHOLD_MS


def _extract_option_id(
    raw: Any,
    scenario_id: str,
) -> tuple[str | None, float | None]:
    """Extract the primary option ID and first-click time from a raw answer value.

    The frontend sends either:
      - A string: the option ID directly (legacy / simple mode)
      - A dict: { primary, least, first_click_ms, change_count }
    """
    if isinstance(raw, str):
        return raw if raw else None, None
    if isinstance(raw, dict):
        option_id = raw.get("primary")
        first_click_ms = raw.get("first_click_ms")
        option_id = str(option_id) if option_id else None
        first_click_ms = (
            float(first_click_ms) if isinstance(first_click_ms, (int, float)) else None
        )
        return option_id, first_click_ms
    logger.warning(
        "Scenario analyzer: unexpected answer type '%s' for '%s'",
        type(raw).__name__,
        scenario_id,
    )
    return None, None


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return dict(value.model_dump())
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(
        f"answers must be a mapping or expose model_dump(), got {type(value).__name__}"
    )


__all__ = [
    "analyze_scenario_responses",
    "compute_scenario_enriched_features",
]
