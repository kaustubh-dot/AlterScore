import numpy as np
import pandas as pd

from scripts.fairness_harden_xgboost_candidate import (
    apply_proxy_feature_clipping,
    build_subgroup_probability_diagnostics,
    choose_recommended_calibration_strategy,
)


def test_apply_proxy_feature_clipping_uses_train_quantiles() -> None:
    feature_frame = pd.DataFrame(
        {
            "session_duration_sec": [10.0, 12.0, 15.0, 1000.0],
            "avg_response_time_ms": [200.0, 220.0, 240.0, 3000.0],
        }
    )
    train_mask = pd.Series([True, True, True, False])

    clipped, summary = apply_proxy_feature_clipping(
        feature_frame=feature_frame,
        train_mask=train_mask,
        clip_quantiles={"session_duration_sec": (0.0, 1.0)},
    )

    assert summary["applied"] is True
    assert clipped.loc[3, "session_duration_sec"] == 15.0
    assert clipped.loc[3, "avg_response_time_ms"] == 3000.0


def test_build_subgroup_probability_diagnostics_reports_target_group_summary() -> None:
    protected = pd.DataFrame(
        {
            "gender": ["non_binary", "non_binary", "female", "female"],
            "age_group": ["26-35"] * 4,
            "region": ["urban"] * 4,
            "education_level": ["secondary"] * 4,
        }
    )

    report = build_subgroup_probability_diagnostics(
        y_true=np.asarray([1, 0, 1, 0]),
        probabilities=np.asarray([0.7, 0.6, 0.8, 0.2]),
        protected_frame=protected,
        groups=["gender=non_binary"],
    )

    assert report["gender=non_binary"]["available"] is True
    assert report["gender=non_binary"]["n_samples"] == 2
    assert "reliability_curve" in report["gender=non_binary"]


def test_choose_recommended_calibration_strategy_prefers_low_subgroup_ece() -> None:
    recommended = choose_recommended_calibration_strategy(
        {
            "raw": {
                "production_safe": True,
                "fairness_gate": {"passed": True},
                "test_metrics": {"auc_roc": 0.81, "expected_calibration_error": 0.03},
                "target_group_diagnostics": {
                    "gender=non_binary": {"expected_calibration_error": 0.11}
                },
            },
            "temperature": {
                "production_safe": True,
                "fairness_gate": {"passed": True},
                "test_metrics": {"auc_roc": 0.805, "expected_calibration_error": 0.025},
                "target_group_diagnostics": {
                    "gender=non_binary": {"expected_calibration_error": 0.07}
                },
            },
        }
    )

    assert recommended == "temperature"
