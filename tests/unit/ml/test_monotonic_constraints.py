import pandas as pd

from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES
from backend.ml.training.classical.monotonic_constraints import (
    MONOTONIC_TREE_ACTIVE_FEATURES,
    MONOTONIC_TREE_MASKED_FEATURES,
    apply_monotonic_tree_feature_masking,
    build_monotonic_constraint_vector,
    neutralize_operational_metadata_for_training,
)


def test_build_monotonic_constraint_vector_matches_feature_registry_length() -> None:
    constraints = build_monotonic_constraint_vector()

    assert len(constraints) == len(ALL_MODEL_FEATURES)
    assert constraints[ALL_MODEL_FEATURES.index("numeracy_score")] == 1
    assert constraints[ALL_MODEL_FEATURES.index("scroll_hesitation_score")] == -1
    assert constraints[ALL_MODEL_FEATURES.index("device_type")] == 0


def test_monotonic_tree_active_features_exclude_masked_and_operational_inputs() -> None:
    assert "device_type" not in MONOTONIC_TREE_ACTIVE_FEATURES
    assert "time_of_day" not in MONOTONIC_TREE_ACTIVE_FEATURES
    assert not set(MONOTONIC_TREE_ACTIVE_FEATURES) & set(MONOTONIC_TREE_MASKED_FEATURES)


def test_neutralize_operational_metadata_for_training_sets_canonical_values() -> None:
    frame = pd.DataFrame(
        {
            "device_type": ["desktop", "tablet"],
            "time_of_day": ["night", "morning"],
        }
    )

    neutralized = neutralize_operational_metadata_for_training(frame)

    assert neutralized["device_type"].tolist() == ["mobile", "mobile"]
    assert neutralized["time_of_day"].tolist() == ["afternoon", "afternoon"]


def test_apply_monotonic_tree_feature_masking_uses_train_medians() -> None:
    frame = pd.DataFrame(
        {
            "psychological_credit_index": [0.2, 0.6, 0.9],
            "engagement_score": [0.1, 0.4, 0.8],
            "text_semantic_dim1": [1.0, 2.0, 3.0],
        }
    )
    train_mask = pd.Series([True, True, False])

    masked, replacements = apply_monotonic_tree_feature_masking(
        frame,
        train_mask=train_mask,
        masked_features=(
            "psychological_credit_index",
            "engagement_score",
            "text_semantic_dim1",
        ),
    )

    assert masked["psychological_credit_index"].tolist() == [0.4, 0.4, 0.4]
    assert masked["engagement_score"].tolist() == [0.25, 0.25, 0.25]
    assert masked["text_semantic_dim1"].tolist() == [1.5, 1.5, 1.5]
    assert replacements == {
        "psychological_credit_index": 0.4,
        "engagement_score": 0.25,
        "text_semantic_dim1": 1.5,
    }
