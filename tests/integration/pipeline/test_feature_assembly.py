import numpy as np

from backend.app.schemas.score import ScoreRequest
from backend.ml.inference.feature_assembly import (
    assemble_feature_frame,
    assemble_request_features,
)
from backend.ml.nlp.extractor import extract_raw_text_embedding
from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    PROTECTED_FEATURES,
    TARGET,
    TEMPORAL_METADATA,
)
from backend.ml.preprocessing.pipeline import fit_preprocessor, fit_text_pca, transform_features


def test_assemble_request_features_builds_canonical_feature_frame_with_train_fitted_pca() -> None:
    requests = _build_score_requests()
    train_embeddings = np.vstack(
        [
            extract_raw_text_embedding(request.answers.q27_resilience_text)
            for request in requests[:2]
        ]
    )
    text_pca = fit_text_pca(train_embeddings)

    assembled = assemble_request_features(
        requests[2],
        text_pca=text_pca,
        require_text_pca=True,
    )

    expected_projection = text_pca.transform(assembled.raw_embedding.reshape(1, -1))[0]

    assert list(assembled.feature_row) == ALL_MODEL_FEATURES
    assert assembled.feature_frame.columns.tolist() == ALL_MODEL_FEATURES
    assert set(PROTECTED_FEATURES).isdisjoint(assembled.feature_frame.columns)
    assert set(TEMPORAL_METADATA).isdisjoint(assembled.feature_frame.columns)
    assert TARGET not in assembled.feature_frame.columns
    assert "behavioral_trust_score" in assembled.feature_row

    np.testing.assert_allclose(
        [
            assembled.nlp_features["text_semantic_dim1"],
            assembled.nlp_features["text_semantic_dim2"],
        ],
        expected_projection,
    )


def test_assemble_request_features_neutralizes_device_and_time_inputs_for_model_scoring() -> None:
    requests = _build_score_requests()
    train_embeddings = np.vstack(
        [
            extract_raw_text_embedding(request.answers.q27_resilience_text)
            for request in requests[:2]
        ]
    )
    text_pca = fit_text_pca(train_embeddings)

    assembled = assemble_request_features(
        requests[2],
        text_pca=text_pca,
        require_text_pca=True,
    )

    assert assembled.raw_behavioral_features["device_type"] == "tablet"
    assert assembled.raw_behavioral_features["time_of_day"] == "evening"
    assert assembled.behavioral_features["device_type"] == "mobile"
    assert assembled.behavioral_features["time_of_day"] == "afternoon"
    assert assembled.feature_row["device_type"] == "mobile"
    assert assembled.feature_row["time_of_day"] == "afternoon"


def test_assembled_request_features_flow_into_preprocessing_transform() -> None:
    requests = _build_score_requests()
    train_embeddings = np.vstack(
        [
            extract_raw_text_embedding(request.answers.q27_resilience_text)
            for request in requests[:2]
        ]
    )
    text_pca = fit_text_pca(train_embeddings)

    train_frame = assemble_feature_frame(
        requests[:2],
        text_pca=text_pca,
        require_text_pca=True,
    )
    score_frame = assemble_feature_frame(
        requests[2:],
        text_pca=text_pca,
        require_text_pca=True,
    )

    preprocessor = fit_preprocessor(train_frame)
    transformed = transform_features(preprocessor, score_frame)

    assert train_frame.columns.tolist() == ALL_MODEL_FEATURES
    assert score_frame.columns.tolist() == ALL_MODEL_FEATURES
    assert transformed.shape == (1, len(ALL_MODEL_FEATURES))
    assert not np.isnan(transformed).any()


def test_assemble_request_features_can_require_train_fitted_text_pca() -> None:
    request = _build_score_requests()[0]

    try:
        assemble_request_features(request, require_text_pca=True)
    except ValueError as exc:
        assert "text_pca" in str(exc)
    else:
        raise AssertionError("Expected require_text_pca=True to reject a missing PCA artifact.")


def _build_score_requests() -> list[ScoreRequest]:
    payloads = [
        {
            "answers": _base_answers()
            | {
                "q27_resilience_text": (
                    "When income fell, I cut expenses, found extra work, and "
                    "made a repayment plan."
                ),
            },
            "behavioral": _base_behavioral()
            | {
                "avg_response_time_ms": 4900.0,
                "typing_speed_wpm": 35.0,
                "device_type": "mobile",
                "time_of_day": "afternoon",
            },
        },
        {
            "answers": _base_answers()
            | {
                "future_orient_q1": 0,
                "future_orient_q2": 0,
                "future_orient_q3": 2,
                "q27_resilience_text": (
                    "I felt stuck at first, but I asked for help and started "
                    "budgeting more carefully."
                ),
            },
            "behavioral": _base_behavioral()
            | {
                "avg_response_time_ms": 6100.0,
                "answer_change_rate": 0.14,
                "typing_speed_wpm": 29.0,
                "device_type": "desktop",
                "time_of_day": "morning",
            },
        },
        {
            "answers": _base_answers()
            | {
                "CRT_q1": 10,
                "honesty_trap_q1": 5,
                "honesty_trap_q2": 5,
                "q27_resilience_text": (
                    "Things fell apart and I felt stuck before I made a plan "
                    "to recover."
                ),
            },
            "behavioral": _base_behavioral()
            | {
                "avg_response_time_ms": 7000.0,
                "answer_change_rate": 0.22,
                "risk_response_speed_ratio": 1.4,
                "typing_speed_wpm": 24.0,
                "device_type": "tablet",
                "time_of_day": "evening",
            },
        },
    ]
    return [ScoreRequest.model_validate(payload) for payload in payloads]


def _base_answers() -> dict[str, int | float | str]:
    return {
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
        "risk_q1": 1,
        "risk_q2": 1,
        "locus_q1": 0,
        "locus_q2": 0,
        "locus_q3": 4,
        "social_capital_q1": 2,
        "social_capital_q2": 0,
        "social_capital_q3": 0,
        "resilience_q1": 4,
        "resilience_q2": 4,
        "resilience_q3": 0,
        "loss_aversion_q1": 0,
        "honesty_trap_q1": 2,
        "honesty_trap_q2": 2,
        "future_orient_repeat": 1,
        "locus_repeat": 0,
        "reciprocity_q1": 4,
        "reciprocity_q2": 0,
        "q27_resilience_text": "I reduced expenses and found extra work.",
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
