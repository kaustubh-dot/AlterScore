import numpy as np

from backend.ml.nlp.extractor import (
    RAW_EMBEDDING_DIM,
    SENTENCE_TRANSFORMER_MODEL_NAME,
    SPACY_MODEL_NAME,
    extract_nlp_feature_batch,
    extract_nlp_features,
    extract_raw_text_embedding,
)


def test_model_names_are_pinned_to_prd_choices() -> None:
    assert SENTENCE_TRANSFORMER_MODEL_NAME == "all-MiniLM-L6-v2"
    assert SPACY_MODEL_NAME == "en_core_web_sm"


def test_empty_text_returns_neutral_defaults() -> None:
    result = extract_nlp_features("")

    assert result["text_sentiment_compound"] == 0.0
    assert result["text_agency_score"] == 0.3
    assert result["text_problem_solving_flag"] == 0.0
    np.testing.assert_array_equal(result["_embedding_raw"], np.zeros(RAW_EMBEDDING_DIM))


def test_high_agency_text_scores_above_low_agency_text() -> None:
    high_agency_result = extract_nlp_features(
        "When I lost my job in 2021, I immediately started budgeting strictly and "
        "found freelance work within 2 weeks. I learned that I can handle crisis "
        "if I act fast."
    )
    low_agency_result = extract_nlp_features(
        "Bad things kept happening and I was unable to do anything. Everything "
        "just fell apart and I had no choice but to give up."
    )

    assert high_agency_result["text_agency_score"] > 0.3
    assert high_agency_result["text_problem_solving_flag"] > 0.8
    assert isinstance(high_agency_result["text_sentiment_compound"], float)

    assert low_agency_result["text_agency_score"] < 0.2
    assert low_agency_result["text_sentiment_compound"] < 0.0
    assert (
        high_agency_result["text_agency_score"] > low_agency_result["text_agency_score"]
    )


def test_problem_solving_keywords_trigger_flag() -> None:
    result = extract_nlp_features(
        "I made a plan, reduced expenses, asked for help, and budgeted carefully "
        "until I recovered."
    )

    assert result["text_problem_solving_flag"] == 1.0


def test_raw_embedding_is_deterministic_and_has_expected_shape() -> None:
    first_embedding = extract_raw_text_embedding(
        "I built a repayment plan and found extra work."
    )
    second_embedding = extract_raw_text_embedding(
        "I built a repayment plan and found extra work."
    )

    assert first_embedding.shape == (RAW_EMBEDDING_DIM,)
    np.testing.assert_allclose(first_embedding, second_embedding)
    assert np.linalg.norm(first_embedding) > 0.0


def test_batch_extraction_returns_feature_rows_and_embeddings() -> None:
    feature_rows, embeddings = extract_nlp_feature_batch(
        [
            "I adjusted my budget and learned to manage cash flow better.",
            "I felt stuck and gave up after everything fell apart.",
        ]
    )

    assert len(feature_rows) == 2
    assert embeddings.shape == (2, RAW_EMBEDDING_DIM)
    assert set(feature_rows[0]) == {
        "text_sentiment_compound",
        "text_agency_score",
        "text_problem_solving_flag",
    }


def test_batch_extraction_handles_empty_input() -> None:
    feature_rows, embeddings = extract_nlp_feature_batch([])

    assert feature_rows == []
    assert embeddings.shape == (0, RAW_EMBEDDING_DIM)
