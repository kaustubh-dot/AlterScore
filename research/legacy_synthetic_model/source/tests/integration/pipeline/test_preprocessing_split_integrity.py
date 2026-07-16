import joblib
import numpy as np
import pandas as pd

from backend.ml.data_generation.generator import (
    TEMPORAL_SPLIT_MONTHS,
    generate_synthetic_dataset,
)
from backend.ml.features.answer_parser import parse_answers
from backend.ml.nlp.extractor import extract_nlp_features
from backend.ml.nlp.extractor import RAW_EMBEDDING_DIM
from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    PROTECTED_FEATURES,
    TARGET,
    TEMPORAL_METADATA,
)
from backend.ml.preprocessing.pipeline import (
    TEXT_PCA_FEATURES,
    apply_text_pca,
    fit_preprocessor,
    fit_text_pca,
    prepare_model_feature_frame,
    prepare_temporal_data,
    transform_features,
)


def test_prepare_temporal_data_uses_documented_splits_and_train_only_text_pca(
    tmp_path,
) -> None:
    dataset = generate_synthetic_dataset(row_count=1_200, seed=11)
    raw_embeddings = _build_embedding_matrix(dataset)

    prepared = prepare_temporal_data(
        dataset,
        raw_text_embeddings=raw_embeddings,
        text_pca_artifact_path=tmp_path / "text_pca.pkl",
    )

    assert prepared.train.cohort_months.max() <= max(TEMPORAL_SPLIT_MONTHS["train"])
    assert prepared.validation.cohort_months.isin(
        TEMPORAL_SPLIT_MONTHS["validation"]
    ).all()
    assert prepared.test.cohort_months.min() >= min(TEMPORAL_SPLIT_MONTHS["test"])

    assert prepared.train.indices.intersection(prepared.validation.indices).empty
    assert prepared.train.indices.intersection(prepared.test.indices).empty
    assert prepared.validation.indices.intersection(prepared.test.indices).empty
    assert len(prepared.train.indices) + len(prepared.validation.indices) + len(
        prepared.test.indices
    ) == len(dataset)

    assert prepared.train.X.columns.tolist() == ALL_MODEL_FEATURES
    assert prepared.validation.X.columns.tolist() == ALL_MODEL_FEATURES
    assert prepared.test.X.columns.tolist() == ALL_MODEL_FEATURES
    assert set(PROTECTED_FEATURES).isdisjoint(prepared.train.X.columns)
    assert set(TEMPORAL_METADATA).isdisjoint(prepared.train.X.columns)
    assert TARGET not in prepared.train.X.columns

    train_embeddings = raw_embeddings[prepared.train.indices.to_numpy()]
    np.testing.assert_allclose(prepared.text_pca.mean_, train_embeddings.mean(axis=0))
    assert not np.allclose(prepared.text_pca.mean_, raw_embeddings.mean(axis=0))
    assert (tmp_path / "text_pca.pkl").is_file()
    loaded_text_pca = joblib.load(tmp_path / "text_pca.pkl")
    np.testing.assert_allclose(
        loaded_text_pca.components_, prepared.text_pca.components_
    )

    assert set(TEXT_PCA_FEATURES).isdisjoint(prepared.train.X.columns)


def test_fit_preprocessor_transforms_all_splits_and_imputes_missing_values(
    tmp_path,
) -> None:
    dataset = generate_synthetic_dataset(row_count=1_200, seed=29)
    raw_embeddings = _build_embedding_matrix(dataset)
    prepared = prepare_temporal_data(dataset, raw_text_embeddings=raw_embeddings)

    train_features = prepared.train.X.copy()
    validation_features = prepared.validation.X.copy()
    test_features = prepared.test.X.copy()

    train_features.iloc[0, train_features.columns.get_loc("numeracy_score")] = np.nan
    train_features.iloc[1, train_features.columns.get_loc("CRT_score")] = np.nan
    validation_features.iloc[0, validation_features.columns.get_loc("honesty_score")] = np.nan
    test_features.iloc[0, test_features.columns.get_loc("resilience_score")] = np.nan

    preprocessor = fit_preprocessor(
        train_features,
        artifact_path=tmp_path / "preprocessor.pkl",
    )

    transformed_train = transform_features(preprocessor, train_features)
    transformed_validation = transform_features(preprocessor, validation_features)
    transformed_test = transform_features(preprocessor, test_features)

    expected_feature_count = len(ALL_MODEL_FEATURES)
    assert transformed_train.shape == (len(train_features), expected_feature_count)
    assert transformed_validation.shape == (
        len(validation_features),
        expected_feature_count,
    )
    assert transformed_test.shape == (len(test_features), expected_feature_count)
    assert not np.isnan(transformed_train).any()
    assert not np.isnan(transformed_validation).any()
    assert not np.isnan(transformed_test).any()

    assert (tmp_path / "preprocessor.pkl").is_file()
    loaded_preprocessor = joblib.load(tmp_path / "preprocessor.pkl")
    loaded_transform = transform_features(loaded_preprocessor, validation_features)
    np.testing.assert_allclose(loaded_transform, transformed_validation)


