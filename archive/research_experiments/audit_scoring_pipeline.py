"""Repeatable scoring-pipeline audit for the current AlterScore runtime bundle."""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "score_request_valid.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.app.services.scoring import ScoringService


def main() -> None:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    base_payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    bundle = load_runtime_artifact_bundle(strict=True)
    service = ScoringService(bundle)

    controlled_cases = build_controlled_cases(base_payload)
    case_results = {
        name: summarize_case(service.score_request_debug(payload))
        for name, payload in controlled_cases.items()
    }

    monotonic_checks = [
        monotonic_check(
            service,
            base_payload,
            "scroll_hesitation_score",
            {"behavioral": {"scroll_hesitation_score": 0.05}},
            {"behavioral": {"scroll_hesitation_score": 0.95}},
            expect_higher_on_high=False,
        ),
        monotonic_check(
            service,
            base_payload,
            "session_duration_sec",
            {"behavioral": {"session_duration_sec": 250.0}},
            {"behavioral": {"session_duration_sec": 1500.0}},
            expect_higher_on_high=False,
        ),
        monotonic_check(
            service,
            base_payload,
            "risk_response_speed_ratio",
            {"behavioral": {"risk_response_speed_ratio": 0.5}},
            {"behavioral": {"risk_response_speed_ratio": 2.5}},
            expect_higher_on_high=False,
        ),
        monotonic_check(
            service,
            base_payload,
            "numeracy_score_proxy",
            {"answers": {"numeracy_q1": 1000, "numeracy_q2": 0, "numeracy_q3": 0}},
            {"answers": {"numeracy_q1": 6600, "numeracy_q2": 1120, "numeracy_q3": 14400}},
            expect_higher_on_high=True,
        ),
        monotonic_check(
            service,
            base_payload,
            "future_orientation",
            {"answers": {"future_orient_q1": 0, "future_orient_q2": 0, "future_orient_q3": 1}},
            {"answers": {"future_orient_q1": 1, "future_orient_q2": 1, "future_orient_q3": 5}},
            expect_higher_on_high=True,
        ),
        monotonic_check(
            service,
            base_payload,
            "resilience_score",
            {"answers": {"resilience_q1": 1, "resilience_q2": 1, "resilience_q3": 3}},
            {"answers": {"resilience_q1": 5, "resilience_q2": 5, "resilience_q3": 0}},
            expect_higher_on_high=True,
        ),
        monotonic_check(
            service,
            base_payload,
            "social_capital_score",
            {"answers": {"social_capital_q1": 0, "social_capital_q2": 2, "social_capital_q3": 2}},
            {"answers": {"social_capital_q1": 3, "social_capital_q2": 0, "social_capital_q3": 0}},
            expect_higher_on_high=True,
        ),
    ]

    report = {
        "runtime_model_name": bundle.report.runtime_model_name,
        "runtime_model_type": bundle.report.runtime_model_type,
        "controlled_cases": case_results,
        "monotonic_checks": monotonic_checks,
        "missing_financial_inputs": [
            "income",
            "debt",
            "savings",
            "employment_stability",
            "existing_repayment_history",
        ],
    }
    print(json.dumps(report, indent=2))


