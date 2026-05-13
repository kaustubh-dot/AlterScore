"""Parse raw assessment answers into AlterScore psychometric features."""

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
    "financial_literacy_q2": 1,
}
_LOCUS_SCORE_MAP: Final[dict[int, float]] = {
    0: 1.0,
    1: 0.5,
    2: 0.0,
}
_LOSS_AVERSION_SCORE_MAP: Final[dict[int, float]] = {
    0: 0.0,
    1: 0.5,
    2: 1.0,
    3: 0.2,
}
_SOCIAL_CAPITAL_Q1_SCORE_MAP: Final[dict[int, float]] = {
    0: 0.0,
    1: 0.33,
    2: 0.67,
    3: 1.0,
}
_SOCIAL_CAPITAL_Q2_SCORE_MAP: Final[dict[int, float]] = {
    0: 1.0,
    1: 0.8,
    2: 0.0,
    3: 0.5,
}
_SOCIAL_CAPITAL_Q3_SCORE_MAP: Final[dict[int, float]] = {
    0: 1.0,
    1: 0.4,
    2: 0.0,
}
_RESILIENCE_Q3_SCORE_MAP: Final[dict[int, float]] = {
    0: 1.0,
    1: 0.9,
    2: 0.8,
    3: 0.0,
}
_RECIPROCITY_Q2_SCORE_MAP: Final[dict[int, float]] = {
    0: 1.0,
    1: 0.5,
    2: 0.0,
}


def parse_answers(answers: Mapping[str, Any] | Any) -> dict[str, float]:
    """Map raw answer payloads into the 14 psychometric model features."""

    answer_values = _coerce_answer_mapping(answers)

    numeracy_score = _mean(
        [
            _score_with_tolerance(answer_values.get("numeracy_q1"), target=6600.0, tight_tolerance=100.0, partial_tolerance=300.0),
            _score_with_tolerance(answer_values.get("numeracy_q2"), target=1120.0, tight_tolerance=50.0),
            _score_with_tolerance(answer_values.get("numeracy_q3"), target=14400.0, tight_tolerance=200.0),
        ]
    )
    crt_score = _mean(
        [
            _score_with_tolerance(answer_values.get("CRT_q1"), target=5.0, tight_tolerance=2.0),
            _score_with_tolerance(answer_values.get("CRT_q2"), target=5.0, tight_tolerance=1.0),
            _score_with_tolerance(answer_values.get("CRT_q3"), target=47.0, tight_tolerance=1.0),
        ]
    )
    financial_literacy_score = _mean(
        [
            1.0 if answer_values.get(question_id) == correct_answer else 0.0
            for question_id, correct_answer in _FINANCIAL_LITERACY_CORRECT_ANSWERS.items()
        ]
    )

    future_choice_share = _mean(
        [
            _binary_choice_score(answer_values.get("future_orient_q1")),
            _binary_choice_score(answer_values.get("future_orient_q2")),
        ]
    )
    future_orientation = _clip01(
        0.6 * future_choice_share + 0.4 * _normalize_likert(answer_values.get("future_orient_q3"))
    )
    delay_discounting_rate = future_choice_share

    risk_choice_share = _mean(
        [
            _binary_choice_score(answer_values.get("risk_q1")),
            _binary_choice_score(answer_values.get("risk_q2")),
        ]
    )
    risk_consistency_flag = float(
        _coerce_int(answer_values.get("risk_q1"), default=0) != _coerce_int(answer_values.get("risk_q2"), default=0)
    )
    loss_aversion_score = _LOSS_AVERSION_SCORE_MAP.get(
        _coerce_int(answer_values.get("loss_aversion_q1"), default=-1),
        0.0,
    )

    locus_of_control = _clip01(
        _mean(
            [
                _LOCUS_SCORE_MAP.get(_coerce_int(answer_values.get("locus_q1"), default=-1), 0.0),
                _LOCUS_SCORE_MAP.get(_coerce_int(answer_values.get("locus_q2"), default=-1), 0.0),
                _normalize_likert(answer_values.get("locus_q3")),
            ]
        )
    )
    conscientiousness_score = _normalize_likert(answer_values.get("conscientiousness_q1"))
    social_capital_score = _clip01(
        _mean(
            [
                _SOCIAL_CAPITAL_Q1_SCORE_MAP.get(_coerce_int(answer_values.get("social_capital_q1"), default=-1), 0.0),
                _SOCIAL_CAPITAL_Q2_SCORE_MAP.get(_coerce_int(answer_values.get("social_capital_q2"), default=-1), 0.0),
                _SOCIAL_CAPITAL_Q3_SCORE_MAP.get(_coerce_int(answer_values.get("social_capital_q3"), default=-1), 0.0),
            ]
        )
    )
    honesty_score = _compute_honesty_score(
        answers=answer_values,
        numeracy_score=numeracy_score,
        crt_score=crt_score,
    )
    resilience_score = _clip01(
        _mean(
            [
                _normalize_likert(answer_values.get("resilience_q1")),
                _normalize_likert(answer_values.get("resilience_q2")),
                _RESILIENCE_Q3_SCORE_MAP.get(_coerce_int(answer_values.get("resilience_q3"), default=-1), 0.0),
            ]
        )
    )
    reciprocity_norm = _clip01(
        _mean(
            [
                _normalize_likert(answer_values.get("reciprocity_q1")),
                _RECIPROCITY_Q2_SCORE_MAP.get(_coerce_int(answer_values.get("reciprocity_q2"), default=-1), 0.0),
            ]
        )
    )

    return {
        "numeracy_score": numeracy_score,
        "CRT_score": crt_score,
        "financial_literacy_score": financial_literacy_score,
        "future_orientation": future_orientation,
        "delay_discounting_rate": delay_discounting_rate,
        "risk_attitude": risk_choice_share,
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
    future_inconsistency = abs(
        _coerce_int(answers.get("future_orient_q1"), default=0)
        - _coerce_int(answers.get("future_orient_repeat"), default=0)
    )
    locus_inconsistency = abs(
        _coerce_int(answers.get("locus_q1"), default=0)
        - _coerce_int(answers.get("locus_repeat"), default=0)
    ) / 2.0
    inconsistency_ratio = (future_inconsistency + locus_inconsistency) / 2.0

    suspicious_traps = sum(
        _coerce_int(answers.get(question_id), default=3) >= 4
        for question_id in ("honesty_trap_q1", "honesty_trap_q2")
    )
    social_desirability_penalty = 0.25 * suspicious_traps

    implausibility_flag = float(
        suspicious_traps == 2 and numeracy_score >= (2.0 / 3.0) and crt_score >= (2.0 / 3.0)
    )
    honesty = (
        (1.0 - inconsistency_ratio)
        * (1.0 - social_desirability_penalty)
        * (1.0 - 0.25 * implausibility_flag)
    )
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


def _binary_choice_score(value: Any) -> float:
    return float(_coerce_int(value, default=0) == 1)


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
