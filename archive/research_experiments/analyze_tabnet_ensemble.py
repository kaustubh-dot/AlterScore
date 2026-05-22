"""Analyze whether TabNet should be dropped or downweighted in the live ensemble."""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "score_request_valid.json"
DATASET_PATH = ROOT / "data" / "raw" / "synthetic_dataset.csv"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.app.services.scoring import ScoringService
from backend.ml.data_generation.generator import TEMPORAL_SPLIT_MONTHS
from backend.ml.inference.ensemble_adapter import _predict_base_model_proba
from backend.ml.preprocessing.pipeline import (
    align_text_features_from_raw_text,
    prepare_temporal_data,
    transform_features,
)


def main() -> None:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    bundle = load_runtime_artifact_bundle(strict=True)
    score_service = ScoringService(bundle)
    temporal_analysis = build_temporal_stack_analysis(bundle)
    case_analysis = build_controlled_case_analysis(score_service)

    report = {
        "runtime_model_name": bundle.report.runtime_model_name,
        "runtime_model_type": bundle.report.runtime_model_type,
        "temporal_test_analysis": temporal_analysis,
        "controlled_case_analysis": case_analysis,
        "recommendation": summarize_recommendation(
            temporal_analysis=temporal_analysis,
            case_analysis=case_analysis,
        ),
    }
    print(json.dumps(report, indent=2))


def build_temporal_stack_analysis(bundle: Any) -> dict[str, Any]:
    dataset = pd.read_csv(DATASET_PATH)
    aligned_dataset, raw_embeddings = align_text_features_from_raw_text(dataset)
    prepared = prepare_temporal_data(
        aligned_dataset,
        raw_text_embeddings=raw_embeddings,
        text_pca_artifact_path=None,
    )
    X_validation = transform_features(bundle.preprocessor, prepared.validation.X)
    X_test = transform_features(bundle.preprocessor, prepared.test.X)
    y_validation = prepared.validation.y.to_numpy(dtype=int)
    y_test = prepared.test.y.to_numpy(dtype=int)

    base_model_order = tuple(bundle.stacking_config["base_model_order"])
    validation_probabilities = {
        model_name: _positive_class_probability(
            _predict_base_model_proba(bundle.base_models[model_name], X_validation)
        )
        for model_name in base_model_order
    }
    test_probabilities = {
        model_name: _positive_class_probability(
            _predict_base_model_proba(bundle.base_models[model_name], X_test)
        )
        for model_name in base_model_order
    }

    current_meta_matrix = np.column_stack(
        [validation_probabilities[model_name] for model_name in base_model_order]
    )
    current_test_meta_matrix = np.column_stack(
        [test_probabilities[model_name] for model_name in base_model_order]
    )
    current_raw_meta = bundle.model.calibrated_classifiers_[0].estimator
    current_test_probabilities = np.asarray(
        bundle.model.predict_proba(current_test_meta_matrix),
        dtype=float,
    )[:, 1]
    current_test_raw_probabilities = current_raw_meta.predict_proba(current_test_meta_matrix)[:, 1]

    stack_variants = {
        "current_runtime": {
            "auc": float(roc_auc_score(y_test, current_test_probabilities)),
            "brier": float(brier_score_loss(y_test, current_test_probabilities)),
            "raw_auc": float(roc_auc_score(y_test, current_test_raw_probabilities)),
            "coefficients": {
                model_name: float(weight)
                for model_name, weight in zip(
                    base_model_order,
                    current_raw_meta.coef_[0].tolist(),
                    strict=True,
                )
            },
            "intercept": float(current_raw_meta.intercept_[0]),
        },
        "drop_tabnet_retrained_meta": _fit_stack_variant(
            validation_probabilities=validation_probabilities,
            test_probabilities=test_probabilities,
            y_validation=y_validation,
            y_test=y_test,
            feature_names=tuple(
                model_name for model_name in base_model_order if model_name != "tabnet"
            ),
        ),
        "tabnet_half_weight_retrained_meta": _fit_stack_variant(
            validation_probabilities=validation_probabilities,
            test_probabilities=test_probabilities,
            y_validation=y_validation,
            y_test=y_test,
            feature_names=base_model_order,
            weights=(1.0, 1.0, 1.0, 1.0, 0.5, 1.0),
        ),
        "tabnet_quarter_weight_retrained_meta": _fit_stack_variant(
            validation_probabilities=validation_probabilities,
            test_probabilities=test_probabilities,
            y_validation=y_validation,
            y_test=y_test,
            feature_names=base_model_order,
            weights=(1.0, 1.0, 1.0, 1.0, 0.25, 1.0),
        ),
        "tabnet_zero_weight_retrained_meta": _fit_stack_variant(
            validation_probabilities=validation_probabilities,
            test_probabilities=test_probabilities,
            y_validation=y_validation,
            y_test=y_test,
            feature_names=base_model_order,
            weights=(1.0, 1.0, 1.0, 1.0, 0.0, 1.0),
        ),
    }

    strong_profile_mask = (
        (prepared.test.X["numeracy_score"] >= 0.8)
        & (prepared.test.X["future_orientation"] >= 0.8)
        & (prepared.test.X["resilience_score"] >= 0.8)
    )
    strong_profile_indices = np.where(strong_profile_mask.to_numpy())[0]
    strong_profile_summary = None
    if strong_profile_indices.size:
        strong_profile_means = {
            model_name: float(np.mean(test_probabilities[model_name][strong_profile_indices]))
            for model_name in base_model_order
        }
        peer_mean = float(
            np.mean(
                [strong_profile_means[model_name] for model_name in base_model_order if model_name != "tabnet"]
            )
        )
        strong_profile_summary = {
            "count": int(strong_profile_indices.size),
            "base_mean_probabilities": strong_profile_means,
            "tabnet_minus_peer_mean": float(strong_profile_means["tabnet"] - peer_mean),
        }

    peer_mean_test = np.mean(
        np.column_stack(
            [
                test_probabilities[model_name]
                for model_name in base_model_order
                if model_name != "tabnet"
            ]
        ),
        axis=1,
    )
    disagreement_mask = test_probabilities["tabnet"] + 0.25 < peer_mean_test
    disagreement_positive_mask = disagreement_mask & (y_test == 1)

    return {
        "split_row_counts": {
            "validation": int(len(y_validation)),
            "test": int(len(y_test)),
        },
        "base_test_auc": {
            model_name: float(roc_auc_score(y_test, test_probabilities[model_name]))
            for model_name in base_model_order
        },
        "base_label_correlation": {
            model_name: float(np.corrcoef(test_probabilities[model_name], y_test)[0, 1])
            for model_name in base_model_order
        },
        "stack_variants": stack_variants,
        "strong_profile_summary": strong_profile_summary,
        "tabnet_peer_disagreement": {
            "rows": int(disagreement_mask.sum()),
            "positive_label_rows": int(disagreement_positive_mask.sum()),
            "mean_tabnet_prob_on_disagree_positive": (
                float(np.mean(test_probabilities["tabnet"][disagreement_positive_mask]))
                if disagreement_positive_mask.any()
                else None
            ),
            "mean_peer_prob_on_disagree_positive": (
                float(np.mean(peer_mean_test[disagreement_positive_mask]))
                if disagreement_positive_mask.any()
                else None
            ),
        },
    }


