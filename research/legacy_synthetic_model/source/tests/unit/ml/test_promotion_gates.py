from backend.app.core.paths import PRODUCTION_MANIFEST_PATH
from backend.ml.registry.promotion_gates import (
    build_promotion_gate_summary_from_manifest,
    evaluate_promotion_gates,
    load_promotion_gate_policy,
    main,
    promotion_gate_exit_code,
)


def _manifest() -> dict:
    return {
        "runtime_model_name": "xgboost_monotonic",
        "promotion_status": "promoted",
    }


def _metrics(*, auc: float = 0.78, ece: float = 0.04) -> dict:
    return {
        "model_stats": [
            {
                "model_name": "xgboost_monotonic",
                "split": "test_months_11_12",
                "auc_roc": auc,
                "expected_calibration_error": ece,
            }
        ]
    }


def _fairness(
    *,
    overall_ece: float = 0.04,
    flagged_share: float = 0.02,
    max_gap: int = 80,
) -> dict:
    return {
        "overall_auc": 0.78,
        "worst_auc_gap": 0.03,
        "calibration_parity": {
            "overall_expected_calibration_error": overall_ece,
        },
        "individual_fairness_proxy": {
            "flagged_pair_share": flagged_share,
            "max_score_gap": max_gap,
        },
        "post_governance_impact": {
            "overall_auc_after_governance": 0.775,
            "overall_approval_rate_delta": -0.02,
        },
    }


def _psi(*, max_psi: float = 0.05, verdict: str = "stable") -> dict:
    return {
        "max_psi": max_psi,
        "verdict": verdict,
    }


def _population_percentiles_passing() -> dict:
    """Minimal percentiles payload that satisfies all distribution gates."""
    score_to_pct: dict[str, int] = {}
    for s in range(300, 851):
        if s < 450:
            pct = 0
        elif s < 580:
            pct = int((s - 450) / (580 - 450) * 10)
        elif s < 640:
            pct = 10 + int((s - 580) / 60 * 25)
        elif s < 720:
            pct = 35 + int((s - 640) / 80 * 45)
        elif s < 800:
            pct = 80 + int((s - 720) / 80 * 15)
        else:
            pct = 95 + int((s - 800) / 50 * 5)
        score_to_pct[str(s)] = min(pct, 100)
    return {
        "summary": {"median_score": 638.0, "max_score": 820.0},
        "score_to_percentile": score_to_pct,
    }


def test_promotion_gates_pass_for_clean_promoted_bundle() -> None:
    result = evaluate_promotion_gates(
        manifest=_manifest(),
        metrics_payload=_metrics(),
        fairness_report=_fairness(),
        psi_report=_psi(),
        population_percentiles=_population_percentiles_passing(),
    )

    assert result is not None
    assert result["status"] == "passed"
    assert result["blocking_failures"] == []


def test_promotion_gates_fail_for_bad_calibration_and_individual_fairness() -> None:
    result = evaluate_promotion_gates(
        manifest=_manifest(),
        metrics_payload=_metrics(ece=0.13),
        fairness_report=_fairness(
            overall_ece=0.13,
            flagged_share=0.50,
            max_gap=250,
        ),
        psi_report=_psi(),
        population_percentiles=_population_percentiles_passing(),
    )

    assert result is not None
    assert result["status"] == "failed"
    assert set(result["blocking_failures"]) >= {
        "expected_calibration_error",
        "calibration_parity_ece",
        "individual_fairness_flagged_share",
        "individual_fairness_max_score_gap",
    }
    assert promotion_gate_exit_code(result) == 1


def test_promotion_gates_warn_for_watch_level_drift() -> None:
    result = evaluate_promotion_gates(
        manifest=_manifest(),
        metrics_payload=_metrics(),
        fairness_report=_fairness(),
        psi_report=_psi(max_psi=0.21, verdict="watch"),
        population_percentiles=_population_percentiles_passing(),
    )

    assert result is not None
    assert result["status"] == "warning"
    assert result["warnings"] == ["drift_max_psi"]


def test_current_manifest_is_promoted_without_blocking_gate_failures() -> None:
    result = build_promotion_gate_summary_from_manifest(PRODUCTION_MANIFEST_PATH)

    assert result["promotion_status"] == "promoted"
    assert result["policy_version"] == "promotion_gate_policy_v2"
    assert result["status"] in {"passed", "warning"}
    assert result["blocking_failures"] == []
    assert promotion_gate_exit_code(result) == 0
    assert promotion_gate_exit_code(result, require_clean_pass=True) == (
        0 if result["status"] == "passed" else 1
    )


