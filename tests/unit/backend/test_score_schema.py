from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.app.schemas.common import ErrorResponse
from backend.app.schemas.score import AnswerPayload, ScoreRequest, ScoreResponse


def build_valid_score_request_payload() -> dict:
    return {
        "answers": {
            "numeracy_q1": 6600,
            "numeracy_q2": 1120,
            "numeracy_q3": 14400,
            "financial_literacy_q1": 1,
            "financial_literacy_q2": 1,
            "conscientiousness_q1": 4,
            "CRT_q1": 5,
            "CRT_q2": 5,
            "CRT_q3": 47,
            "future_orient_q1": 1,
            "future_orient_q2": 1,
            "future_orient_q3": 4,
            "risk_q1": 0,
            "risk_q2": 1,
            "locus_q1": 0,
            "locus_q2": 1,
            "locus_q3": 4,
            "social_capital_q1": 2,
            "social_capital_q2": 0,
            "social_capital_q3": 0,
            "resilience_q1": 4,
            "resilience_q2": 4,
            "resilience_q3": 0,
            "loss_aversion_q1": 0,
            "honesty_trap_q1": 2,
            "honesty_trap_q2": 3,
            "future_orient_repeat": 1,
            "locus_repeat": 0,
            "reciprocity_q1": 4,
            "reciprocity_q2": 0,
            "q27_resilience_text": (
                "When my income fell, I reduced expenses, found extra work, "
                "and made a repayment plan."
            ),
        },
        "behavioral": {
            "avg_response_time_ms": 5200.0,
            "answer_change_rate": 0.08,
            "session_duration_sec": 410.0,
            "dropout_count": 0,
            "scroll_hesitation_score": 0.52,
            "risk_response_speed_ratio": 0.85,
            "time_of_day": "afternoon",
            "device_type": "mobile",
            "typing_speed_wpm": 34.0,
        },
    }


def test_valid_score_request_payload_parses_successfully() -> None:
    request = ScoreRequest.model_validate(build_valid_score_request_payload())

    assert request.answers.numeracy_q1 == 6600
    assert request.behavioral.time_of_day == "afternoon"
    assert request.behavioral.device_type == "mobile"
    assert request.session_id


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("time_of_day", "late_night"),
        ("device_type", "smart_tv"),
    ],
)
def test_invalid_categorical_behavioral_values_are_rejected(
    field_name: str, bad_value: str
) -> None:
    payload = build_valid_score_request_payload()
    payload["behavioral"][field_name] = bad_value

    with pytest.raises(ValidationError):
        ScoreRequest.model_validate(payload)


def test_score_request_schema_excludes_protected_attributes() -> None:
    payload = build_valid_score_request_payload()
    payload["answers"]["gender"] = "female"

    assert "gender" not in ScoreRequest.model_fields
    assert "gender" not in AnswerPayload.model_fields

    with pytest.raises(ValidationError):
        ScoreRequest.model_validate(payload)


def test_score_response_serializes_expected_top_level_fields() -> None:
    response = ScoreResponse.model_validate(
        {
            "session_id": "123e4567-e89b-12d3-a456-426614174000",
            "credit_score": 712,
            "risk_band": "good",
            "repayment_probability": 0.7314,
            "percentile": 68,
            "explanation": [
                {
                    "feature": "future_orientation",
                    "display_name": "Future Orientation",
                    "shap_value": 0.082,
                    "direction": "positive",
                    "feature_value": 0.91,
                    "plain_language": "Future-oriented choices increased the score.",
                }
            ],
            "counterfactual_actions": [
                {
                    "feature": "numeracy_score",
                    "current_value": 0.66,
                    "suggested_value": 0.85,
                    "estimated_score_gain": 24,
                    "plain_language": (
                        "Improving financial math accuracy could move the score upward."
                    ),
                }
            ],
            "loan_eligibility": {
                "band": "good",
                "amount_min": 10000,
                "amount_max": 30000,
                "description": (
                    "Eligible for a moderate starter loan subject to lender policy."
                ),
            },
            "improvement_tips": [
                {
                    "feature": "numeracy_score",
                    "title": "Strengthen financial math",
                    "body": (
                        "Practice interest, discount, and savings calculations before "
                        "applying again."
                    ),
                }
            ],
            "timestamp": datetime(2026, 5, 13, tzinfo=timezone.utc),
        }
    )

    serialized = response.model_dump(mode="json")

    assert set(serialized) == {
        "session_id",
        "credit_score",
        "risk_band",
        "repayment_probability",
        "percentile",
        "explanation",
        "counterfactual_actions",
        "loan_eligibility",
        "improvement_tips",
        "timestamp",
    }


def test_error_response_matches_documented_wrapper_shape() -> None:
    error = ErrorResponse.model_validate(
        {
            "error": {
                "code": "SCORING_FAILED",
                "message": "Human readable error",
                "details": {},
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": datetime(2026, 5, 13, tzinfo=timezone.utc),
            }
        }
    )

    assert set(error.model_dump(mode="json")) == {"error"}
