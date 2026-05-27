"""Parse raw assessment answers into AlterScore psychometric features.

v2 assessment: 5 reasoning + 8 behavioral scenarios + 1 open-text.
Scenario questions are handled by scenario_analyzer.py; this module
handles the objective reasoning questions (numeracy, CRT, financial literacy)
and the embedded honesty traps.

The scenario_analyzer enrichment is applied in feature_assembly.py after
this parser produces the base psychometric features.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final


PSYCHOMETRIC_FEATURES: Final[list[str]] = [
    "numeracy_score",
    "CRT_score",
    "financial_literacy_score",
    "future_orientation",
    "delay_discounting_rate",
    "risk_attitude",
    "risk_consistency_flag",
    "loss_aversion_score",
    "locus_of_control",
    "conscientiousness_score",
    "social_capital_score",
    "honesty_score",
    "resilience_score",
    "reciprocity_norm",
]

_FINANCIAL_LITERACY_CORRECT_ANSWERS: Final[dict[str, int]] = {
    "financial_literacy_q1": 1,
}


def parse_answers(answers: Mapping[str, Any] | Any) -> dict[str, float]:
    """Map raw answer payloads into the 14 psychometric model features.

    Produces base values from the objective reasoning questions only.
    Scenario-derived enrichments are applied separately by
    compute_scenario_enriched_features() in feature_assembly.py.

    Features that have no direct source in the v2 question bank
    (risk_attitude, loss_aversion_score, etc.) are set to neutral
    priors (0.5) and then enriched by scenario signals downstream.
    """
    answer_values = _coerce_answer_mapping(answers)

    # --- Numeracy (2 questions) -------------------------------------------
    numeracy_score = _mean(
        [
            _score_with_tolerance(
                answer_values.get("numeracy_q1"),
                target=6600.0,
                tight_tolerance=100.0,
                partial_tolerance=300.0,
            ),
            _score_with_tolerance(
                answer_values.get("numeracy_q2"),
                target=1120.0,
                tight_tolerance=50.0,
            ),
        ]
    )

    # --- CRT (2 questions) ------------------------------------------------
    crt_score = _mean(
        [
            _score_with_tolerance(answer_values.get("CRT_q1"), target=5.0, tight_tolerance=2.0),
            _score_with_tolerance(answer_values.get("CRT_q2"), target=47.0, tight_tolerance=1.0),
        ]
    )

    # --- Financial Literacy (1 question) ----------------------------------
    financial_literacy_score = _mean(
        [
            1.0 if answer_values.get(q_id) == correct else 0.0
            for q_id, correct in _FINANCIAL_LITERACY_CORRECT_ANSWERS.items()
        ]
    )

    # --- Honesty (embedded traps: honesty_trap_q1, honesty_trap_q2) -------
    honesty_score = _compute_honesty_score(
        answers=answer_values,
        numeracy_score=numeracy_score,
        crt_score=crt_score,
    )

    # --- Features with no direct v2 question source -----------------------
    # Set to neutral priors. Scenario enrichment in feature_assembly.py will
    # blend scenario-derived values into these using a 60/40 weighting.
    future_orientation = 0.5
    delay_discounting_rate = 0.5
    risk_attitude = 0.5
    risk_consistency_flag = 0.0  # No risk pair in v2; set to no-conflict
    loss_aversion_score = 0.5
    locus_of_control = 0.5
    conscientiousness_score = 0.5
    social_capital_score = 0.5
    resilience_score = 0.5
    reciprocity_norm = 0.5

    return {
        "numeracy_score": numeracy_score,
        "CRT_score": crt_score,
        "financial_literacy_score": financial_literacy_score,
        "future_orientation": future_orientation,
        "delay_discounting_rate": delay_discounting_rate,
        "risk_attitude": risk_attitude,
        "risk_consistency_flag": risk_consistency_flag,
        "loss_aversion_score": loss_aversion_score,
        "locus_of_control": locus_of_control,
        "conscientiousness_score": conscientiousness_score,
        "social_capital_score": social_capital_score,
        "honesty_score": honesty_score,
        "resilience_score": resilience_score,
        "reciprocity_norm": reciprocity_norm,
    }


def _compute_honesty_score(
    answers: Mapping[str, Any],
    *,
    numeracy_score: float,
    crt_score: float,
) -> float:
    """Compute honesty score from embedded social-desirability traps.

    v2 uses only honesty_trap_q1 as the active frontend trap.
    honesty_trap_q2 was removed from the question bank (frontend no longer
    sends it; schema defaults to 3 = neutral). The backend still reads both
    fields for backward compatibility, but the active signal is from q1.

    Honesty trap: "I have never told even a small lie in my entire life."
    Agreeing (≥4) with an implausible universal triggers a penalty.
    """
    # q2 will be 3 (neutral) from schema default — counts as 0 suspicious traps
    suspicious_traps = sum(
        _coerce_int(answers.get(q_id), default=3) >= 4
        for q_id in ("honesty_trap_q1", "honesty_trap_q2")
    )
    # 1 suspicious trap = 0.25 penalty (max from q1 alone); 2 = 0.45 (legacy compat)
    social_desirability_penalty = 0.25 * suspicious_traps if suspicious_traps == 1 else 0.45 * suspicious_traps

    # Implausibility: agreeing with both traps + high cognitive score = likely faking
    implausibility_flag = float(
        suspicious_traps >= 1
        and numeracy_score >= 0.5
        and crt_score >= 0.5
    )
    honesty = (1.0 - social_desirability_penalty) * (1.0 - 0.20 * implausibility_flag)
    return _clip01(honesty)



def _coerce_answer_mapping(answers: Mapping[str, Any] | Any) -> dict[str, Any]:
    if hasattr(answers, "model_dump"):
        return dict(answers.model_dump())
    if isinstance(answers, Mapping):
        return dict(answers)
    raise TypeError("answers must be a mapping or expose model_dump().")


def _score_with_tolerance(
    answer: Any,
    *,
    target: float,
    tight_tolerance: float,
    partial_tolerance: float | None = None,
) -> float:
    numeric_answer = _coerce_float(answer, default=None)
    if numeric_answer is None:
        return 0.0

    error = abs(numeric_answer - target)
    if error <= tight_tolerance:
        return 1.0
    if partial_tolerance is not None and error <= partial_tolerance:
        return 0.5
    return 0.0


def _normalize_likert(value: Any, *, default: int = 3) -> float:
    coerced = _coerce_int(value, default=default)
    return _clip01((coerced - 1) / 4.0)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _coerce_float(value: Any, *, default: float | None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: Any, *, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clip01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


__all__ = [
    "PSYCHOMETRIC_FEATURES",
    "parse_answers",
]
