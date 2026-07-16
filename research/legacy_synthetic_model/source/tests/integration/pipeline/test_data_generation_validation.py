import pandas as pd

from backend.ml.data_generation.generator import (
    DEFAULT_ROW_COUNT,
    TEMPORAL_SPLIT_MONTHS,
    generate_synthetic_dataset,
)
from backend.ml.data_generation.validators import validate_synthetic_dataset
from backend.ml.nlp.extractor import RAW_TEXT_RESPONSE_COLUMN
from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    PROTECTED_FEATURES,
    RAW_BROWSER_TELEMETRY_FIELDS,
    TARGET,
    TEMPORAL_METADATA,
)


def test_generated_dataset_passes_required_validation_checks() -> None:
    dataset = generate_synthetic_dataset()

    summary = validate_synthetic_dataset(dataset)

    assert summary["row_count"] == DEFAULT_ROW_COUNT
    assert 0.30 <= summary["default_rate"] <= 0.45
    assert summary["test_rows"] >= 1_000
    assert summary["month_count"] == 12


def test_generator_is_deterministic_for_fixed_seed() -> None:
    pd.testing.assert_frame_equal(
        generate_synthetic_dataset(seed=7),
        generate_synthetic_dataset(seed=7),
    )


def test_generated_dataset_includes_required_audit_and_answer_columns() -> None:
    dataset = generate_synthetic_dataset(row_count=512, seed=13)
    required_columns = {
        *ALL_MODEL_FEATURES,
        *PROTECTED_FEATURES,
        *TEMPORAL_METADATA,
        TARGET,
        RAW_TEXT_RESPONSE_COLUMN,
    }

    assert required_columns.issubset(dataset.columns)
    assert dataset[RAW_TEXT_RESPONSE_COLUMN].str.len().min() > 10


def test_temporal_split_intent_matches_documented_months() -> None:
    assert TEMPORAL_SPLIT_MONTHS == {
        "train": tuple(range(1, 9)),
        "validation": (9, 10),
        "test": (11, 12),
    }


def test_synthetic_target_and_model_registry_are_answer_only() -> None:
    dataset = generate_synthetic_dataset()

    assert dataset["numeracy_score"].corr(dataset[TARGET]) > 0.25
    assert dataset["CRT_score"].corr(dataset[TARGET]) > 0.20
    assert dataset["financial_literacy_score"].corr(dataset[TARGET]) > 0.20
    assert set(RAW_BROWSER_TELEMETRY_FIELDS).isdisjoint(ALL_MODEL_FEATURES)

    low_numeracy = dataset[
        dataset["numeracy_score"] <= dataset["numeracy_score"].quantile(0.2)
    ][TARGET].mean()
    high_numeracy = dataset[
        dataset["numeracy_score"] >= dataset["numeracy_score"].quantile(0.8)
    ][TARGET].mean()
    assert high_numeracy > low_numeracy


def test_protected_attributes_remain_outside_all_model_features() -> None:
    assert set(PROTECTED_FEATURES).isdisjoint(ALL_MODEL_FEATURES)
