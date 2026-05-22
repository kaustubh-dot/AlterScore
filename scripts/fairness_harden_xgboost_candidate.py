"""Targeted fairness hardening and final promotion review for monotonic XGBoost.

This script keeps the constrained monotonic XGBoost architecture intact while
running a focused fairness-hardening pass:
- subgroup calibration diagnostics with emphasis on gender=non_binary
- conservative proxy-sensitive feature clipping and model regularization variants
- production-safe calibration strategy review
- final governed promotion comparison against the runtime ensemble baseline
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import expit, logit
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.ml.data_generation.generator import DEFAULT_ROW_COUNT, generate_synthetic_dataset
from backend.ml.evaluation.drift import build_psi_report_from_prepared_data
from backend.ml.evaluation.fairness import build_fairness_report
from backend.ml.evaluation.metrics import (
    compute_calibration_points,
    expected_calibration_error,
)
from backend.ml.training.classical.monotonic_constraints import (
    MONOTONIC_TREE_ACTIVE_FEATURES,
    build_monotonic_constraint_vector,
)
from scripts.retrain_tabnet_repair_experiment import to_jsonable
from scripts.train_monotonic_tree_candidates import (
    NamedProcessedModel,
    build_candidate_report,
    build_proxy_feature_risks,
    build_runtime_baseline_report,
    build_subgroup_shap_comparison,
    build_tabnet_research_report,
    build_processed_feature_frame,
    evaluate_fairness_gate,
    prepare_monotonic_tree_prepared_data,
    rebuild_prepared_data,
)

DEFAULT_OUTPUT_DIR = ROOT / "runtime" / "governed_reports" / "xgboost_fairness_hardening" / "latest"
TARGET_GROUPS: Final[tuple[str, ...]] = ("gender=non_binary",)
PROXY_SENSITIVE_FEATURES: Final[tuple[str, ...]] = (
    "session_duration_sec",
    "avg_response_time_ms",
    "financial_literacy_score",
    "numeracy_score",
    "locus_of_control",
    "answer_change_rate",
)


@dataclass(frozen=True)
class VariantSpec:
    name: str
    description: str
    model_params: dict[str, Any]
    clip_quantiles: dict[str, tuple[float, float]] | None = None


def main() -> None:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    warnings.filterwarnings(
        "ignore",
        message=r".*If you are loading a serialized model.*",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=r"Device used : cpu",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message=r"X does not have valid feature names, but LGBMClassifier was fitted with feature names",
        category=UserWarning,
    )
    args = parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    dataset = generate_synthetic_dataset(row_count=args.row_count, seed=args.seed)
    prepared, governance_artifacts, test_protected, original_prepared = (
        prepare_monotonic_tree_prepared_data(
            dataset=dataset,
            seed=args.seed,
            output_dir=output_dir / "base_prepared",
        )
    )

    current_bundle = load_runtime_artifact_bundle(strict=True)
    baseline_runtime = build_runtime_baseline_report(current_bundle, prepared)
    tabnet_research = build_tabnet_research_report(
        current_bundle,
        prepared=prepared,
        governance_artifacts=governance_artifacts,
        test_protected=test_protected,
    )

    variant_specs = build_variant_specs(args.seed)
    candidate_reports: dict[str, Any] = {}
    calibration_reviews: dict[str, Any] = {}

    for variant in variant_specs:
        variant_dir = artifacts_dir / variant.name
        variant_dir.mkdir(parents=True, exist_ok=True)
        variant_prepared, variant_artifacts, clip_summary = prepare_variant_prepared_data(
            variant=variant,
            base_prepared=prepared,
            original_prepared=original_prepared,
            output_dir=variant_dir,
        )
        model = train_xgboost_variant(
            variant=variant,
            prepared=variant_prepared,
        )
        joblib.dump(model, variant_dir / f"{variant.name}.pkl")
        candidate_report, validation_probabilities, test_probabilities, processed_test_features = (
            evaluate_variant_report(
                variant_name=variant.name,
                model=model,
                prepared=variant_prepared,
                governance_artifacts=variant_artifacts,
                test_protected=test_protected,
            )
        )
        candidate_report["variant_description"] = variant.description
        candidate_report["feature_policy"] = {
            "active_training_features": list(MONOTONIC_TREE_ACTIVE_FEATURES),
            "proxy_sensitive_features": list(PROXY_SENSITIVE_FEATURES),
            "clip_summary": clip_summary,
        }
        candidate_report["fairness_hardening_diagnostic"] = build_fairness_hardening_diagnostic(
            y_true=variant_prepared.y_test,
            probabilities=test_probabilities,
            protected_frame=test_protected,
            feature_frame=variant_prepared.feature_frame.loc[variant_prepared.test_mask].reset_index(drop=True),
            model=model,
            processed_test_features=processed_test_features,
        )
        candidate_reports[variant.name] = candidate_report
        calibration_reviews[variant.name] = build_calibration_strategy_review(
            candidate_name=variant.name,
            y_validation=variant_prepared.y_validation,
            validation_probabilities=validation_probabilities,
            validation_protected=original_prepared.validation.protected.reset_index(drop=True),
            y_test=variant_prepared.y_test,
            test_probabilities=test_probabilities,
            test_protected=test_protected,
            feature_frame=variant_prepared.feature_frame.loc[variant_prepared.test_mask].reset_index(drop=True),
        )

    report = {
        "experiment": {
            "name": "xgboost_monotonic_fairness_hardening",
            "seed": args.seed,
            "row_count": args.row_count,
            "output_dir": str(output_dir),
            "target_groups": list(TARGET_GROUPS),
            "proxy_sensitive_features": list(PROXY_SENSITIVE_FEATURES),
            "goal": (
                "Focused fairness hardening and final promotion review for the "
                "governed monotonic XGBoost production-track candidate."
            ),
        },
        "baseline_runtime": baseline_runtime,
        "tabnet_research_baseline": tabnet_research,
        "dataset_drift_report": build_psi_report_from_prepared_data(original_prepared),
        "candidate_reports": candidate_reports,
        "calibration_strategy_reviews": calibration_reviews,
        "promotion_review": build_promotion_review(
            baseline_runtime=baseline_runtime,
            candidate_reports=candidate_reports,
            calibration_reviews=calibration_reviews,
        ),
    }

    report_path = output_dir / "xgboost_fairness_hardening_report.json"
    report_path.write_text(json.dumps(to_jsonable(report), indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "report_path": str(report_path),
                **to_jsonable(report["promotion_review"]),
            },
            indent=2,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row-count", type=int, default=DEFAULT_ROW_COUNT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def build_variant_specs(seed: int) -> list[VariantSpec]:
    base_params = {
        "colsample_bytree": 1.0,
        "eval_metric": "logloss",
        "learning_rate": 0.05,
        "max_depth": 4,
        "monotone_constraints": build_monotonic_constraint_vector(),
        "n_estimators": 220,
        "n_jobs": 1,
        "objective": "binary:logistic",
        "random_state": seed,
        "subsample": 1.0,
        "tree_method": "hist",
        "verbosity": 0,
    }
    return [
        VariantSpec(
            name="xgboost_monotonic",
            description="Current governed monotonic XGBoost production-track baseline.",
            model_params=base_params,
        ),
        VariantSpec(
            name="xgboost_monotonic_proxy_regularized",
            description=(
                "Same active feature set with stronger regularization and shallower "
                "trees to reduce proxy-sensitive over-concentration."
            ),
            model_params={
                **base_params,
                "learning_rate": 0.04,
                "max_depth": 3,
                "min_child_weight": 10.0,
                "gamma": 0.2,
                "reg_alpha": 0.15,
                "reg_lambda": 3.0,
                "n_estimators": 260,
                "max_delta_step": 1.0,
            },
        ),
        VariantSpec(
            name="xgboost_monotonic_proxy_clipped",
            description=(
                "Proxy-sensitive feature clipping plus the same conservative "
                "regularization to smooth subgroup tails without removing the signals."
            ),
            model_params={
                **base_params,
                "learning_rate": 0.04,
                "max_depth": 3,
                "min_child_weight": 10.0,
                "gamma": 0.2,
                "reg_alpha": 0.15,
                "reg_lambda": 3.0,
                "n_estimators": 260,
                "max_delta_step": 1.0,
            },
            clip_quantiles={
                "session_duration_sec": (0.05, 0.95),
                "avg_response_time_ms": (0.05, 0.95),
                "financial_literacy_score": (0.02, 0.98),
                "numeracy_score": (0.02, 0.98),
                "locus_of_control": (0.02, 0.98),
                "answer_change_rate": (0.05, 0.95),
            },
        ),
    ]


def prepare_variant_prepared_data(
    *,
    variant: VariantSpec,
    base_prepared: Any,
    original_prepared: Any,
    output_dir: Path,
) -> tuple[Any, Any, dict[str, Any]]:
    feature_frame = base_prepared.feature_frame.copy()
    clip_summary = {"applied": False, "features": {}}
    if variant.clip_quantiles:
        feature_frame, clip_summary = apply_proxy_feature_clipping(
            feature_frame=feature_frame,
            train_mask=base_prepared.train_mask,
            clip_quantiles=variant.clip_quantiles,
        )
    variant_prepared = rebuild_prepared_data(
        prepared=original_prepared,
        feature_frame=feature_frame,
        mask_replacements=base_prepared.mask_replacements,
        output_dir=output_dir,
    )
    variant_artifacts = type("Artifacts", (), {})()
    variant_artifacts.preprocessor = variant_prepared.preprocessor
    variant_artifacts.text_pca = original_prepared.text_pca
    return variant_prepared, variant_artifacts, clip_summary


def apply_proxy_feature_clipping(
    *,
    feature_frame: pd.DataFrame,
    train_mask: pd.Series,
    clip_quantiles: dict[str, tuple[float, float]],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    updated = feature_frame.copy()
    train_frame = updated.loc[train_mask.to_numpy()].reset_index(drop=True)
    summary = {"applied": True, "features": {}}
    for feature_name, (lower_q, upper_q) in clip_quantiles.items():
        if feature_name not in updated.columns:
            continue
        lower = float(train_frame[feature_name].quantile(lower_q))
        upper = float(train_frame[feature_name].quantile(upper_q))
        if lower > upper:
            lower, upper = upper, lower
        updated.loc[:, feature_name] = updated[feature_name].clip(lower=lower, upper=upper)
        summary["features"][feature_name] = {
            "lower_quantile": float(lower_q),
            "upper_quantile": float(upper_q),
            "lower_bound": lower,
            "upper_bound": upper,
        }
    return updated, summary


def train_xgboost_variant(*, variant: VariantSpec, prepared: Any) -> Any:
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("xgboost is required for fairness hardening experiments.") from exc

    X_train = build_processed_feature_frame(prepared, prepared.train_mask)
    model = XGBClassifier(**variant.model_params)
    model.fit(X_train, prepared.y_train)
    return model


def evaluate_variant_report(
    *,
    variant_name: str,
    model: Any,
    prepared: Any,
    governance_artifacts: Any,
    test_protected: pd.DataFrame,
) -> tuple[dict[str, Any], np.ndarray, np.ndarray, pd.DataFrame]:
    validation_processed = build_processed_feature_frame(prepared, prepared.validation_mask)
    test_processed = build_processed_feature_frame(prepared, prepared.test_mask)
    named_model = NamedProcessedModel(
        model=model,
        feature_names=tuple(prepared.preprocessor.get_feature_names_out().tolist()),
    )
    validation_probabilities = np.asarray(
        named_model.predict_proba(validation_processed)[:, 1],
        dtype=float,
    )
    test_probabilities = np.asarray(named_model.predict_proba(test_processed)[:, 1], dtype=float)
    report = build_candidate_report(
        candidate_name=variant_name,
        model=model,
        prepared=prepared,
        governance_artifacts=governance_artifacts,
        test_protected=test_protected,
    )
    return report, validation_probabilities, test_probabilities, test_processed


def build_fairness_hardening_diagnostic(
    *,
    y_true: np.ndarray,
    probabilities: np.ndarray,
    protected_frame: pd.DataFrame,
    feature_frame: pd.DataFrame,
    model: Any,
    processed_test_features: pd.DataFrame,
) -> dict[str, Any]:
    calibration_risk_groups = find_top_calibration_risk_groups(
        y_true=y_true,
        probabilities=probabilities,
        protected_frame=protected_frame,
    )
    target_groups = list(dict.fromkeys(list(TARGET_GROUPS) + calibration_risk_groups))
    return {
        "target_groups": target_groups,
        "subgroup_probability_diagnostics": build_subgroup_probability_diagnostics(
            y_true=y_true,
            probabilities=probabilities,
            protected_frame=protected_frame,
            groups=target_groups,
        ),
        "proxy_feature_review": build_target_group_proxy_review(
            feature_frame=feature_frame,
            protected_frame=protected_frame,
            groups=target_groups,
        ),
        "subgroup_shap_comparison": build_subgroup_shap_comparison(
            model=model,
            processed_test_features=processed_test_features,
            protected_frame=protected_frame,
            target_groups=target_groups,
        ),
    }


def find_top_calibration_risk_groups(
    *,
    y_true: np.ndarray,
    probabilities: np.ndarray,
    protected_frame: pd.DataFrame,
    top_k: int = 3,
) -> list[str]:
    fairness_report = build_fairness_report(
        y_true,
        probabilities,
        protected_frame,
        feature_frame=None,
    )
    candidates: list[tuple[float, str]] = []
    groups = fairness_report.get("calibration_parity", {}).get("groups", {})
    for protected_name, group_payload in groups.items():
        for group_value, metrics in group_payload.items():
            ece_gap = float(metrics.get("ece_gap_from_overall", 0.0))
            if int(metrics.get("n_samples", 0)) < 30:
                continue
            candidates.append((ece_gap, f"{protected_name}={group_value}"))
    candidates.sort(reverse=True)
    return [group_name for _, group_name in candidates[:top_k]]


def build_subgroup_probability_diagnostics(
    *,
    y_true: np.ndarray,
    probabilities: np.ndarray,
    protected_frame: pd.DataFrame,
    groups: list[str],
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    y_true_array = np.asarray(y_true, dtype=int)
    probability_array = np.asarray(probabilities, dtype=float)
    for group_name in groups:
        protected_name, group_value = group_name.split("=", 1)
        attribute = protected_frame[protected_name].fillna("__MISSING__").astype(str)
        mask = (attribute == group_value).to_numpy(dtype=bool)
        n_samples = int(mask.sum())
        if n_samples == 0:
            output[group_name] = {"n_samples": 0, "available": False}
            continue
        subgroup_true = y_true_array[mask]
        subgroup_prob = probability_array[mask]
        output[group_name] = {
            "available": True,
            "n_samples": n_samples,
            "auc_roc": safe_auc(subgroup_true, subgroup_prob),
            "brier_score": float(brier_score_loss(subgroup_true, subgroup_prob)),
            "expected_calibration_error": float(
                expected_calibration_error(subgroup_true, subgroup_prob)
            ),
            "positive_rate": float(subgroup_true.mean()),
            "probability_summary": {
                "mean": float(subgroup_prob.mean()),
                "std": float(subgroup_prob.std(ddof=0)),
                "min": float(subgroup_prob.min()),
                "p05": float(np.percentile(subgroup_prob, 5)),
                "p50": float(np.percentile(subgroup_prob, 50)),
                "p95": float(np.percentile(subgroup_prob, 95)),
                "max": float(subgroup_prob.max()),
            },
            "sharpness_std": float(subgroup_prob.std(ddof=0)),
            "high_confidence_share": float(
                np.mean((subgroup_prob <= 0.2) | (subgroup_prob >= 0.8))
            ),
            "uncertain_band_share": float(
                np.mean((subgroup_prob >= 0.4) & (subgroup_prob <= 0.6))
            ),
            "reliability_curve": compute_calibration_points(
                subgroup_true,
                subgroup_prob,
                n_bins=10,
            ),
        }
    return output


def build_target_group_proxy_review(
    *,
    feature_frame: pd.DataFrame,
    protected_frame: pd.DataFrame,
    groups: list[str],
) -> dict[str, Any]:
    base_proxy = build_proxy_feature_risks(
        feature_frame,
        protected_frame,
        active_feature_names=MONOTONIC_TREE_ACTIVE_FEATURES,
    )
    output: dict[str, Any] = {}
    for group_name in groups:
        protected_name, group_value = group_name.split("=", 1)
        matches = [
            row
            for row in base_proxy.get(protected_name, [])
            if row.get("group") == group_value
        ]
        top_shifted = matches[0]["top_shifted_features"] if matches else []
        filtered_shifted = [
            row
            for row in top_shifted
            if row["feature"] in PROXY_SENSITIVE_FEATURES
        ]
        output[group_name] = {
            "top_proxy_sensitive_shifts": filtered_shifted,
            "all_top_shifts": top_shifted,
        }
    return output


def build_calibration_strategy_review(
    *,
    candidate_name: str,
    y_validation: np.ndarray,
    validation_probabilities: np.ndarray,
    validation_protected: pd.DataFrame,
    y_test: np.ndarray,
    test_probabilities: np.ndarray,
    test_protected: pd.DataFrame,
    feature_frame: pd.DataFrame,
) -> dict[str, Any]:
    strategies = fit_calibration_strategies(
        y_validation=y_validation,
        validation_probabilities=validation_probabilities,
        validation_protected=validation_protected,
    )
    results: dict[str, Any] = {}
    for strategy_name, strategy in strategies.items():
        calibrated_test = np.asarray(strategy["apply"](test_probabilities, test_protected), dtype=float)
        fairness_report = build_fairness_report(
            y_test,
            calibrated_test,
            test_protected,
            feature_frame=feature_frame,
        )
        fairness_gate = evaluate_fairness_gate(fairness_report)
        subgroup_diagnostics = build_subgroup_probability_diagnostics(
            y_true=y_test,
            probabilities=calibrated_test,
            protected_frame=test_protected,
            groups=list(TARGET_GROUPS),
        )
        results[strategy_name] = {
            "production_safe": bool(strategy["production_safe"]),
            "requires_protected_attribute_at_runtime": bool(
                strategy["requires_protected_attribute_at_runtime"]
            ),
            "test_metrics": {
                "auc_roc": safe_auc(y_test, calibrated_test),
                "brier_score": float(brier_score_loss(y_test, calibrated_test)),
                "expected_calibration_error": float(
                    expected_calibration_error(y_test, calibrated_test)
                ),
            },
            "fairness_gate": fairness_gate,
            "fairness_summary": {
                "worst_auc_gap": fairness_report["worst_auc_gap"],
                "flagged_groups": fairness_report["flagged_groups"],
                "max_ece_gap": fairness_report["calibration_parity"]["max_ece_gap"],
            },
            "target_group_diagnostics": subgroup_diagnostics,
        }
    recommended = choose_recommended_calibration_strategy(results)
    return {
        "candidate_name": candidate_name,
        "strategies": results,
        "recommended_production_strategy": recommended,
        "rejected_runtime_unsafe_strategies": [
            name
            for name, payload in results.items()
            if payload["requires_protected_attribute_at_runtime"]
        ],
    }


def fit_calibration_strategies(
    *,
    y_validation: np.ndarray,
    validation_probabilities: np.ndarray,
    validation_protected: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    validation_probabilities = np.asarray(validation_probabilities, dtype=float)
    y_validation = np.asarray(y_validation, dtype=int)

    isotonic = IsotonicRegression(out_of_bounds="clip")
    isotonic.fit(validation_probabilities, y_validation)

    platt = LogisticRegression(max_iter=1000, solver="lbfgs")
    platt.fit(validation_probabilities.reshape(-1, 1), y_validation)

    temperature = fit_temperature_scaler(
        validation_probabilities=validation_probabilities,
        y_validation=y_validation,
    )

    groupwise_gender_isotonic = fit_groupwise_isotonic_calibrator(
        probabilities=validation_probabilities,
        y_true=y_validation,
        protected_values=validation_protected["gender"].reset_index(drop=True),
        min_support=40,
    )

    return {
        "raw": {
            "production_safe": True,
            "requires_protected_attribute_at_runtime": False,
            "apply": lambda probs, _: np.asarray(probs, dtype=float),
        },
        "temperature": {
            "production_safe": True,
            "requires_protected_attribute_at_runtime": False,
            "apply": lambda probs, _: apply_temperature_scaling(
                np.asarray(probs, dtype=float),
                temperature,
            ),
        },
        "isotonic": {
            "production_safe": True,
            "requires_protected_attribute_at_runtime": False,
            "apply": lambda probs, _: isotonic.predict(np.asarray(probs, dtype=float)),
        },
        "platt": {
            "production_safe": True,
            "requires_protected_attribute_at_runtime": False,
            "apply": lambda probs, _: platt.predict_proba(
                np.asarray(probs, dtype=float).reshape(-1, 1)
            )[:, 1],
        },
        "oracle_gender_isotonic": {
            "production_safe": False,
            "requires_protected_attribute_at_runtime": True,
            "apply": lambda probs, protected: apply_groupwise_isotonic(
                np.asarray(probs, dtype=float),
                protected["gender"].reset_index(drop=True),
                groupwise_gender_isotonic,
            ),
        },
    }


def fit_temperature_scaler(
    *,
    validation_probabilities: np.ndarray,
    y_validation: np.ndarray,
) -> float:
    clipped = np.clip(np.asarray(validation_probabilities, dtype=float), 1e-6, 1.0 - 1e-6)
    logits = logit(clipped)

    def objective(temperature: float) -> float:
        scaled = expit(logits / max(temperature, 1e-3))
        return float(
            -np.mean(
                y_validation * np.log(np.clip(scaled, 1e-6, 1.0))
                + (1 - y_validation) * np.log(np.clip(1.0 - scaled, 1e-6, 1.0))
            )
        )

    optimum = minimize_scalar(objective, bounds=(0.5, 3.0), method="bounded")
    return float(optimum.x)


def apply_temperature_scaling(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    clipped = np.clip(np.asarray(probabilities, dtype=float), 1e-6, 1.0 - 1e-6)
    return expit(logit(clipped) / max(float(temperature), 1e-3))


def fit_groupwise_isotonic_calibrator(
    *,
    probabilities: np.ndarray,
    y_true: np.ndarray,
    protected_values: pd.Series,
    min_support: int,
) -> dict[str, Any]:
    probabilities = np.asarray(probabilities, dtype=float)
    y_true = np.asarray(y_true, dtype=int)
    groups = protected_values.fillna("__MISSING__").astype(str).reset_index(drop=True)
    global_isotonic = IsotonicRegression(out_of_bounds="clip")
    global_isotonic.fit(probabilities, y_true)
    group_models: dict[str, Any] = {}
    for group_value in sorted(groups.unique().tolist()):
        mask = (groups == group_value).to_numpy(dtype=bool)
        if int(mask.sum()) < min_support or len(np.unique(y_true[mask])) < 2:
            continue
        subgroup_model = IsotonicRegression(out_of_bounds="clip")
        subgroup_model.fit(probabilities[mask], y_true[mask])
        group_models[group_value] = subgroup_model
    return {"global": global_isotonic, "groups": group_models}


def apply_groupwise_isotonic(
    probabilities: np.ndarray,
    protected_values: pd.Series,
    calibrator: dict[str, Any],
) -> np.ndarray:
    probabilities = np.asarray(probabilities, dtype=float)
    groups = protected_values.fillna("__MISSING__").astype(str).reset_index(drop=True)
    output = np.asarray(calibrator["global"].predict(probabilities), dtype=float)
    for group_value, subgroup_model in calibrator["groups"].items():
        mask = (groups == group_value).to_numpy(dtype=bool)
        if mask.any():
            output[mask] = subgroup_model.predict(probabilities[mask])
    return output


def choose_recommended_calibration_strategy(strategy_results: dict[str, Any]) -> str:
    def sort_key(item: tuple[str, Any]) -> tuple[float, float, float]:
        _, payload = item
        diagnostics = payload.get("target_group_diagnostics", {}).get("gender=non_binary", {})
        subgroup_ece = float(diagnostics.get("expected_calibration_error", 1.0))
        overall_ece = float(payload["test_metrics"]["expected_calibration_error"])
        auc_penalty = -float(payload["test_metrics"]["auc_roc"])
        return (subgroup_ece, overall_ece, auc_penalty)

    safe_items = [
        item
        for item in strategy_results.items()
        if item[1]["production_safe"] and item[1]["fairness_gate"]["passed"]
    ]
    if not safe_items:
        safe_items = [
            item for item in strategy_results.items() if item[1]["production_safe"]
        ]
    return sorted(safe_items, key=sort_key)[0][0]


def build_promotion_review(
    *,
    baseline_runtime: dict[str, Any],
    candidate_reports: dict[str, Any],
    calibration_reviews: dict[str, Any],
) -> dict[str, Any]:
    runtime_auc = float(baseline_runtime["test_metrics"]["auc_roc"])
    eligible_candidates = [
        (name, payload)
        for name, payload in candidate_reports.items()
        if payload["promotion_eligible"]
    ]
    eligible_candidates.sort(
        key=lambda item: (
            -float(item[1]["test_metrics"]["auc_roc"]),
            float(item[1]["test_metrics"]["expected_calibration_error"]),
        )
    )
    leading_candidate = eligible_candidates[0][0] if eligible_candidates else None
    leading_strategy = (
        calibration_reviews[leading_candidate]["recommended_production_strategy"]
        if leading_candidate
        else None
    )
    return {
        "promotion_ready_candidate": leading_candidate,
        "recommended_probability_output": leading_strategy,
        "runtime_baseline_auc": runtime_auc,
        "candidate_auc_lift": (
            round(
                float(candidate_reports[leading_candidate]["test_metrics"]["auc_roc"]) - runtime_auc,
                4,
            )
            if leading_candidate
            else None
        ),
        "strict_governance_kept": True,
        "summary": (
            "Use the leading monotonic XGBoost candidate only if the final "
            "fairness hardening review preserves promotion eligibility under the "
            "existing governance stack."
        ),
    }


def safe_auc(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=int)
    probabilities = np.asarray(probabilities, dtype=float)
    if len(np.unique(y_true)) < 2 or len(np.unique(probabilities)) < 2:
        return 0.5
    return float(roc_auc_score(y_true, probabilities))


if __name__ == "__main__":
    main()