def test_promotion_gate_policy_file_is_versioned() -> None:
    policy = load_promotion_gate_policy()

    assert policy.policy_schema_version == "1.0.0"
    assert policy.policy_version == "promotion_gate_policy_v2"
    assert policy.max_expected_calibration_error == 0.08
    # distribution gates present
    assert policy.score_dist_min_median == 580.0
    assert policy.score_dist_max_reachable == 760


def test_cli_returns_success_for_current_promoted_manifest_quiet() -> None:
    exit_code = main(["--manifest", str(PRODUCTION_MANIFEST_PATH), "--quiet"])

    assert exit_code == 0


def test_promoted_manifest_with_blocking_failures_returns_failure() -> None:
    result = evaluate_promotion_gates(
        manifest=_manifest(),
        metrics_payload=_metrics(ece=0.13),
        fairness_report=_fairness(
            overall_ece=0.13,
            flagged_share=0.50,
            max_gap=250,
        ),
        psi_report=_psi(),
        population_percentiles=_population_percentiles_passing(),
    )

    assert result is not None
    assert result["promotion_status"] == "promoted"
    assert promotion_gate_exit_code(result) == 1


def _population_percentiles_good(
    *, median: float = 638, max_score: float = 810
) -> dict:
    """Minimal population percentiles payload that passes distribution gates."""
    score_to_pct: dict[str, int] = {}
    for s in range(300, 851):
        if s < 425:
            score_to_pct[str(s)] = 0
        elif s < 550:
            score_to_pct[str(s)] = int((s - 425) / (550 - 425) * 14) + 1
        elif s < 650:
            score_to_pct[str(s)] = 15 + int((s - 550) / 100 * 50)
        else:
            score_to_pct[str(s)] = 65 + int((s - 650) / 200 * 35)
    return {
        "summary": {"median_score": median, "max_score": max_score},
        "score_to_percentile": score_to_pct,
        "artifacts": {},
    }


def _population_percentiles_collapsed() -> dict:
    """Mimics the old factor=40 failure: median=529, max=683."""
    score_to_pct: dict[str, int] = {}
    for s in range(300, 851):
        if s < 425:
            score_to_pct[str(s)] = 0
        elif s <= 683:
            score_to_pct[str(s)] = int((s - 425) / (683 - 425) * 100)
        else:
            score_to_pct[str(s)] = 100
    return {
        "summary": {"median_score": 529.0, "max_score": 683.0},
        "score_to_percentile": score_to_pct,
    }


def test_score_distribution_gate_passes_for_healthy_mapping() -> None:
    from backend.ml.registry.promotion_gates import (
        _evaluate_score_distribution_gates,
        DEFAULT_PROMOTION_GATE_POLICY,
    )

    checks = _evaluate_score_distribution_gates(
        population_percentiles=_population_percentiles_good(),
        policy=DEFAULT_PROMOTION_GATE_POLICY,
    )
    failures = [c for c in checks if c.status == "fail"]
    assert failures == [], [c.message for c in failures]


def test_score_distribution_gate_blocks_collapsed_mapping() -> None:
    """factor=40 / old mapping must fail the distribution gate."""
    from backend.ml.registry.promotion_gates import (
        _evaluate_score_distribution_gates,
        DEFAULT_PROMOTION_GATE_POLICY,
    )

    checks = _evaluate_score_distribution_gates(
        population_percentiles=_population_percentiles_collapsed(),
        policy=DEFAULT_PROMOTION_GATE_POLICY,
    )
    failing_names = {c.name for c in checks if c.status == "fail"}
    # median=529 fails min_median; max=683 fails max_reachable
    assert "score_dist_median" in failing_names
    assert "score_dist_max_reachable" in failing_names


def test_score_distribution_gate_fails_when_artifact_missing() -> None:
    from backend.ml.registry.promotion_gates import (
        _evaluate_score_distribution_gates,
        DEFAULT_PROMOTION_GATE_POLICY,
    )

    checks = _evaluate_score_distribution_gates(
        population_percentiles=None,
        policy=DEFAULT_PROMOTION_GATE_POLICY,
    )
    assert any(c.status == "fail" for c in checks)
