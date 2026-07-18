"""Focused invariants for the pure Phase 3 unified scorer."""

from __future__ import annotations

import ast
import json
from collections.abc import Mapping
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction
from itertools import product
from pathlib import Path

import pytest

import backend.app.unified_scoring as unified_scoring
from backend.app.branching import (
    build_branching_scenarios,
    enumerate_paths,
    run_scenario,
)
from backend.app.instrument import generate_form
from backend.app.unified_scoring import (
    legacy_demo_score,
    quantize_fraction_half_up,
    round_fraction_half_up,
    score_unified_assessment,
)


def _submission(form, paths: tuple[tuple[str, ...], ...] | None = None):
    scenarios = build_branching_scenarios()
    selected_paths = paths or tuple(
        enumerate_paths(scenario)[0] for scenario in scenarios
    )
    responses: dict[str, object] = dict(form.objective_answer_key())
    responses.update(
        {
            item.presentation_id: item.options[0].option_id
            for item in form.static_sjt_items
        }
    )
    for scenario, path in zip(scenarios, selected_paths, strict=True):
        responses.update(
            {
                stage.presentation_id: option_id
                for stage, option_id in zip(scenario.stages, path, strict=True)
            }
        )
    behavior = {
        item.presentation_id: item.options[0].option_id
        for item in form.behavior_profile_items
    }
    return responses, behavior


def _score_without_behavior(result):
    return (
        result.objective_score,
        result.judgment_score,
        result.judgment_components,
        result.financial_decision_index,
        result.legacy_demo_score,
        result.limitations,
        result.explanation,
        result.branching_results,
    )


@pytest.mark.parametrize("index", range(101))
def test_all_canonical_financial_indices_map_to_legacy_demo_score(index: int) -> None:
    expected = 300 + (Fraction(11, 2) * index + Fraction(1, 2)).numerator // (
        Fraction(11, 2) * index + Fraction(1, 2)
    ).denominator
    assert legacy_demo_score(index) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (Fraction(1, 2) - Fraction(1, 1_000_000), 0),
        (Fraction(1, 2), 1),
        (Fraction(1, 2) + Fraction(1, 1_000_000), 1),
        (Fraction(3, 2) - Fraction(1, 1_000_000), 1),
        (Fraction(3, 2), 2),
    ),
)
def test_half_up_rounding_is_exact_at_whole_number_boundaries(
    value: Fraction, expected: int
) -> None:
    assert round_fraction_half_up(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (Fraction(1, 200) - Fraction(1, 1_000_000), Decimal("0.00")),
        (Fraction(1, 200), Decimal("0.01")),
        (Fraction(1, 200) + Fraction(1, 1_000_000), Decimal("0.01")),
        (Fraction(199, 200), Decimal("1.00")),
        (Fraction(1, 1), Decimal("1.00")),
    ),
)
def test_half_up_quantization_is_exact_at_two_decimal_boundaries(
    value: Fraction, expected: Decimal
) -> None:
    assert quantize_fraction_half_up(value, 2) == expected


def test_input_order_behavior_and_narrative_cannot_change_scored_result() -> None:
    form = generate_form(310)
    responses, behavior = _submission(form)
    baseline = score_unified_assessment(form, responses, behavior, None)

    reordered = dict(reversed(tuple(responses.items())))
    reordered_behavior = dict(reversed(tuple(behavior.items())))
    reordered_result = score_unified_assessment(
        form, reordered, reordered_behavior, "A different narrative."
    )
    assert reordered_result == baseline

    changed_behavior = {
        item.presentation_id: item.options[-1].option_id
        for item in form.behavior_profile_items
    }
    changed_result = score_unified_assessment(
        form, responses, changed_behavior, "A second narrative."
    )
    assert _score_without_behavior(changed_result) == _score_without_behavior(baseline)
    assert changed_result.behavior_profile != baseline.behavior_profile