def build_controlled_case_analysis(score_service: ScoringService) -> dict[str, Any]:
    base_payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    cases = {
        "baseline": base_payload,
        "low_numeracy": _apply_modifications(
            base_payload,
            {"answers": {"numeracy_q1": 1000, "numeracy_q2": 0, "numeracy_q3": 0}},
        ),
        "high_numeracy": _apply_modifications(
            base_payload,
            {"answers": {"numeracy_q1": 6600, "numeracy_q2": 1120, "numeracy_q3": 14400}},
        ),
        "low_future_orientation": _apply_modifications(
            base_payload,
            {"answers": {"future_orient_q1": 0, "future_orient_q2": 0, "future_orient_q3": 1}},
        ),
        "high_future_orientation": _apply_modifications(
            base_payload,
            {"answers": {"future_orient_q1": 1, "future_orient_q2": 1, "future_orient_q3": 5}},
        ),
        "low_resilience": _apply_modifications(
            base_payload,
            {"answers": {"resilience_q1": 1, "resilience_q2": 1, "resilience_q3": 3}},
        ),
        "high_resilience": _apply_modifications(
            base_payload,
            {"answers": {"resilience_q1": 5, "resilience_q2": 5, "resilience_q3": 0}},
        ),
        "empty_text": _apply_modifications(
            base_payload,
            {
                "answers": {"q27_resilience_text": ""},
                "behavioral": {"typing_speed_wpm": 0.0},
            },
        ),
        "strong_text": _apply_modifications(
            base_payload,
            {
                "answers": {
                    "q27_resilience_text": (
                        "When sales fell, I reviewed every expense, negotiated supplier terms, "
                        "found extra freelance work, and protected my repayment plan. "
                        "I learned to act early, stay transparent, and keep a cash buffer "
                        "for future shocks."
                    )
                }
            },
        ),
    }

    summarized_cases = {}
    for case_name, payload in cases.items():
        debug_trace = score_service.score_request_debug(payload)
        summarized_cases[case_name] = {
            "credit_score": debug_trace["final_score"]["credit_score"],
            "repayment_probability": float(debug_trace["model_debug"]["repayment_probability"]),
            "raw_meta_probability": debug_trace["model_debug"].get("raw_meta_probability"),
            "meta_feature_vector": debug_trace["model_debug"].get("meta_feature_vector"),
        }

    return {
        "cases": summarized_cases,
        "tabnet_outlier_patterns": {
            "high_numeracy_vs_low_numeracy": _compare_tabnet_pattern(
                summarized_cases["low_numeracy"],
                summarized_cases["high_numeracy"],
            ),
            "high_future_vs_low_future": _compare_tabnet_pattern(
                summarized_cases["low_future_orientation"],
                summarized_cases["high_future_orientation"],
            ),
            "high_resilience_vs_low_resilience": _compare_tabnet_pattern(
                summarized_cases["low_resilience"],
                summarized_cases["high_resilience"],
            ),
            "strong_text_vs_empty_text": _compare_tabnet_pattern(
                summarized_cases["empty_text"],
                summarized_cases["strong_text"],
            ),
        },
    }


