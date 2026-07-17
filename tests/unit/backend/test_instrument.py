"""Phase 1 tests for the canonical, model-independent instrument."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json

import pytest
from pydantic import ValidationError

import backend.app.instrument.canonical as canonical_module
from backend.app.instrument import (
    BEHAVIOR_VALUES,
    OBJECTIVE_GENERATORS,
    InvalidResponse,
    NarrativeConfig,
    ObjectivePresentation,
    UnknownCanonicalId,
    generate_form,
)


def _issued(item) -> dict[str, int]:
    return {value.name: value.value for value in item.issued_values}


def _independent_answer(item) -> int:
    values = _issued(item)
    if item.concept == "cash_flow":
        return values["opening_cash"] + values["inflow"] - values["expenses"]
    if item.concept == "simple_interest":
        return (
            values["principal"]
            * values["annual_rate_percent"]
            * values["term_years"]
            // 100
        )
    if item.concept == "borrowing_cost_comparison":
        total_a = (
            values["principal"]
            + values["principal"]
            * values["offer_a_rate_percent"]
            * values["term_years"]
            // 100
            + values["offer_a_fee"]
        )
        total_b = (
            values["principal"]
            + values["principal"]
            * values["offer_b_rate_percent"]
            * values["term_years"]
            // 100
            + values["offer_b_fee"]
        )
        assert total_a == values["offer_a_total_repayment"]
        assert total_b == values["offer_b_total_repayment"]
        assert total_a != total_b
        return total_b - total_a
    if item.concept == "discount_price":
        return (
            values["marked_price"]
            - values["marked_price"] * values["discount_rate_percent"] // 100
        )
    if item.concept == "inflation_price":
        return values["current_price"] * (100 + values["inflation_rate_percent"]) // 100
    if item.concept == "due_date_shortfall":
        return values["due_amount"] - values["available_amount"]
    if item.concept == "repayment_total":
        interest = (
            values["principal"]
            * values["annual_rate_percent"]
            * values["term_years"]
            // 100
        )
        assert interest == values["interest"]
        return values["principal"] + interest + values["fee"]
    if item.concept == "emergency_buffer":
        return values["monthly_essential_costs"] * values["buffer_months"]
    raise AssertionError(f"uncovered concept: {item.concept}")


def _valid_static_responses(form) -> dict[str, str]:
    return {
        item.presentation_id: item.options[0].option_id
        for item in form.static_sjt_items
    }


def _valid_behavior_responses(form) -> dict[str, str]:
    return {
        item.presentation_id: item.options[0].option_id
        for item in form.behavior_profile_items
    }


def _walk_mappings(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_mappings(child)


def test_registry_contains_eight_objective_generators_and_complete_form() -> None:
    form = generate_form(123)

    assert len(OBJECTIVE_GENERATORS) == 8
    assert len(form.objective_items) == 8
    assert len(form.static_sjt_items) == 4
    assert len(form.behavior_profile_items) == 6
    assert {item.response_kind for item in form.to_public_model().items[:8]} == {
        "integer"
    }
    assert tuple(BEHAVIOR_VALUES) == (
        "Never",
        "Rarely",
        "Sometimes",
        "Often",
        "Always",
        "Not applicable",
    )


def test_thousands_of_seeded_forms_recompute_independently() -> None:
    for seed in range(2048):
        form = generate_form(seed)
        assert len({item.presentation_id for item in form.objective_items}) == 8
        for item in form.objective_items:
            values = _issued(item)
            assert values
            assert all(
                isinstance(value, int) and not isinstance(value, bool)
                for value in values.values()
            )
            assert item.correct_answer == _independent_answer(item)
            assert item.answer_min <= item.correct_answer <= item.answer_max
            assert item.correct_answer >= 0

        borrowing = next(
            item
            for item in form.objective_items
            if item.concept == "borrowing_cost_comparison"
        )
        borrowing_values = _issued(borrowing)
        assert (
            borrowing_values["offer_a_total_repayment"]
            != borrowing_values["offer_b_total_repayment"]
        )


def test_same_seed_is_deterministic_and_distinct_seeds_vary() -> None:
    first = generate_form(777)
    second = generate_form(777)

    assert first.objective_items == second.objective_items
    assert first.static_sjt_items == second.static_sjt_items
    assert first.behavior_profile_items == second.behavior_profile_items
    assert first.serialize_public() == second.serialize_public()

    objective_variants = {
        tuple(
            (item.concept, item.prompt, item.correct_answer)
            for item in generate_form(seed).objective_items
        )
        for seed in range(40)
    }
    assert len(objective_variants) > 1
    for index in range(8):
        assert (
            len(
                {
                    tuple(item.issued_values)
                    for item in (
                        generate_form(seed).objective_items[index] for seed in range(40)
                    )
                }
            )
            > 1
        )


def test_objective_boundaries_are_exact_and_no_tolerance_credit_exists() -> None:
    form = generate_form(88)
    key = form.objective_answer_key()

    assert form.objective_score(key) == Fraction(100, 1)

    all_wrong = {item_id: answer + 1 for item_id, answer in key.items()}
    assert form.objective_score(all_wrong) == Fraction(0, 1)

    one_correct = {item_id: answer + 1 for item_id, answer in key.items()}
    first_id = next(iter(key))
    one_correct[first_id] = key[first_id]
    assert form.objective_score(one_correct) == Fraction(25, 2)


@pytest.mark.parametrize(
    "bad_value",
    [True, False, 1.0, "1", -1, 10_000_001],
)
def test_objective_invalid_or_out_of_range_values_reject(bad_value) -> None:
    form = generate_form(9)
    responses = form.objective_answer_key()
    first_id = next(iter(responses))
    responses[first_id] = bad_value

    with pytest.raises(InvalidResponse):
        form.validate_objective_responses(responses)


@pytest.mark.parametrize("boundary", [0, 10_000_000])
def test_objective_private_integer_bounds_are_inclusive(boundary: int) -> None:
    form = generate_form(9)
    responses = form.objective_answer_key()
    first_id = next(iter(responses))
    responses[first_id] = boundary

    assert form.validate_objective_responses(responses)[first_id] == boundary


def test_unknown_canonical_item_and_option_ids_reject() -> None:
    form = generate_form(21)
    objective_responses = form.objective_answer_key()
    objective_responses["objective_unknown"] = 0
    with pytest.raises(UnknownCanonicalId):
        form.validate_objective_responses(objective_responses)

    static_responses = _valid_static_responses(form)
    first_static = next(iter(static_responses))
    static_responses[first_static] = "sjt01_z"
    with pytest.raises(UnknownCanonicalId):
        form.validate_static_sjt_responses(static_responses)

    behavior_responses = _valid_behavior_responses(form)
    first_behavior = next(iter(behavior_responses))
    behavior_responses[first_behavior] = "behavior_unknown"
    with pytest.raises(UnknownCanonicalId):
        form.validate_behavior_profile(behavior_responses)


def test_static_sjt_normalization_is_exact() -> None:
    form = generate_form(314)
    rubric = form.static_rubric()

    assert set(rubric) == {item.presentation_id for item in form.static_sjt_items}
    for item in form.static_sjt_items:
        points_seen = set()
        for option in item.options:
            responses = _valid_static_responses(form)
            responses[item.presentation_id] = option.option_id
            normalized = form.normalize_static_sjt_responses(responses)
            points = normalized[item.presentation_id]
            points_seen.add(points)
            assert points == rubric[item.presentation_id][option.option_id]
            assert form.static_sjt_score(
                item.presentation_id, option.option_id
            ) == Fraction(100 * points, 3)
        assert points_seen == {0, 1, 2, 3}


def test_static_sjt_partial_credit_tracks_increasing_decision_quality() -> None:
    form = generate_form(314)
    items = {item.presentation_id: item for item in form.static_sjt_items}

    receivable = {option.option_id: option for option in items["static_sjt_01"].options}
    assert receivable["sjt01_d"].rubric_points == 2
    assert "confirm a collection date" in receivable["sjt01_d"].label
    assert "due date passes" not in receivable["sjt01_d"].label

    runway = {option.option_id: option for option in items["static_sjt_03"].options}
    assert runway["sjt03_b"].rubric_points == 1
    assert "loan first" in runway["sjt03_b"].label
    assert runway["sjt03_d"].rubric_points == 2
    assert "30 days" in runway["sjt03_d"].label
    assert runway["sjt03_c"].rubric_points == 3
    assert "Start reducing" in runway["sjt03_c"].label


def test_sanitized_serialization_is_an_exact_public_allowlist() -> None:
    form = generate_form(505)
    payload = form.serialize_public()
    assert set(payload) == {"items", "behavior_profile_items", "narrative"}
    assert len(payload["items"]) == 12
    assert len(payload["behavior_profile_items"]) == 6
    assert set(payload["narrative"]) == {"enabled", "prompt", "max_length"}

    for item in payload["items"][:8]:
        assert set(item) == {
            "presentation_id",
            "item_type",
            "prompt",
            "response_kind",
            "required",
        }
    for item in payload["items"][8:]:
        assert set(item) == {
            "presentation_id",
            "item_type",
            "prompt",
            "response_kind",
            "required",
            "options",
        }
        assert all(set(option) == {"option_id", "label"} for option in item["options"])
    for item in payload["behavior_profile_items"]:
        assert set(item) == {
            "presentation_id",
            "item_type",
            "prompt",
            "response_kind",
            "required",
            "options",
        }
        assert [option["label"] for option in item["options"]] and set(
            option["label"] for option in item["options"]
        ) == set(BEHAVIOR_VALUES)

    forbidden = {
        "answer",
        "correct",
        "key",
        "weight",
        "rubric",
        "point",
        "bound",
        "seed",
        "rule",
        "rationale",
        "feature",
        "artifact",
    }
    for key, _ in _walk_mappings(payload):
        assert not any(token in str(key).lower() for token in forbidden), key
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "10_000_000" not in serialized
    assert "offer_a_total_repayment" not in serialized
    assert "Tests exact" not in serialized

    public_copy = form.serialize_public()
    public_copy["items"][0]["prompt"] = "changed"
    assert form.objective_items[0].prompt != "changed"


def test_public_models_reject_server_only_fields() -> None:
    with pytest.raises(ValidationError):
        ObjectivePresentation.model_validate(
            {
                "presentation_id": "objective_01",
                "prompt": "Question",
                "correct_answer": 10,
            }
        )


def test_narrative_config_is_frozen_to_the_public_1000_character_limit() -> None:
    assert (
        NarrativeConfig(enabled=True, prompt="Optional", max_length=1000).max_length
        == 1000
    )

    with pytest.raises(ValidationError):
        NarrativeConfig.model_validate(
            {"enabled": True, "prompt": "Optional", "max_length": 999}
        )

    form = generate_form(708)
    malformed_private_config = NarrativeConfig.model_construct(
        enabled=True, prompt="Optional", max_length=999
    )
    with pytest.raises(AssertionError, match="1000-character limit"):
        canonical_module._validate_instrument_integrity(
            form.objective_items,
            form.static_sjt_items,
            form.behavior_profile_items,
            malformed_private_config,
        )


@pytest.mark.parametrize("collision_target", ["static", "behavior"])
def test_catalog_integrity_rejects_cross_category_presentation_id_collisions(
    collision_target: str,
) -> None:
    form = generate_form(707)
    duplicate_id = form.objective_items[0].presentation_id
    static_items = form.static_sjt_items
    behavior_items = form.behavior_profile_items
    if collision_target == "static":
        static_items = (
            replace(static_items[0], presentation_id=duplicate_id),
            *static_items[1:],
        )
    else:
        behavior_items = (
            replace(behavior_items[0], presentation_id=duplicate_id),
            *behavior_items[1:],
        )

    with pytest.raises(AssertionError, match="unique across all item types"):
        canonical_module._validate_instrument_integrity(
            form.objective_items, static_items, behavior_items, form.narrative
        )


def test_complete_submission_validates_without_scoring_unscored_fields() -> None:
    form = generate_form(606)
    responses = {**form.objective_answer_key(), **_valid_static_responses(form)}
    behavior = _valid_behavior_responses(form)
    validated_responses, validated_behavior, narrative = form.validate_submission(
        responses, behavior, "A short optional reflection."
    )
    assert validated_responses == responses
    assert validated_behavior == behavior
    assert narrative == "A short optional reflection."

    with pytest.raises(InvalidResponse):
        form.validate_submission(responses, behavior, "x" * 1001)