def test_all_54_branching_paths_score_through_the_unified_service() -> None:
    form = generate_form(311)
    scenarios = build_branching_scenarios()
    default_paths = tuple(enumerate_paths(scenario)[0] for scenario in scenarios)
    seen: set[tuple[str, tuple[str, ...]]] = set()

    for scenario_index, scenario in enumerate(scenarios):
        for path in enumerate_paths(scenario):
            paths = list(default_paths)
            paths[scenario_index] = path
            responses, behavior = _submission(form, tuple(paths))
            result = score_unified_assessment(form, responses, behavior)
            branch_result = result.branching_results[scenario_index]
            assert branch_result.scenario_presentation_id == scenario.scenario_presentation_id
            assert branch_result.option_ids == path
            assert len(branch_result.timeline) == 3
            assert len(result.judgment_components) == 6
            seen.add((scenario.scenario_presentation_id, path))

    assert len(seen) == 54


def test_all_729_paired_branching_paths_score_through_the_unified_service() -> None:
    form = generate_form(316)
    scenarios = build_branching_scenarios()
    paired_paths = product(*(enumerate_paths(scenario) for scenario in scenarios))
    seen: set[tuple[tuple[str, ...], ...]] = set()

    for paths in paired_paths:
        responses, behavior = _submission(form, paths)
        result = score_unified_assessment(form, responses, behavior)
        assert tuple(branch.option_ids for branch in result.branching_results) == paths
        assert 0 <= result.financial_decision_index <= 100
        assert len(result.judgment_components) == 6
        seen.add(paths)

    assert len(seen) == 729


def test_all_six_judgment_components_have_equal_weight() -> None:
    form = generate_form(312)
    responses, behavior = _submission(form)
    result = score_unified_assessment(form, responses, behavior)
    component_mean = sum(result.judgment_components, Fraction(0, 1)) / 6
    expected_weighted_total = (
        Fraction(55, 100) * result.objective_score
        + Fraction(45, 100) * component_mean
    )

    assert result.judgment_score == component_mean
    assert result.explanation.formula.judgment_score == quantize_fraction_half_up(
        component_mean, 2
    )
    assert result.financial_decision_index == round_fraction_half_up(
        expected_weighted_total
    )
    assert result.explanation.formula.weighted_total_exact == (
        f"{expected_weighted_total.numerator}/{expected_weighted_total.denominator}"
    )


@pytest.mark.parametrize("missing_id_kind", ("objective", "static", "branch"))
def test_missing_scored_or_branch_response_fails_closed(missing_id_kind: str) -> None:
    form = generate_form(313)
    responses, behavior = _submission(form)
    if missing_id_kind == "objective":
        missing_id = form.objective_items[0].presentation_id
    elif missing_id_kind == "static":
        missing_id = form.static_sjt_items[0].presentation_id
    else:
        missing_id = build_branching_scenarios()[0].stages[0].presentation_id
    responses.pop(missing_id)

    with pytest.raises(ValueError):
        score_unified_assessment(form, responses, behavior)


@pytest.mark.parametrize("extra_id", ("extra_scored_response", "extra_branch_response"))
def test_extra_scored_or_branch_response_fails_closed(extra_id: str) -> None:
    form = generate_form(314)
    responses, behavior = _submission(form)
    responses[extra_id] = "not-issued"

    with pytest.raises(ValueError):
        score_unified_assessment(form, responses, behavior)


