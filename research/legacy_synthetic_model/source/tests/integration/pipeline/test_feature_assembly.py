from copy import deepcopy

import numpy as np

from backend.app.schemas.score import ScoreRequest
from backend.ml.inference.feature_assembly import (
    assemble_feature_frame,
    assemble_request_features,
)
from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    PROTECTED_FEATURES,
    RAW_BROWSER_TELEMETRY_FIELDS,
    TARGET,
    TEMPORAL_METADATA,
)
from backend.ml.preprocessing.pipeline import fit_preprocessor, transform_features


def test_assembly_builds_a_canonical_answer_only_feature_frame() -> None:
    assembled = assemble_request_features(_build_score_requests()[0])

    assert list(assembled.feature_row) == ALL_MODEL_FEATURES
    assert assembled.feature_frame.columns.tolist() == ALL_MODEL_FEATURES
    assert set(PROTECTED_FEATURES).isdisjoint(assembled.feature_frame.columns)
    assert set(TEMPORAL_METADATA).isdisjoint(assembled.feature_frame.columns)
    assert TARGET not in assembled.feature_frame.columns
    assert set(RAW_BROWSER_TELEMETRY_FIELDS).isdisjoint(assembled.feature_row)
    assert assembled.text_quality.status == "substantive"


def test_assembly_keeps_raw_browser_data_diagnostic_only() -> None:
    baseline = _build_score_requests()[2]
    variant_payload = baseline.model_dump()
    variant_payload["behavioral"] = {
        "avg_response_time_ms": 100.0,
        "answer_change_rate": 1.0,
        "session_duration_sec": 0.0,
        "dropout_count": 20,
        "scroll_hesitation_score": 1.0,
        "risk_response_speed_ratio": 5.0,
        "time_of_day": "night",
        "device_type": "tablet",
        "typing_speed_wpm": 200.0,
    }
    for answer in variant_payload["answers"].values():
        if isinstance(answer, dict) and "first_click_ms" in answer:
            answer["first_click_ms"] = 0
            answer["change_count"] = 50
    variant = ScoreRequest.model_validate(variant_payload)

    baseline_assembled = assemble_request_features(baseline)
    variant_assembled = assemble_request_features(variant)

    assert baseline_assembled.feature_row == variant_assembled.feature_row
    assert baseline_assembled.raw_behavioral_features != variant_assembled.raw_behavioral_features
    assert variant_assembled.raw_behavioral_features["device_type"] == "tablet"


def test_legacy_text_pca_arguments_are_score_inert_for_compatibility() -> None:
    request = _build_score_requests()[0]

    without_pca = assemble_request_features(request)
    with_unused_pca = assemble_request_features(
        request,
        text_pca=object(),
        require_text_pca=True,
    )

    assert with_unused_pca.feature_row == without_pca.feature_row
    assert with_unused_pca.text_quality == without_pca.text_quality


def test_assembled_answer_features_flow_into_preprocessing_transform() -> None:
    requests = _build_score_requests()
    train_frame = assemble_feature_frame(requests[:2])
    score_frame = assemble_feature_frame(requests[2:])

    preprocessor = fit_preprocessor(train_frame)
    transformed = transform_features(preprocessor, score_frame)

    assert train_frame.columns.tolist() == ALL_MODEL_FEATURES
    assert score_frame.columns.tolist() == ALL_MODEL_FEATURES
    assert transformed.shape == (1, len(ALL_MODEL_FEATURES))
    assert not np.isnan(transformed).any()


def _build_score_requests() -> list[ScoreRequest]:
    payloads = [
        {
            "answers": _base_answers()
            | {
                "open_response_text": (
                    "When income fell, I cut expenses, found extra work, and made a repayment plan."
                ),
            },
            "behavioral": _base_behavioral(),
        },
        {
            "answers": _base_answers()
            | {
                "scenario_s1": _scenario("s1_a", "s1_b"),
                "open_response_text": (
                    "I felt stuck at first, but I asked for help and started budgeting more carefully."
                ),
            },
            "behavioral": _base_behavioral() | {"device_type": "desktop"},
        },
        {
            "answers": _base_answers()
            | {
                "CRT_q1": 10,
                "honesty_trap_q1": 5,
                "open_response_text": (
                    "Things fell apart and I felt stuck before I planned steps to recover and repaid urgent bills."
                ),
            },
            "behavioral": _base_behavioral() | {"device_type": "tablet"},
        },
    ]
    return [ScoreRequest.model_validate(deepcopy(payload)) for payload in payloads]


def _scenario(primary: str, least: str) -> dict[str, int | str]:
    return {
        "primary": primary,
        "least": least,
        "first_click_ms": 4_000,
        "change_count": 0,
    }


def _base_answers() -> dict[str, int | float | str | dict[str, int | str]]:
    return {
        "numeracy_q1": 6600,
        "numeracy_q2": 1120,
        "financial_literacy_q1": 1,
        "CRT_q1": 5,
        "CRT_q2": 47,
        "scenario_s1": _scenario("s1_b", "s1_a"),
        "scenario_s2": _scenario("s2_b", "s2_d"),
        "scenario_s3": _scenario("s3_b", "s3_d"),
        "scenario_s4": _scenario("s4_b", "s4_c"),
        "scenario_s5": _scenario("s5_b", "s5_a"),
        "scenario_s6": _scenario("s6_c", "s6_a"),
        "honesty_trap_q1": 2,
        "scenario_s8": _scenario("s8_b", "s8_a"),
        "open_response_text": (
            "I reduced expenses, found extra work, paid urgent bills, and planned repayments carefully."
        ),
    }


def _base_behavioral() -> dict[str, float | int | str]:
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