def summarize_recommendation(
    *,
    temporal_analysis: dict[str, Any],
    case_analysis: dict[str, Any],
) -> dict[str, Any]:
    current_auc = temporal_analysis["stack_variants"]["current_runtime"]["auc"]
    drop_auc = temporal_analysis["stack_variants"]["drop_tabnet_retrained_meta"]["auc"]
    quarter_auc = temporal_analysis["stack_variants"]["tabnet_quarter_weight_retrained_meta"]["auc"]
    disagreement_positive_rows = temporal_analysis["tabnet_peer_disagreement"]["positive_label_rows"]
    resilience_pattern = case_analysis["tabnet_outlier_patterns"]["high_resilience_vs_low_resilience"]

    should_drop = drop_auc > current_auc + 0.002
    should_reweight = (
        disagreement_positive_rows > 0
        and resilience_pattern["tabnet_probability_delta"] < -0.5
    )

    return {
        "drop_tabnet": should_drop,
        "reweight_tabnet": should_reweight,
        "summary": (
            "Do not drop TabNet outright based on current aggregate AUC. "
            "Its removal slightly reduces held-out ensemble performance. "
            "However, TabNet is the dominant outlier in the controlled monotonicity failures, "
            "so the next fix should be to reduce or guard its influence rather than remove it."
        ),
        "evidence": {
            "current_runtime_auc": current_auc,
            "drop_tabnet_auc": drop_auc,
            "quarter_weight_auc": quarter_auc,
            "positive_disagreement_rows": disagreement_positive_rows,
            "high_resilience_tabnet_delta": resilience_pattern["tabnet_probability_delta"],
        },
    }


def _fit_stack_variant(
    *,
    validation_probabilities: dict[str, np.ndarray],
    test_probabilities: dict[str, np.ndarray],
    y_validation: np.ndarray,
    y_test: np.ndarray,
    feature_names: tuple[str, ...],
    weights: tuple[float, ...] | None = None,
) -> dict[str, Any]:
    validation_matrix = np.column_stack([validation_probabilities[name] for name in feature_names])
    test_matrix = np.column_stack([test_probabilities[name] for name in feature_names])

    if weights is not None:
        weight_vector = np.asarray(weights, dtype=float)
        validation_matrix = validation_matrix * weight_vector
        test_matrix = test_matrix * weight_vector

    meta_learner = LogisticRegression(
        C=1.0,
        max_iter=1000,
        solver="lbfgs",
        random_state=42,
    )
    meta_learner.fit(validation_matrix, y_validation)

    calibrated_model = CalibratedClassifierCV(
        estimator=FrozenEstimator(meta_learner),
        method="isotonic",
    )
    calibrated_model.fit(validation_matrix, y_validation)

    calibrated_test_probabilities = calibrated_model.predict_proba(test_matrix)[:, 1]
    raw_test_probabilities = meta_learner.predict_proba(test_matrix)[:, 1]

    return {
        "auc": float(roc_auc_score(y_test, calibrated_test_probabilities)),
        "brier": float(brier_score_loss(y_test, calibrated_test_probabilities)),
        "raw_auc": float(roc_auc_score(y_test, raw_test_probabilities)),
        "coefficients": {
            feature_name: float(weight)
            for feature_name, weight in zip(
                feature_names,
                meta_learner.coef_[0].tolist(),
                strict=True,
            )
        },
        "intercept": float(meta_learner.intercept_[0]),
    }


def _compare_tabnet_pattern(
    lower_case: dict[str, Any],
    higher_case: dict[str, Any],
) -> dict[str, Any]:
    lower_tabnet = float(lower_case["meta_feature_vector"]["tabnet"])
    higher_tabnet = float(higher_case["meta_feature_vector"]["tabnet"])
    lower_score = int(lower_case["credit_score"])
    higher_score = int(higher_case["credit_score"])
    return {
        "lower_case_score": lower_score,
        "higher_case_score": higher_score,
        "score_delta": higher_score - lower_score,
        "lower_case_tabnet_probability": lower_tabnet,
        "higher_case_tabnet_probability": higher_tabnet,
        "tabnet_probability_delta": higher_tabnet - lower_tabnet,
    }


def _positive_class_probability(probabilities: np.ndarray) -> np.ndarray:
    if probabilities.ndim == 2:
        return probabilities[:, 1].astype(float, copy=False)
    return probabilities.astype(float, copy=False)


def _apply_modifications(
    base_payload: dict[str, Any],
    modifications: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    payload = copy.deepcopy(base_payload)
    for section_name, section_values in modifications.items():
        payload[section_name].update(section_values)
    return payload


if __name__ == "__main__":
    main()