def test_recommendation_evidence_ids_are_real_or_empty_maintenance_evidence() -> None:
    form = generate_form(315)
    scenarios = build_branching_scenarios()
    objective_ids = {item.presentation_id for item in form.objective_items}
    scenario_ids = {scenario.scenario_presentation_id for scenario in scenarios}
    option_ids = {
        option.option_id
        for item in form.static_sjt_items
        for option in item.options
    }
    option_ids.update(
        option.option_id
        for scenario in scenarios
        for stage in scenario.stages
        for option in stage.options
    )

    responses, behavior = _submission(form)
    wrong_answer = form.objective_items[0].correct_answer
    responses[form.objective_items[0].presentation_id] = (
        wrong_answer - 1 if wrong_answer else wrong_answer + 1
    )
    result = score_unified_assessment(form, responses, behavior)
    recommendations = result.explanation.recommendations
    assert any(
        recommendation.evidence_type == "objective"
        and form.objective_items[0].presentation_id in recommendation.evidence_ids
        for recommendation in recommendations
    )

    weak_paths = tuple(
        min(enumerate_paths(scenario), key=lambda path: run_scenario(scenario, path).scenario_score)
        for scenario in scenarios
    )
    weak_responses, weak_behavior = _submission(form, weak_paths)
    weak_result = score_unified_assessment(form, weak_responses, weak_behavior)
    assert any(
        recommendation.evidence_type == "branching"
        and recommendation.evidence_ids
        and set(recommendation.evidence_ids) <= scenario_ids
        for recommendation in weak_result.explanation.recommendations
    )

    for recommendation in (*recommendations, *weak_result.explanation.recommendations):
        if recommendation.evidence_type == "objective":
            assert recommendation.evidence_ids
            assert set(recommendation.evidence_ids) <= objective_ids
        elif recommendation.evidence_type == "branching":
            assert recommendation.evidence_ids
            assert set(recommendation.evidence_ids) <= scenario_ids
        else:
            assert recommendation.evidence_type == "maintenance"
            assert recommendation.evidence_ids == []
        assert not set(recommendation.evidence_ids) & option_ids


def _walk_mappings(value: object):
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key)
            yield from _walk_mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_mappings(child)


def test_unified_scoring_has_no_forbidden_api_ml_or_v1_imports() -> None:
    forbidden_prefixes = (
        "backend.api",
        "backend.app.api",
        "backend.app.core",
        "backend.app.main",
        "backend.app.schemas.score",
        "backend.app.services",
        "backend.app.v1",
        "backend.ml",
        "fastapi",
        "joblib",
        "lightgbm",
        "shap",
        "xgboost",
    )
    package_path = Path(unified_scoring.__file__).parent
    imported: set[str] = set()
    for source_path in package_path.glob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported.add(node.module)

    assert not {
        module
        for module in imported
        if module.startswith(forbidden_prefixes)
    }


def test_public_explanation_has_no_option_ids_rubric_shap_or_probability_fields() -> None:
    form = generate_form(316)
    responses, behavior = _submission(form)
    result = score_unified_assessment(form, responses, behavior)
    payload = result.explanation.model_dump(mode="json")
    serialized = json.dumps(payload, sort_keys=True)
    all_option_ids = {
        option.option_id
        for item in form.static_sjt_items
        for option in item.options
    }
    all_option_ids.update(
        option.option_id
        for item in form.behavior_profile_items
        for option in item.options
    )
    all_option_ids.update(
        option.option_id
        for scenario in build_branching_scenarios()
        for stage in scenario.stages
        for option in stage.options
    )

    forbidden_key_fragments = ("option_id", "rubric", "point", "shap", "probability")
    assert not any(
        fragment in key.lower()
        for key in _walk_mappings(payload)
        for fragment in forbidden_key_fragments
    )
    assert not any(option_id in serialized for option_id in all_option_ids)
    assert "rubric" not in serialized.lower()
    assert "shap" not in serialized.lower()
    assert "probability" not in serialized.lower()


def test_explanation_decimal2_json_fields_are_numbers_and_reconcile_exactly() -> None:
    form = generate_form(317)
    responses, behavior = _submission(form)
    result = score_unified_assessment(form, responses, behavior)
    payload = json.loads(result.explanation.model_dump_json())

    assert isinstance(payload["formula"]["objective_score"], float)
    assert isinstance(payload["formula"]["judgment_score"], float)
    assert all(
        isinstance(value, float)
        for scenario in payload["branching_scenarios"]
        for value in (*scenario["dimensions"].values(), scenario["scenario_score"])
    )

    forged_formula = result.explanation.formula.model_copy(
        update={
            "objective_score": Decimal("0.00"),
            "objective_contribution_exact": "0/1",
            "weighted_total_exact": "0/1",
        }
    )
    forged_explanation = result.explanation.model_copy(
        update={"formula": forged_formula}
    )
    with pytest.raises(ValueError, match="reconcile"):
        replace(result, explanation=forged_explanation)
    with pytest.raises(Exception):
        result.explanation.formula.objective_score = Decimal("0.00")
