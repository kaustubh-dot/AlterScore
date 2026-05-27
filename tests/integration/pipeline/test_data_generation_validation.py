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
    first_dataset = generate_synthetic_dataset(seed=7)
    second_dataset = generate_synthetic_dataset(seed=7)

    pd.testing.assert_frame_equal(first_dataset, second_dataset)


def test_generated_dataset_includes_model_audit_temporal_and_target_columns() -> None:
    dataset = generate_synthetic_dataset(row_count=512, seed=13)
    expected_columns = [
        *ALL_MODEL_FEATURES,
        *PROTECTED_FEATURES,
        *TEMPORAL_METADATA,
        TARGET,
        RAW_TEXT_RESPONSE_COLUMN,
    ]

    assert dataset.columns.tolist() == expected_columns
    assert dataset[RAW_TEXT_RESPONSE_COLUMN].str.len().min() > 10


def test_temporal_split_intent_matches_documented_months() -> None:
    assert TEMPORAL_SPLIT_MONTHS == {
        "train": tuple(range(1, 9)),
        "validation": (9, 10),
        "test": (11, 12),
    }


def test_later_cohorts_are_faster_and_have_higher_typing_speed_on_average() -> None:
    dataset = generate_synthetic_dataset()
    early_cohorts = dataset[dataset["cohort_month"].between(1, 4)]
    later_cohorts = dataset[dataset["cohort_month"].between(9, 12)]

    assert (
        later_cohorts["avg_response_time_ms"].mean()
        < early_cohorts["avg_response_time_ms"].mean()
    )
    assert (
        later_cohorts["typing_speed_wpm"].mean()
        > early_cohorts["typing_speed_wpm"].mean()
    )


def test_repaired_synthetic_supervision_matches_behavioral_directionality() -> None:
    dataset = generate_synthetic_dataset()

    assert dataset["scroll_hesitation_score"].corr(dataset[TARGET]) < -0.25
    assert dataset["engagement_score"].corr(dataset[TARGET]) > 0.25

    low_hesitation = dataset[
        dataset["scroll_hesitation_score"]
        <= dataset["scroll_hesitation_score"].quantile(0.2)
    ][TARGET].mean()
    high_hesitation = dataset[
        dataset["scroll_hesitation_score"]
        >= dataset["scroll_hesitation_score"].quantile(0.8)
    ][TARGET].mean()
    assert low_hesitation > high_hesitation

    device_repayment_rates = dataset.groupby("device_type")[TARGET].mean()
    assert device_repayment_rates.max() - device_repayment_rates.min() < 0.05


def test_protected_attributes_remain_outside_all_model_features() -> None:
    assert set(PROTECTED_FEATURES).isdisjoint(ALL_MODEL_FEATURES)