def test_answer_parser_and_derived_features_flow_into_preprocessing() -> None:
    feature_rows = []
    raw_embeddings = []
    for response_time_ms, device_type, time_of_day, text, answer_overrides in [
        (
            5200.0,
            "mobile",
            "afternoon",
            "I reduced expenses, found extra work, and made a repayment plan.",
            {},
        ),
        (
            6100.0,
            "desktop",
            "morning",
            "I started budgeting more carefully and asked for help early.",
            {
                "numeracy_q1": 6500,
            },
        ),
        (
            7000.0,
            "mobile",
            "evening",
            "Things fell apart and I felt stuck before I made a plan.",
            {
                "CRT_q1": 10,
                "honesty_trap_q1": 4,
            },
        ),
    ]:
        answers = _answer_payload() | answer_overrides
        psychometric_features = parse_answers(answers)
        nlp_features = extract_nlp_features(text)
        raw_embeddings.append(np.asarray(nlp_features["_embedding_raw"], dtype=float))
        feature_rows.append(
            {
                **psychometric_features,
                **{
                    "avg_response_time_ms": response_time_ms,
                    "answer_change_rate": 0.08,
                    "session_duration_sec": response_time_ms / 12.0,
                    "dropout_count": 0.0,
                    "scroll_hesitation_score": 0.58,
                    "risk_response_speed_ratio": 0.85,
                    "typing_speed_wpm": 33.0,
                    "device_type": device_type,
                    "time_of_day": time_of_day,
                },
                **{
                    key: value
                    for key, value in nlp_features.items()
                    if key != "_embedding_raw"
                },
            }
        )

    raw_embedding_matrix = np.vstack(raw_embeddings)
    text_pca = fit_text_pca(raw_embedding_matrix)
    feature_frame = apply_text_pca(
        pd.DataFrame(feature_rows), raw_embedding_matrix, text_pca
    )
    feature_frame = prepare_model_feature_frame(feature_frame)
    preprocessor = fit_preprocessor(feature_frame)
    transformed = transform_features(preprocessor, feature_frame)

    assert feature_frame.columns.tolist() == ALL_MODEL_FEATURES
    assert transformed.shape == (3, len(ALL_MODEL_FEATURES))


def _build_embedding_matrix(dataset) -> np.ndarray:
    embeddings = np.zeros((len(dataset), RAW_EMBEDDING_DIM), dtype=float)
    row_index = np.arange(len(dataset), dtype=float)
    cohort_months = dataset["cohort_month"].to_numpy(dtype=float)

    embeddings[:, 0] = cohort_months * 10.0
    embeddings[:, 1] = dataset["text_agency_score"].to_numpy(dtype=float) * 3.0
    embeddings[:, 2] = dataset["text_sentiment_compound"].to_numpy(dtype=float) * 2.0
    embeddings[:, 3] = dataset[TARGET].to_numpy(dtype=float)
    embeddings[:, 4] = row_index / max(len(dataset) - 1, 1)

    return embeddings


def _answer_payload() -> dict[str, int | float | str | dict]:
    def _scenario(opt):
        return {
            "primary": opt,
            "least": None,
            "first_click_ms": 4000,
            "change_count": 0,
        }

    return {
        "numeracy_q1": 6600,
        "numeracy_q2": 1120,
        "financial_literacy_q1": 1,
        "CRT_q1": 5,
        "CRT_q2": 47,
        "scenario_s1": _scenario("s1_b"),
        "scenario_s2": _scenario("s2_b"),
        "scenario_s3": _scenario("s3_b"),
        "scenario_s4": _scenario("s4_b"),
        "scenario_s5": _scenario("s5_b"),
        "scenario_s6": _scenario("s6_c"),
        "honesty_trap_q1": 2,
        "scenario_s8": _scenario("s8_b"),
        "open_response_text": "I reduced expenses and found extra work.",
    }
