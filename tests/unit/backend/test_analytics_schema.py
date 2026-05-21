from datetime import datetime, timezone

from backend.app.schemas.analytics import (
    BaselineComparisonResponse,
    CalibrationCurveResponse,
    ConfusionMatrixResponse,
    DriftReport,
    FairnessReport,
    GlobalImportanceResponse,
    HealthResponse,
    ModelStatsResponse,
    PrecisionRecallResponse,
    RocCurveResponse,
    ScoreDistributionResponse,
)


def test_health_response_matches_documented_contract_shape() -> None:
    response = HealthResponse.model_validate(
        {
            "status": "ok",
            "version": "0.1.0",
            "model_loaded": True,
            "artifact_source": "manifest",
            "manifest_backed": True,
            "manifest_version": "local_logistic_runtime_v1",
            "model_version": "0.1.0",
            "artifacts_loaded": [
                "production_manifest",
                "runtime_model",
                "preprocessor",
                "text_pca",
                "shap_explainer",
                "dice_explainer",
                "metrics",
                "baseline_metrics",
                "fairness_report",
                "psi_report",
                "global_importance",
                "population_percentiles",
            ],
            "missing_artifacts": [],
            "invalid_artifacts": [],
            "timestamp": datetime(2026, 5, 13, tzinfo=timezone.utc),
        }
    )

    assert set(response.model_dump(mode="json")) == {
        "status",
        "version",
        "model_loaded",
        "artifact_source",
        "manifest_backed",
        "manifest_version",
        "model_version",
        "artifacts_loaded",
        "missing_artifacts",
        "invalid_artifacts",
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
        {
            "model_name": "xgboost",
            "model_type": "classical",
            "items": [
                {
                    "feature": "future_orientation",
                    "display_name": "Future Orientation",
                    "mean_abs_shap": 0.083,
                    "category": "psychometric",
                    "rank": 1,
                }
            ],
        }
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

    assert importance.model_name == "xgboost"
    assert importance.items[0].rank == 1
    assert set(drift.model_dump(mode="json")) == {
        "max_psi",
        "verdict",
        "thresholds",
        "top_drifted_features",
        "all_features",
    }


def test_score_distribution_shape_matches_documented_contract() -> None:
    response = ScoreDistributionResponse.model_validate(
        {
            "model_name": "logistic_regression",
            "row_count": 10_000,
            "summary": {
                "min_score": 300,
                "max_score": 850,
                "mean_score": 590.8,
                "median_score": 596.0,
            },
            "score_histogram": [
                {
                    "label": "300-349",
                    "score_min": 300,
                    "score_max": 349,
                    "count": 367,
                    "share": 0.0367,
                }
            ],
        }
    )

    assert response.row_count == 10_000
    assert response.score_histogram[0].label == "300-349"


def test_curve_and_confusion_shapes_match_documented_contracts() -> None:
    roc = RocCurveResponse.model_validate(
        [
            {
                "model_name": "logistic_regression",
                "model_type": "classical",
                "split": "test_months_11_12",
                "points": [
                    {
                        "fpr": 0.0,
                        "tpr": 0.0,
                    },
                    {
                        "fpr": 1.0,
                        "tpr": 1.0,
                    },
                ],
            }
        ]
    )
    pr = PrecisionRecallResponse.model_validate(
        [
            {
                "model_name": "logistic_regression",
                "model_type": "classical",
                "split": "test_months_11_12",
                "points": [
                    {
                        "recall": 1.0,
                        "precision": 0.72,
                    }
                ],
            }
        ]
    )
    calibration = CalibrationCurveResponse.model_validate(
        [
            {
                "model_name": "logistic_regression",
                "model_type": "classical",
                "split": "test_months_11_12",
                "points": [
                    {
                        "mean_predicted": 0.45,
                        "fraction_positive": 0.52,
                        "count": 168,
                    }
                ],
            }
        ]
    )
    confusion = ConfusionMatrixResponse.model_validate(
        [
            {
                "model_name": "logistic_regression",
                "model_type": "classical",
                "split": "test_months_11_12",
                "threshold": 0.24,
                "tp": 1245,
                "fp": 331,
                "fn": 54,
                "tn": 170,
                "tpr": 0.9584,
                "fpr": 0.6607,
                "fnr": 0.0416,
                "precision": 0.79,
                "recall": 0.9584,
                "specificity": 0.3393,
                "accuracy": 0.785,
                "f1": 0.866,
            }
        ]
    )

    assert roc.root[0].points[1].tpr == 1.0
    assert pr.root[0].points[0].precision == 0.72
    assert calibration.root[0].points[0].count == 168
    assert confusion.root[0].threshold == 0.24


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
            "calibration_parity": {
                "n_bins": 10,
                "overall_expected_calibration_error": 0.04,
                "max_ece_gap": 0.02,
                "evaluated_group_count": 1,
                "skipped_group_count": 0,
                "groups": {
                    "gender": {
                        "female": {
                            "n_samples": 450,
                            "expected_calibration_error": 0.05,
                            "ece_gap_from_overall": 0.01,
                            "mean_predicted_probability": 0.68,
                            "observed_repayment_rate": 0.70,
                            "points": [
                                {
                                    "mean_predicted": 0.65,
                                    "fraction_positive": 0.68,
                                    "count": 120,
                                }
                            ],
                        }
                    }
                },
            },
            "individual_fairness_proxy": {
                "similarity_feature_set": [
                    "numeracy_score",
                    "CRT_score",
                ],
                "similarity_threshold": 0.9,
                "score_gap_threshold": 50,
                "evaluated_applicants": 450,
                "evaluated_pairs": 80,
                "flagged_pair_count": 1,
                "flagged_pair_share": 0.0125,
                "max_score_gap": 64,
                "mean_score_gap": 18.5,
                "p95_score_gap": 42.0,
                "worst_pairs": [
                    {
                        "row_position_a": 0,
                        "row_position_b": 9,
                        "score_a": 710,
                        "score_b": 646,
                        "score_gap": 64,
                        "cosine_similarity": 0.94,
                        "differing_attributes": ["gender"],
                    }
                ],
                "verdict": "Individual fairness proxy found one pair to review.",
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
        "calibration_parity",
        "individual_fairness_proxy",
    }
