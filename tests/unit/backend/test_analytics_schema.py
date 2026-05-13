from datetime import datetime, timezone

from backend.app.schemas.analytics import (
    BaselineComparisonResponse,
    DriftReport,
    FairnessReport,
    GlobalImportanceResponse,
    HealthResponse,
    ModelStatsResponse,
)


def test_health_response_matches_documented_contract_shape() -> None:
    response = HealthResponse.model_validate(
        {
            "status": "ok",
            "version": "0.1.0",
            "model_loaded": True,
            "artifacts_loaded": [
                "calibrated_stacking",
                "preprocessor",
                "text_pca",
                "shap_explainer",
                "dice_explainer",
                "metrics",
                "fairness_report",
                "psi_report",
            ],
            "missing_artifacts": [],
            "timestamp": datetime(2026, 5, 13, tzinfo=timezone.utc),
        }
    )

    assert set(response.model_dump(mode="json")) == {
        "status",
        "version",
        "model_loaded",
        "artifacts_loaded",
        "missing_artifacts",
        "timestamp",
    }


def test_model_stats_and_baseline_comparison_list_shapes_parse() -> None:
    model_stats = ModelStatsResponse.model_validate(
        [
            {
                "model_name": "stacking_ensemble",
                "model_type": "ensemble",
                "auc_roc": 0.81,
                "auc_pr": 0.86,
                "ks_statistic": 0.47,
                "brier_score": 0.14,
                "expected_calibration_error": 0.03,
                "accuracy": 0.76,
                "precision": 0.79,
                "recall": 0.82,
                "f1": 0.80,
                "threshold": 0.45,
                "split": "test_months_11_12",
            }
        ]
    )
    baseline = BaselineComparisonResponse.model_validate(
        [
            {
                "model_name": "simulated_loan_officer",
                "model_type": "baseline",
                "auc_roc": 0.68,
                "ks_statistic": 0.28,
                "brier_score": 0.19,
                "expected_calibration_error": 0.08,
                "lift_vs_loan_officer": 0.0,
            }
        ]
    )

    assert model_stats.root[0].model_name == "stacking_ensemble"
    assert baseline.root[0].model_type == "baseline"


def test_global_importance_and_drift_report_shapes_match_contract() -> None:
    importance = GlobalImportanceResponse.model_validate(
        [
            {
                "feature": "future_orientation",
                "display_name": "Future Orientation",
                "mean_abs_shap": 0.083,
                "category": "psychometric",
                "rank": 1,
            }
        ]
    )
    drift = DriftReport.model_validate(
        {
            "max_psi": 0.12,
            "verdict": "stable",
            "thresholds": {
                "stable_below": 0.2,
                "watch_below": 0.3,
                "alert_at_or_above": 0.3,
            },
            "top_drifted_features": [
                {
                    "feature": "typing_speed_wpm",
                    "psi": 0.12,
                    "status": "stable",
                }
            ],
            "all_features": [],
        }
    )

    assert importance.root[0].rank == 1
    assert set(drift.model_dump(mode="json")) == {
        "max_psi",
        "verdict",
        "thresholds",
        "top_drifted_features",
        "all_features",
    }


def test_fairness_report_shape_matches_documented_contract() -> None:
    fairness = FairnessReport.model_validate(
        {
            "overall_auc": 0.81,
            "overall_approval_rate": 0.64,
            "overall_default_rate": 0.28,
            "worst_auc_gap": 0.03,
            "flagged_groups": [],
            "verdict": (
                "Model shows acceptable fairness across all tested demographic groups."
            ),
            "groups": {
                "gender": {
                    "female": {
                        "n_samples": 450,
                        "auc": 0.80,
                        "auc_gap_from_overall": 0.01,
                        "approval_rate": 0.63,
                        "fpr": 0.14,
                        "fnr": 0.18,
                        "mean_score": 688.4,
                        "flag": "green",
                    }
                }
            },
        }
    )

    assert set(fairness.model_dump(mode="json")) == {
        "overall_auc",
        "overall_approval_rate",
        "overall_default_rate",
        "worst_auc_gap",
        "flagged_groups",
        "verdict",
        "groups",
    }
