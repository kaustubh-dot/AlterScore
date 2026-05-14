import numpy as np

from backend.ml.explainability.global_importance import (
    build_global_importance_report_for_candidate_models,
)


class _LinearModel:
    coef_ = np.asarray([[0.2, 0.1]], dtype=float)


class _TreeModel:
    feature_importances_ = np.asarray([0.3, 0.7], dtype=float)


def test_global_importance_prefers_highest_auc_supported_model() -> None:
    report, selected_model_name = build_global_importance_report_for_candidate_models(
        {
            "logistic_regression": _LinearModel(),
            "xgboost": _TreeModel(),
        },
        train_processed_features=np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=float),
        test_processed_features=np.asarray([[0.1, 0.9], [0.9, 0.1]], dtype=float),
        model_stats=[
            {
                "model_name": "logistic_regression",
                "auc_roc": 0.81,
                "split": "test_months_11_12",
            },
            {
                "model_name": "xgboost",
                "auc_roc": 0.92,
                "split": "test_months_11_12",
            },
        ],
        candidate_model_types={
            "logistic_regression": "classical",
            "xgboost": "classical",
        },
        feature_names=("numeracy_score", "CRT_score"),
    )

    assert selected_model_name == "xgboost"
    assert report["model_name"] == "xgboost"
    assert report["model_type"] == "classical"
    assert [item["rank"] for item in report["items"]] == [1, 2]
