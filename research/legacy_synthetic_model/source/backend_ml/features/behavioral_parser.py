"""Parse raw behavioral telemetry into AlterScore behavioral model features."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

BEHAVIORAL_FEATURES: Final[list[str]] = [
    "avg_response_time_ms",
    "answer_change_rate",
    "session_duration_sec",
    "dropout_count",
    "scroll_hesitation_score",
    "risk_response_speed_ratio",
    "typing_speed_wpm",
    "device_type",
    "time_of_day",
]

VALID_TIME_OF_DAY: Final[set[str]] = {
    "morning",
    "afternoon",
    "evening",
    "night",
}
VALID_DEVICE_TYPES: Final[set[str]] = {
    "mobile",
    "desktop",
    "tablet",
}


def parse_behavioral(
    behavioral: Mapping[str, Any] | Any,
) -> dict[str, float | int | str]:
    """Coerce raw telemetry into the canonical 9 behavioral model features."""

    values = _coerce_behavioral_mapping(behavioral)

    return {
        "avg_response_time_ms": _coerce_bounded_float(
            values.get("avg_response_time_ms"),
            field_name="avg_response_time_ms",
            lower=100.0,
            upper=120000.0,
        ),
        "answer_change_rate": _coerce_bounded_float(
            values.get("answer_change_rate"),
            field_name="answer_change_rate",
            lower=0.0,
            upper=1.0,
        ),
        "session_duration_sec": _coerce_bounded_float(
            values.get("session_duration_sec"),
            field_name="session_duration_sec",
            lower=0.0,
            upper=7200.0,
        ),
        "dropout_count": _coerce_bounded_int(
            values.get("dropout_count"),
            field_name="dropout_count",
            lower=0,
            upper=20,
        ),
        "scroll_hesitation_score": _coerce_bounded_float(
            values.get("scroll_hesitation_score"),
            field_name="scroll_hesitation_score",
            lower=0.0,
            upper=1.0,
        ),
        "risk_response_speed_ratio": _coerce_bounded_float(
            values.get("risk_response_speed_ratio"),
            field_name="risk_response_speed_ratio",
            lower=0.0,
            upper=5.0,
        ),
        "typing_speed_wpm": _coerce_bounded_float(
            values.get("typing_speed_wpm", 0.0),
            field_name="typing_speed_wpm",
            lower=0.0,
            upper=200.0,
        ),
        "device_type": _coerce_categorical(
            values.get("device_type"),
            field_name="device_type",
            valid_values=VALID_DEVICE_TYPES,
        ),
        "time_of_day": _coerce_categorical(
            values.get("time_of_day"),
            field_name="time_of_day",
            valid_values=VALID_TIME_OF_DAY,
        ),
    }


def _coerce_behavioral_mapping(behavioral: Mapping[str, Any] | Any) -> dict[str, Any]:
    if hasattr(behavioral, "model_dump"):
        return dict(behavioral.model_dump())
    if isinstance(behavioral, Mapping):
        return dict(behavioral)
    raise TypeError("behavioral must be a mapping or expose model_dump().")


def _coerce_bounded_float(
    value: Any,
    *,
    field_name: str,
    lower: float,
    upper: float,
) -> float:
    if value is None:
        raise ValueError(f"{field_name} is required.")
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc

    return float(min(max(numeric_value, lower), upper))


def _coerce_bounded_int(
    value: Any,
    *,
    field_name: str,
    lower: int,
    upper: int,
) -> int:
    if value is None:
        raise ValueError(f"{field_name} is required.")
    try:
        numeric_value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer.") from exc

    return min(max(numeric_value, lower), upper)


def _coerce_categorical(
    value: Any,
    *,
    field_name: str,
    valid_values: set[str],
) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required.")
    normalized_value = str(value).strip().lower()
    if normalized_value not in valid_values:
        raise ValueError(
            f"{field_name} must be one of {sorted(valid_values)}; found {value!r}."
        )
    return normalized_value


__all__ = [
    "BEHAVIORAL_FEATURES",
    "VALID_DEVICE_TYPES",
    "VALID_TIME_OF_DAY",
    "parse_behavioral",
]
