from backend.ml.preprocessing.feature_registry import (
    ACTIONABLE_FEATURES,
    ALL_MODEL_FEATURES,
    CATEGORICAL_FEATURES,
    IMMUTABLE_FEATURES,
    NUMERIC_FEATURES,
    PROTECTED_FEATURES,
    TARGET,
    TEMPORAL_METADATA,
)


def test_numeric_feature_count_is_33() -> None:
    assert len(NUMERIC_FEATURES) == 33


def test_categorical_feature_count_is_2() -> None:
    assert len(CATEGORICAL_FEATURES) == 2


def test_total_model_input_count_is_35() -> None:
    assert ALL_MODEL_FEATURES == NUMERIC_FEATURES + CATEGORICAL_FEATURES
    assert len(ALL_MODEL_FEATURES) == 35
    assert len(set(ALL_MODEL_FEATURES)) == 35


def test_protected_attributes_are_not_model_inputs() -> None:
    assert set(PROTECTED_FEATURES).isdisjoint(ALL_MODEL_FEATURES)


def test_temporal_metadata_is_not_model_inputs() -> None:
    assert set(TEMPORAL_METADATA).isdisjoint(ALL_MODEL_FEATURES)


def test_target_is_not_model_input() -> None:
    assert TARGET not in ALL_MODEL_FEATURES


def test_actionable_features_exclude_non_mutable_and_non_numeric_fields() -> None:
    excluded_features = (
        set(PROTECTED_FEATURES)
        | set(TEMPORAL_METADATA)
        | set(CATEGORICAL_FEATURES)
        | set(IMMUTABLE_FEATURES)
    )

    assert set(ACTIONABLE_FEATURES).isdisjoint(excluded_features)
    assert set(ACTIONABLE_FEATURES).issubset(NUMERIC_FEATURES)
