from scripts.train_monotonic_tree_candidates import (
    build_recommendation,
    evaluate_fairness_gate,
)


def test_evaluate_fairness_gate_blocks_flagged_groups() -> None:
    gate = evaluate_fairness_gate(
        {
            "worst_auc_gap": 0.08,
            "flagged_groups": ["age_group=18-25"],
            "verdict": "Model requires attention.",
        }
    )

    assert gate["passed"] is False
    assert gate["flagged_groups"] == ["age_group=18-25"]


def test_build_recommendation_requires_promotion_eligibility() -> None:
    recommendation = build_recommendation(
        {
            "xgboost_monotonic": {"promotion_eligible": False},
            "lightgbm_monotonic": {"promotion_eligible": False},
        }
    )

    assert recommendation["status"] == "continue_candidate_iteration"
    assert recommendation["recommended_candidates"] == []
