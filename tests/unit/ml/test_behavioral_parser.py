import pytest

from backend.app.schemas.score import BehavioralPayload
from backend.ml.features.behavioral_parser import BEHAVIORAL_FEATURES, parse_behavioral


def test_parse_behavioral_returns_all_expected_behavioral_feature_keys() -> None:
    features = parse_behavioral(_base_behavioral_payload())

    assert list(features) == BEHAVIORAL_FEATURES
    assert features["device_type"] == "mobile"
    assert features["time_of_day"] == "afternoon"


def test_parse_behavioral_clips_numeric_values_to_documented_bounds() -> None:
    features = parse_behavioral(
        _base_behavioral_payload()
        | {
            "avg_response_time_ms": -50,
            "answer_change_rate": 2.0,
            "session_duration_sec": 9000,
            "dropout_count": 40,
            "scroll_hesitation_score": -0.5,
            "risk_response_speed_ratio": 9.0,
            "typing_speed_wpm": 250,
        }
    )

    assert features["avg_response_time_ms"] == 100.0
    assert features["answer_change_rate"] == 1.0
    assert features["session_duration_sec"] == 7200.0
    assert features["dropout_count"] == 20
    assert features["scroll_hesitation_score"] == 0.0
    assert features["risk_response_speed_ratio"] == 5.0
    assert features["typing_speed_wpm"] == 200.0


def test_parse_behavioral_accepts_pydantic_payloads() -> None:
    payload = BehavioralPayload.model_validate(_base_behavioral_payload())

    features = parse_behavioral(payload)

    assert features["avg_response_time_ms"] == 5200.0
    assert features["typing_speed_wpm"] == 34.0


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("device_type", "smart_tv"),
        ("time_of_day", "late_night"),
    ],
)
def test_parse_behavioral_rejects_unknown_categories(
    field_name: str, bad_value: str
) -> None:
    payload = _base_behavioral_payload() | {field_name: bad_value}

    with pytest.raises(ValueError):
        parse_behavioral(payload)


def _base_behavioral_payload() -> dict[str, float | int | str]:
    return {
        "avg_response_time_ms": 5200.0,
        "answer_change_rate": 0.08,
        "session_duration_sec": 410.0,
        "dropout_count": 0,
        "scroll_hesitation_score": 0.52,
        "risk_response_speed_ratio": 0.85,
        "time_of_day": "afternoon",
        "device_type": "mobile",
        "typing_speed_wpm": 34.0,
    }
