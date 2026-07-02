"""Score request and response schemas for AlterScore."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Literal
from uuid import uuid4

from pydantic import Field, field_validator, model_validator

from backend.app.schemas.common import SchemaModel

TimeOfDay = Literal["morning", "afternoon", "evening", "night"]
DeviceType = Literal["mobile", "desktop", "tablet"]
ExplanationDirection = Literal["positive", "negative"]

_SCENARIO_OPTION_PREFIXES = {
    "scenario_s1": "s1_",
    "scenario_s2": "s2_",
    "scenario_s3": "s3_",
    "scenario_s4": "s4_",
    "scenario_s5": "s5_",
    "scenario_s6": "s6_",
    "scenario_s8": "s8_",
}

class ScenarioAnswer(SchemaModel):
    """A single scenario question response with primary, least-like-me, and telemetry."""

    primary: str = Field(
        ..., min_length=2, max_length=10, description="Selected option ID (e.g. 's1_a')"
    )
    least: str = Field(
        ..., min_length=2, max_length=10, description="Least-like-me option ID"
    )
    first_click_ms: int | None = Field(
        default=None, ge=0, le=120000, description="Time to first click in ms"
    )
    change_count: int = Field(
        default=0, ge=0, le=50, description="Number of answer changes before final pick"
    )

    @field_validator("primary", "least")
    @classmethod
    def validate_option_format(cls, v: str) -> str:
        # Option IDs follow the pattern: s{n}_{letter} e.g. s1_a, s8_d
        if not re.match(r"^s\d+_[a-z]$", v):
            raise ValueError(
                f"Invalid scenario option ID format: '{v}'. Expected pattern: s1_a"
            )
        return v

    @model_validator(mode="after")
    def validate_least_differs_from_primary(self) -> "ScenarioAnswer":
        if self.least == self.primary:
            raise ValueError("'least' option cannot be the same as 'primary' option.")
        return self


class AnswerPayload(SchemaModel):
    # -----------------------------------------------------------------------
    # Section A — Financial Reasoning (5 questions)
    # -----------------------------------------------------------------------
    numeracy_q1: int = Field(..., ge=0, le=10000)
    numeracy_q2: float = Field(..., ge=0, le=10000)
    financial_literacy_q1: int = Field(..., ge=0, le=3)
    CRT_q1: float = Field(..., ge=0, le=1000)
    CRT_q2: int = Field(..., ge=1, le=48)

    # -----------------------------------------------------------------------
    # Section B — Behavioral Decision Scenarios (6 main + 2 honesty traps)
    # Scenario answers are rich objects with option ID + optional telemetry.
    # Honesty traps remain as Likert integers (embedded, not labeled).
    # -----------------------------------------------------------------------
    scenario_s1: ScenarioAnswer
    scenario_s2: ScenarioAnswer
    scenario_s3: ScenarioAnswer
    scenario_s4: ScenarioAnswer
    scenario_s5: ScenarioAnswer
    scenario_s6: ScenarioAnswer
    honesty_trap_q1: int = Field(..., ge=1, le=5)
    scenario_s8: ScenarioAnswer  # Consistency trap — mirrors S1

    # -----------------------------------------------------------------------
    # Section C — Open Text (1 question)
    # -----------------------------------------------------------------------
    open_response_text: str = Field(..., max_length=1000)

    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for passing to parsers and analyzers."""
        return self.model_dump()

    @field_validator("open_response_text")
    @classmethod
    def normalize_open_response_text(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @model_validator(mode="after")
    def validate_scenario_option_prefixes(self) -> "AnswerPayload":
        for field_name, expected_prefix in _SCENARIO_OPTION_PREFIXES.items():
            scenario_answer = getattr(self, field_name)
            _validate_scenario_option_prefix(
                scenario_answer.primary,
                field_name=field_name,
                expected_prefix=expected_prefix,
            )
            _validate_scenario_option_prefix(
                scenario_answer.least,
                field_name=field_name,
                expected_prefix=expected_prefix,
            )
        return self


class BehavioralPayload(SchemaModel):
    avg_response_time_ms: float = Field(..., ge=100, le=120000)
    answer_change_rate: float = Field(..., ge=0, le=1)
    session_duration_sec: float = Field(..., ge=0, le=7200)
    dropout_count: int = Field(..., ge=0, le=20)
    scroll_hesitation_score: float = Field(..., ge=0, le=1)
    risk_response_speed_ratio: float = Field(..., ge=0, le=5)
    time_of_day: TimeOfDay
    device_type: DeviceType
    typing_speed_wpm: float = Field(default=0.0, ge=0, le=200)


def _validate_scenario_option_prefix(
    option_id: str,
    *,
    field_name: str,
    expected_prefix: str,
) -> None:
    if not option_id.startswith(expected_prefix):
        raise ValueError(
            f"{field_name} option '{option_id}' must start with '{expected_prefix}'."
        )


class ScoreRequest(SchemaModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    answers: AnswerPayload
    behavioral: BehavioralPayload


class ExplanationItem(SchemaModel):
    feature: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    shap_value: float
    direction: ExplanationDirection
    feature_value: float
    plain_language: str = Field(..., min_length=1)


class CounterfactualAction(SchemaModel):
    feature: str = Field(..., min_length=1)
    current_value: float
    suggested_value: float
    estimated_score_gain: int = Field(..., ge=0)
    plain_language: str = Field(..., min_length=1)


class LoanEligibility(SchemaModel):
    band: str = Field(..., min_length=1)
    amount_min: int = Field(..., ge=0)
    amount_max: int = Field(..., ge=0)
    description: str = Field(..., min_length=1)


class ImprovementTip(SchemaModel):
    feature: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class GovernanceSignals(SchemaModel):
    scenario_consistency_score: float = Field(default=0.5, ge=0, le=1)
    scenario_fast_gaming: bool = False
    scenario_straight_lining_ratio: float = Field(default=0.0, ge=0, le=1)
    scenario_change_rate: float = Field(default=0.0, ge=0, le=1)


class ScoreResponse(SchemaModel):
    session_id: str = Field(..., min_length=1)
    credit_score: int = Field(..., ge=300, le=850)
    risk_band: str = Field(..., min_length=1)
    repayment_probability: float = Field(..., ge=0, le=1)
    percentile: int = Field(..., ge=0, le=100)
    explanation: list[ExplanationItem]
    counterfactual_actions: list[CounterfactualAction]
    loan_eligibility: LoanEligibility
    improvement_tips: list[ImprovementTip]
    governance_signals: GovernanceSignals = Field(default_factory=GovernanceSignals)
    timestamp: datetime


__all__ = [
    "AnswerPayload",
    "BehavioralPayload",
    "CounterfactualAction",
    "DeviceType",
    "ExplanationDirection",
    "GovernanceSignals",
    "ExplanationItem",
    "ImprovementTip",
    "LoanEligibility",
    "ScenarioAnswer",
    "ScoreRequest",
    "ScoreResponse",
    "TimeOfDay",
]
