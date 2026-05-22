import pandas as pd

from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES
from scripts.retrain_tabnet_repair_experiment import (
    apply_tabnet_feature_masking,
    build_monotonic_curriculum_training_set,
    evaluate_counterfactual_acceptance_gate,
    evaluate_monotonic_acceptance_gates,
    parse_feature_list,
    select_hard_pair_candidate_indices,
)


def _sensitivity_payload(values: list[float]) -> dict[str, object]:
    points = [
        {"value": index / (len(values) - 1), "probability": value}
        for index, value in enumerate(values)
    ]
    return {
        "anchor_profile": {},
        "feature_sweeps": {
            "resilience_score": {
                "expected_direction": "increasing",
                "old_tabnet": points,
                "new_tabnet": points,
            }
        },
    }


def test_monotonic_acceptance_gate_passes_materially_increasing_curve() -> None:
    result = evaluate_monotonic_acceptance_gates(
        _sensitivity_payload([0.20, 0.28, 0.35, 0.44, 0.55])
    )

    assert result["passed"] is True


def test_monotonic_acceptance_gate_fails_material_drop() -> None:
    result = evaluate_monotonic_acceptance_gates(
        _sensitivity_payload([0.80, 0.70, 0.62, 0.55, 0.48])
    )

    assert result["passed"] is False
    assert result["results"][0]["endpoint_passed"] is False


def test_parse_feature_list_trims_and_drops_empty_tokens() -> None:
    assert parse_feature_list(" numeracy_score, , resilience_score ,, ") == (
        "numeracy_score",
        "resilience_score",
    )


def test_apply_tabnet_feature_masking_uses_train_median() -> None:
    feature_frame = pd.DataFrame(
        {
            "engagement_score": [0.10, 0.50, 0.90],
            "device_type": ["mobile", "mobile", "desktop"],
        }
    )
    train_mask = pd.Series([True, True, False])

    masked, replacements = apply_tabnet_feature_masking(
        feature_frame,
        train_mask=train_mask,
        masked_features=("engagement_score",),
    )

    assert masked["engagement_score"].tolist() == [0.30, 0.30, 0.30]
    assert replacements == {"engagement_score": 0.30}


def test_curriculum_training_set_adds_monotonic_rows() -> None:
    base_row = {}
    for feature_name in ALL_MODEL_FEATURES:
        if feature_name == "device_type":
            base_row[feature_name] = "mobile"
        elif feature_name == "time_of_day":
            base_row[feature_name] = "afternoon"
        else:
            base_row[feature_name] = 0.5
    base_row["scroll_hesitation_score"] = 0.6
    base_row["resilience_score"] = 0.4
    base_row["future_orientation"] = 0.4
    base_row["numeracy_score"] = 0.4
    train_feature_frame = pd.DataFrame([base_row], columns=ALL_MODEL_FEATURES)

    augmented_frame, augmented_labels, audit = build_monotonic_curriculum_training_set(
        train_feature_frame=train_feature_frame,
        y_train=[1],
        curriculum_features=(
            "resilience_score",
            "future_orientation",
            "numeracy_score",
            "scroll_hesitation_score",
        ),
        repeats=1,
        step=0.1,
        masked_features=(),
        mask_replacements={},
        targeted_counterfactual_step_grid=(0.05, 0.1),
        targeted_strong_threshold=0.7,
        targeted_low_hesitation_threshold=0.3,
    )

    assert len(augmented_frame) == 5
    assert augmented_labels.tolist() == [1, 1, 1, 1, 1]
    assert audit["curriculum_rows_added"] == 4
    assert audit["targeted_rows_added"] == 0


def test_curriculum_training_set_adds_targeted_rows_for_hard_slice() -> None:
    base_row = {}
    for feature_name in ALL_MODEL_FEATURES:
        if feature_name == "device_type":
            base_row[feature_name] = "mobile"
        elif feature_name == "time_of_day":
            base_row[feature_name] = "afternoon"
        else:
            base_row[feature_name] = 0.5
    base_row["resilience_score"] = 0.8
    train_feature_frame = pd.DataFrame([base_row], columns=ALL_MODEL_FEATURES)

    augmented_frame, augmented_labels, audit = build_monotonic_curriculum_training_set(
        train_feature_frame=train_feature_frame,
        y_train=[1],
        curriculum_features=("resilience_score",),
        repeats=1,
        step=0.1,
        masked_features=(),
        mask_replacements={},
        targeted_counterfactual_step_grid=(0.05, 0.1),
        targeted_strong_threshold=0.7,
        targeted_low_hesitation_threshold=0.3,
    )

    assert len(augmented_frame) == 4
    assert augmented_labels.tolist() == [1, 1, 1, 1]
    assert audit["curriculum_rows_added"] == 3
    assert audit["targeted_rows_added"] == 2


def test_curriculum_training_set_supports_collateral_guard_feature() -> None:
    base_row = {}
    for feature_name in ALL_MODEL_FEATURES:
        if feature_name == "device_type":
            base_row[feature_name] = "mobile"
        elif feature_name == "time_of_day":
            base_row[feature_name] = "afternoon"
        else:
            base_row[feature_name] = 0.5
    base_row["text_agency_score"] = 0.85
    train_feature_frame = pd.DataFrame([base_row], columns=ALL_MODEL_FEATURES)

    augmented_frame, augmented_labels, audit = build_monotonic_curriculum_training_set(
        train_feature_frame=train_feature_frame,
        y_train=[1],
        curriculum_features=("text_agency_score",),
        repeats=1,
        step=0.1,
        masked_features=(),
        mask_replacements={},
        targeted_counterfactual_step_grid=(0.05,),
        targeted_strong_threshold=0.7,
        targeted_low_hesitation_threshold=0.3,
    )

    assert len(augmented_frame) == 3
    assert augmented_labels.tolist() == [1, 1, 1]
    assert audit["curriculum_rows_added"] == 2
    assert audit["targeted_rows_added"] == 1


def test_counterfactual_acceptance_gate_blocks_large_violation_rate() -> None:
    result = evaluate_counterfactual_acceptance_gate(
        {
            "feature_results": {
                "resilience_score": {
                    "violation_rate": 0.10,
                    "worst_delta": -0.02,
                }
            }
        },
        max_violation_rate=0.02,
        max_worst_delta=0.05,
    )

    assert result["passed"] is False
    assert result["results"][0]["passed"] is False


def test_select_hard_pair_candidate_indices_prioritizes_resilience_heavy_rows() -> None:
    train_frame = pd.DataFrame(
        {
            "resilience_score": [0.2, 0.9, 0.7, 0.95],
            "scroll_hesitation_score": [0.7, 0.4, 0.2, 0.1],
        }
    )
    positive_indices = pd.Series([0, 1, 2, 3]).to_numpy(dtype=int)

    selected_for_resilience = select_hard_pair_candidate_indices(
        train_frame=train_frame,
        positive_indices=positive_indices,
        feature_name="resilience_score",
        sample_size=2,
    )
    selected_for_hesitation = select_hard_pair_candidate_indices(
        train_frame=train_frame,
        positive_indices=positive_indices,
        feature_name="scroll_hesitation_score",
        sample_size=2,
    )

    assert selected_for_resilience.tolist() == [3, 1]
    assert selected_for_hesitation.tolist() == [3, 2]
