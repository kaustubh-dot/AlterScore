"""Score request and response schemas for AlterScore."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import Field

from backend.app.schemas.common import SchemaModel

TimeOfDay = Literal["morning", "afternoon", "evening", "night"]
DeviceType = Literal["mobile", "desktop", "tablet"]
ExplanationDirection = Literal["positive", "negative"]


class AnswerPayload(SchemaModel):
    numeracy_q1: int = Field(..., ge=0, le=10000)
    numeracy_q2: float = Field(..., ge=0, le=10000)
    numeracy_q3: float = Field(..., ge=0, le=100000)
    financial_literacy_q1: int = Field(..., ge=0, le=3)
    financial_literacy_q2: int = Field(..., ge=0, le=2)
    conscientiousness_q1: int = Field(..., ge=1, le=5)

    CRT_q1: float = Field(..., ge=0, le=1000)
    CRT_q2: float = Field(..., ge=0, le=1000)
    CRT_q3: int = Field(..., ge=1, le=48)
    future_orient_q1: int = Field(..., ge=0, le=1)
    future_orient_q2: int = Field(..., ge=0, le=1)
    future_orient_q3: int = Field(..., ge=1, le=5)
    risk_q1: int = Field(..., ge=0, le=1)
    risk_q2: int = Field(..., ge=0, le=1)

    locus_q1: int = Field(..., ge=0, le=2)
    locus_q2: int = Field(..., ge=0, le=2)
    locus_q3: int = Field(..., ge=1, le=5)
    social_capital_q1: int = Field(..., ge=0, le=3)
    social_capital_q2: int = Field(..., ge=0, le=2)
    social_capital_q3: int = Field(..., ge=0, le=2)
    resilience_q1: int = Field(..., ge=1, le=5)
    resilience_q2: int = Field(..., ge=1, le=5)
    resilience_q3: int = Field(..., ge=0, le=3)
    loss_aversion_q1: int = Field(..., ge=0, le=2)

    honesty_trap_q1: int = Field(..., ge=1, le=5)
    honesty_trap_q2: int = Field(..., ge=1, le=5)
    future_orient_repeat: int = Field(..., ge=0, le=1)
    locus_repeat: int = Field(..., ge=0, le=2)
    reciprocity_q1: int = Field(..., ge=1, le=5)
    reciprocity_q2: int = Field(..., ge=0, le=2)

    q27_resilience_text: str = Field(..., max_length=1000)


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
    timestamp: datetime


__all__ = [
    "AnswerPayload",
    "BehavioralPayload",
    "CounterfactualAction",
    "DeviceType",
    "ExplanationDirection",
    "ExplanationItem",
    "ImprovementTip",
    "LoanEligibility",
    "ScoreRequest",
    "ScoreResponse",
    "TimeOfDay",
]