def build_controlled_cases(base_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    baseline = copy.deepcopy(base_payload)

    terrible = copy.deepcopy(base_payload)
    terrible["answers"].update(
        {
            "numeracy_q1": 1000,
            "numeracy_q2": 1400,
            "numeracy_q3": 1000,
            "financial_literacy_q1": 0,
            "financial_literacy_q2": 0,
            "conscientiousness_q1": 1,
            "CRT_q1": 10,
            "CRT_q2": 100,
            "CRT_q3": 24,
            "future_orient_q1": 0,
            "future_orient_q2": 0,
            "future_orient_q3": 1,
            "risk_q1": 1,
            "risk_q2": 0,
            "loss_aversion_q1": 2,
            "locus_q1": 2,
            "locus_q2": 2,
            "locus_q3": 1,
            "social_capital_q1": 0,
            "social_capital_q2": 2,
            "social_capital_q3": 2,
            "resilience_q1": 1,
            "resilience_q2": 1,
            "resilience_q3": 3,
            "honesty_trap_q1": 5,
            "honesty_trap_q2": 5,
            "future_orient_repeat": 1,
            "locus_repeat": 0,
            "reciprocity_q1": 1,
            "reciprocity_q2": 2,
            "q27_resilience_text": "Everything went wrong and I could not do anything. I felt stuck and gave up.",
        }
    )
    terrible["behavioral"].update(
        {
            "avg_response_time_ms": 15000.0,
            "answer_change_rate": 0.6,
            "session_duration_sec": 1600.0,
            "dropout_count": 5,
            "scroll_hesitation_score": 0.9,
            "risk_response_speed_ratio": 2.3,
            "typing_speed_wpm": 8.0,
        }
    )

    average = copy.deepcopy(base_payload)
    average["answers"].update(
        {
            "numeracy_q1": 6400,
            "numeracy_q2": 1100,
            "numeracy_q3": 14000,
            "financial_literacy_q1": 1,
            "financial_literacy_q2": 0,
            "conscientiousness_q1": 3,
            "CRT_q1": 10,
            "CRT_q2": 5,
            "CRT_q3": 47,
            "future_orient_q1": 1,
            "future_orient_q2": 0,
            "future_orient_q3": 3,
            "risk_q1": 0,
            "risk_q2": 0,
            "loss_aversion_q1": 1,
            "locus_q1": 1,
            "locus_q2": 1,
            "locus_q3": 3,
            "social_capital_q1": 1,
            "social_capital_q2": 1,
            "social_capital_q3": 1,
            "resilience_q1": 3,
            "resilience_q2": 3,
            "resilience_q3": 1,
            "honesty_trap_q1": 3,
            "honesty_trap_q2": 3,
            "future_orient_repeat": 1,
            "locus_repeat": 1,
            "reciprocity_q1": 3,
            "reciprocity_q2": 1,
            "q27_resilience_text": "Income dropped for a month, so I cut some spending, asked for a little help, and got back on track.",
        }
    )
    average["behavioral"].update(
        {
            "avg_response_time_ms": 6200.0,
            "answer_change_rate": 0.14,
            "session_duration_sec": 560.0,
            "dropout_count": 1,
            "scroll_hesitation_score": 0.35,
            "risk_response_speed_ratio": 0.95,
            "typing_speed_wpm": 25.0,
        }
    )

    strong = copy.deepcopy(base_payload)

    perfect = copy.deepcopy(base_payload)
    perfect["answers"].update(
        {
            "conscientiousness_q1": 5,
            "future_orient_q3": 5,
            "risk_q1": 0,
            "risk_q2": 0,
            "locus_q2": 0,
            "locus_q3": 5,
            "social_capital_q1": 3,
            "resilience_q1": 5,
            "resilience_q2": 5,
            "honesty_trap_q1": 1,
            "honesty_trap_q2": 1,
            "reciprocity_q1": 5,
            "q27_resilience_text": "When sales fell, I reviewed every expense, negotiated supplier terms, found extra freelance work, and protected my repayment plan. I learned to act early, stay transparent, and keep a cash buffer for future shocks.",
        }
    )
    perfect["behavioral"].update(
        {
            "avg_response_time_ms": 4300.0,
            "answer_change_rate": 0.0,
            "session_duration_sec": 360.0,
            "dropout_count": 0,
            "scroll_hesitation_score": 0.05,
            "risk_response_speed_ratio": 0.7,
            "typing_speed_wpm": 42.0,
        }
    )

    contradictory = copy.deepcopy(base_payload)
    contradictory["answers"].update(
        {
            "future_orient_q1": 1,
            "future_orient_q2": 1,
            "future_orient_q3": 5,
            "future_orient_repeat": 0,
            "locus_q1": 0,
            "locus_repeat": 2,
            "honesty_trap_q1": 5,
            "honesty_trap_q2": 5,
            "q27_resilience_text": "I say I plan ahead, but honestly I often avoid dealing with problems until late.",
        }
    )
    contradictory["behavioral"].update(
        {
            "answer_change_rate": 0.35,
            "scroll_hesitation_score": 0.6,
        }
    )

    missing_text = copy.deepcopy(base_payload)
    missing_text["answers"]["q27_resilience_text"] = ""
    missing_text["behavioral"]["typing_speed_wpm"] = 0.0

    return {
        "terrible": terrible,
        "average": average,
        "strong": strong,
        "perfect": perfect,
        "contradictory": contradictory,
        "missing_text": missing_text,
    }


def monotonic_check(
    service: ScoringService,
    base_payload: dict[str, Any],
    feature_name: str,
    lower_mods: dict[str, dict[str, Any]],
    higher_mods: dict[str, dict[str, Any]],
    *,
    expect_higher_on_high: bool,
) -> dict[str, Any]:
    lower_payload = apply_modifications(base_payload, lower_mods)
    higher_payload = apply_modifications(base_payload, higher_mods)
    lower = summarize_case(service.score_request_debug(lower_payload))
    higher = summarize_case(service.score_request_debug(higher_payload))
    passed = (
        higher["credit_score"] >= lower["credit_score"]
        if expect_higher_on_high
        else higher["credit_score"] <= lower["credit_score"]
    )
    return {
        "feature": feature_name,
        "expectation": "higher_is_better" if expect_higher_on_high else "higher_is_worse",
        "lower_case": lower,
        "higher_case": higher,
        "passed": passed,
    }


def apply_modifications(
    base_payload: dict[str, Any],
    mods: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    payload = copy.deepcopy(base_payload)
    for section, values in mods.items():
        payload[section].update(values)
    return payload


def summarize_case(debug_trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "credit_score": debug_trace["final_score"]["credit_score"],
        "risk_band": debug_trace["final_score"]["risk_band"],
        "percentile": debug_trace["final_score"]["percentile"],
        "repayment_probability": debug_trace["model_debug"]["repayment_probability"],
        "psychometric_features": debug_trace["psychometric_features"],
        "behavioral_features": debug_trace["behavioral_features"],
        "nlp_features": debug_trace["nlp_features"],
        "meta_feature_vector": debug_trace["model_debug"].get("meta_feature_vector"),
    }


if __name__ == "__main__":
    main()
