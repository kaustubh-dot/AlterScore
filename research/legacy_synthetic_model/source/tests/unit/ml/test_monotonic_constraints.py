import pandas as pd

from backend.ml.preprocessing.feature_registry import (
    ALL_MODEL_FEATURES,
    RAW_BROWSER_TELEMETRY_FIELDS,
)
from backend.ml.training.classical.monotonic_constraints import (
    MONOTONIC_TREE_ACTIVE_FEATURES,
    MONOTONIC_TREE_MASKED_FEATURES,
    apply_monotonic_tree_feature_masking,
    build_monotonic_constraint_vector,
    neutralize_operational_metadata_for_training,
)


def test_constraint_vector_covers_only_answer_derived_feature_registry() -> None:
    constraints = build_monotonic_constraint_vector()

    assert len(constraints) == len(ALL_MODEL_FEATURES)
    assert constraints[ALL_MODEL_FEATURES.index("numeracy_score")] == 1
    assert constraints[ALL_MODEL_FEATURES.index("honesty_score")] == 1
    assert all(field not in ALL_MODEL_FEATURES for field in RAW_BROWSER_TELEMETRY_FIELDS)


def test_constraint_vector_handles_sklearn_numeric_prefixes() -> None:
    constraints = build_monotonic_constraint_vector(
        ("num__numeracy_score", "num__loss_aversion_score", "num__honesty_score")
    )

    assert constraints == (1, 0, 1)


def test_active_features_are_exactly_the_scored_features() -> None:
    assert MONOTONIC_TREE_ACTIVE_FEATURES == tuple(ALL_MODEL_FEATURES)
    assert MONOTONIC_TREE_MASKED_FEATURES == ()


def test_neutralize_operational_metadata_for_training_is_compatible_but_not_required() -> None:
    frame = pd.DataFrame(
        {"device_type": ["desktop", "tablet"], "time_of_day": ["night", "morning"]}
    )

    neutralized = neutralize_operational_metadata_for_training(frame)

    assert neutralized["device_type"].tolist() == ["mobile", "mobile"]
    assert neutralized["time_of_day"].tolist() == ["afternoon", "afternoon"]


def test_feature_masking_remains_available_for_legacy_offline_callers() -> None:
    frame = pd.DataFrame({"legacy_column": [0.2, 0.6, 0.9]})
    masked, replacements = apply_monotonic_tree_feature_masking(
        frame,
        train_mask=pd.Series([True, True, False]),
        masked_features=("legacy_column",),
    )

    assert masked["legacy_column"].tolist() == [0.4, 0.4, 0.4]
    assert replacements == {"legacy_column": 0.4}
