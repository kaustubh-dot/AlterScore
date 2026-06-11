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


def test_promotion_gates_pass_for_clean_promoted_bundle() -> None:
    result = evaluate_promotion_gates(
        manifest=_manifest(),
        metrics_payload=_metrics(),
        fairness_report=_fairness(),
        psi_report=_psi(),
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
            flagged_share=0.22,
            max_gap=165,
        ),
        psi_report=_psi(),
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
    )

    assert result is not None
    assert result["status"] == "warning"
    assert result["warnings"] == ["drift_max_psi"]


def test_current_manifest_is_promoted_without_blocking_gate_failures() -> None:
    result = build_promotion_gate_summary_from_manifest(PRODUCTION_MANIFEST_PATH)

    assert result["promotion_status"] == "promoted"
    assert result["policy_version"] == "promotion_gate_policy_v1"
    assert result["status"] in {"passed", "warning"}
    assert result["blocking_failures"] == []
    assert promotion_gate_exit_code(result) == 0
    assert promotion_gate_exit_code(result, require_clean_pass=True) == (
        0 if result["status"] == "passed" else 1
    )


def test_promotion_gate_policy_file_is_versioned() -> None:
    policy = load_promotion_gate_policy()

    assert policy.policy_schema_version == "1.0.0"
    assert policy.policy_version == "promotion_gate_policy_v1"
    assert policy.max_expected_calibration_error == 0.08


def test_cli_returns_success_for_current_promoted_manifest_quiet() -> None:
    exit_code = main(["--manifest", str(PRODUCTION_MANIFEST_PATH), "--quiet"])

    assert exit_code == 0


def test_promoted_manifest_with_blocking_failures_returns_failure() -> None:
    result = evaluate_promotion_gates(
        manifest=_manifest(),
        metrics_payload=_metrics(ece=0.13),
        fairness_report=_fairness(
            overall_ece=0.13,
            flagged_share=0.22,
            max_gap=165,
        ),
        psi_report=_psi(),
    )

    assert result is not None
    assert result["promotion_status"] == "promoted"
    assert promotion_gate_exit_code(result) == 1
