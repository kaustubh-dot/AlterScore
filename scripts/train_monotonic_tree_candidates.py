"""Governed monotonic tree candidate training for AlterScore.

This script builds production-track LightGBM and XGBoost candidates using:
- temporal validation
- monotonic constraints on critical interpretable features
- neutralized operational metadata
- masked brittle composite features
- fairness, calibration, drift, and counterfactual governance audits

It does not modify the runtime production bundle.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.ml.data_generation.generator import DEFAULT_ROW_COUNT, generate_synthetic_dataset
from backend.ml.evaluation.drift import build_psi_report_from_prepared_data
from backend.ml.evaluation.fairness import RED_AUC_GAP_THRESHOLD, build_fairness_report
from backend.ml.explainability.global_importance import (
    build_global_importance_report_for_candidate_models,
)
from backend.ml.inference.ensemble_adapter import (
    EnsembleInferenceBundle,
    predict_ensemble_proba,
)
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES
from backend.ml.preprocessing.pipeline import (
    align_text_features_from_raw_text,
    fit_preprocessor,
    prepare_temporal_data,
    transform_features,
)
from backend.ml.training.classical.monotonic_constraints import (
    MONOTONIC_TREE_ACTIVE_FEATURES,
    MONOTONIC_TREE_MASKED_FEATURES,
    apply_monotonic_tree_feature_masking,
    build_monotonic_constraint_vector,
    neutralize_operational_metadata_for_training,
)
from scripts.retrain_tabnet_repair_experiment import (
    PreparedCompatibleData,
    build_calibration_audit,
    build_counterfactual_stability_audit,
    build_disagreement_audit,
    build_sensitivity_for_probability_fn,
    evaluate_counterfactual_acceptance_gate,
    evaluate_metadata_stability_gate,
    evaluate_monotonic_acceptance_gates,
    evaluate_probability_model,
    to_jsonable,
)

DEFAULT_OUTPUT_DIR = ROOT / "runtime" / "governed_reports" / "monotonic_tree_candidates" / "latest"
MONOTONIC_AUDIT_FEATURES: tuple[str, ...] = (
    "resilience_score",
    "future_orientation",
    "numeracy_score",
    "scroll_hesitation_score",
    "text_agency_score",
)


@dataclass(frozen=True)
class NamedProcessedModel:
    model: Any
    feature_names: tuple[str, ...]

    def predict_proba(self, processed_features: Any) -> np.ndarray:
        if isinstance(processed_features, pd.DataFrame):
            frame = processed_features.loc[:, list(self.feature_names)]
        else:
            frame = pd.DataFrame(
                np.asarray(processed_features, dtype=float),
                columns=list(self.feature_names),
            )
        return np.asarray(self.model.predict_proba(frame), dtype=float)


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
        message=r".*LightGBM binary classifier with TreeExplainer shap values output has changed.*",
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
    (output_dir / "artifacts").mkdir(parents=True, exist_ok=True)

    dataset = generate_synthetic_dataset(row_count=args.row_count, seed=args.seed)
    prepared, governance_artifacts, test_protected, original_prepared = prepare_monotonic_tree_prepared_data(
        dataset=dataset,
        seed=args.seed,
        output_dir=output_dir,
    )

    current_bundle = load_runtime_artifact_bundle(strict=True)
    baseline_report = build_runtime_baseline_report(current_bundle, prepared)
    tabnet_research_report = build_tabnet_research_report(
        current_bundle,
        prepared=prepared,
        governance_artifacts=governance_artifacts,
        test_protected=test_protected,
    )

    candidates = train_monotonic_candidates(
        prepared=prepared,
        random_state=args.seed,
        output_dir=output_dir / "artifacts",
    )

    candidate_reports = {
        candidate_name: build_candidate_report(
            candidate_name=candidate_name,
            model=model,
            prepared=prepared,
            governance_artifacts=governance_artifacts,
            test_protected=test_protected,
        )
        for candidate_name, model in candidates.items()
    }

    report = {
        "experiment": {
            "name": "monotonic_tree_candidate_governance",
            "seed": args.seed,
            "row_count": args.row_count,
            "output_dir": str(output_dir),
            "production_track_goal": (
                "Governed constrained-tree candidates for primary production scoring."
            ),
            "runtime_disagreement_mitigation_remains_enabled": True,
            "active_training_features": list(MONOTONIC_TREE_ACTIVE_FEATURES),
            "masked_features": list(MONOTONIC_TREE_MASKED_FEATURES),
            "monotonic_constraint_vector": list(build_monotonic_constraint_vector()),
            "monotonic_audit_features": list(MONOTONIC_AUDIT_FEATURES),
        },
        "baseline_runtime": baseline_report,
        "tabnet_research_baseline": tabnet_research_report,
        "dataset_drift_report": build_psi_report_from_prepared_data(original_prepared),
        "candidate_reports": candidate_reports,
        "recommendation": build_recommendation(candidate_reports),
        "tabnet_positioning_note": (
            "TabNet remains a research benchmark and optional auxiliary contributor. "
            "It is not treated as the primary trusted production scorer."
        ),
    }

    report_path = output_dir / "monotonic_tree_candidate_report.json"
    report_path.write_text(json.dumps(to_jsonable(report), indent=2), encoding="utf-8")
    print(json.dumps({"report_path": str(report_path), **to_jsonable(report["recommendation"])}, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row-count", type=int, default=DEFAULT_ROW_COUNT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def prepare_monotonic_tree_prepared_data(
    *,
    dataset: pd.DataFrame,
    seed: int,
    output_dir: Path,
) -> tuple[PreparedCompatibleData, Any, pd.DataFrame, Any]:
    aligned_dataset, raw_text_embeddings = align_text_features_from_raw_text(dataset)
    original_prepared = prepare_temporal_data(
        aligned_dataset,
        raw_text_embeddings=raw_text_embeddings,
        text_pca_random_state=seed,
        text_pca_artifact_path=None,
    )
    train_mask = dataset["cohort_month"].isin(range(1, 9))
    policy_feature_frame = neutralize_operational_metadata_for_training(
        original_prepared.feature_frame
    )
    policy_feature_frame, mask_replacements = apply_monotonic_tree_feature_masking(
        policy_feature_frame,
        train_mask=train_mask,
        masked_features=MONOTONIC_TREE_MASKED_FEATURES,
    )
    prepared = rebuild_prepared_data(
        prepared=original_prepared,
        feature_frame=policy_feature_frame,
        mask_replacements=mask_replacements,
        output_dir=output_dir,
    )
    governance_artifacts = SimpleNamespace(
        preprocessor=prepared.preprocessor,
        text_pca=original_prepared.text_pca,
    )
    test_protected = original_prepared.test.protected.reset_index(drop=True)
    return prepared, governance_artifacts, test_protected, original_prepared
def rebuild_prepared_data(
    *,
    prepared: Any,
    feature_frame: pd.DataFrame,
    mask_replacements: dict[str, Any],
    output_dir: Path,
    ) -> PreparedCompatibleData:
    train_mask = prepared.feature_frame.index.isin(prepared.train.indices)
    validation_mask = prepared.feature_frame.index.isin(prepared.validation.indices)
    test_mask = prepared.feature_frame.index.isin(prepared.test.indices)

    preprocessor = fit_preprocessor(
        feature_frame.loc[train_mask].reset_index(drop=True),
        artifact_path=output_dir / "monotonic_tree_preprocessor.pkl",
    )
    X_processed = transform_features(preprocessor, feature_frame)
    return PreparedCompatibleData(
        preprocessor=preprocessor,
        feature_frame=feature_frame.reset_index(drop=True),
        X_processed=np.asarray(X_processed, dtype=float),
        train_mask=pd.Series(train_mask),
        validation_mask=pd.Series(validation_mask),
        test_mask=pd.Series(test_mask),
        y_train=prepared.train.y.to_numpy(dtype=int),
        y_validation=prepared.validation.y.to_numpy(dtype=int),
        y_test=prepared.test.y.to_numpy(dtype=int),
        masked_features=MONOTONIC_TREE_MASKED_FEATURES,
        mask_replacements=mask_replacements,
    )


def build_processed_feature_frame(
    prepared: PreparedCompatibleData,
    row_mask: pd.Series,
) -> pd.DataFrame:
    feature_names = prepared.preprocessor.get_feature_names_out().tolist()
    return pd.DataFrame(
        prepared.X_processed[row_mask.to_numpy()],
        columns=feature_names,
    )


def train_monotonic_candidates(
    *,
    prepared: PreparedCompatibleData,
    random_state: int,
    output_dir: Path,
) -> dict[str, Any]:
    try:
        from lightgbm import LGBMClassifier
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("lightgbm is required for monotonic candidate training.") from exc

    try:
        from xgboost import XGBClassifier
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("xgboost is required for monotonic candidate training.") from exc

    constraints = build_monotonic_constraint_vector()
    X_train = build_processed_feature_frame(prepared, prepared.train_mask)
    y_train = prepared.y_train

    candidates = {
        "xgboost_monotonic": XGBClassifier(
            colsample_bytree=1.0,
            eval_metric="logloss",
            learning_rate=0.05,
            max_depth=4,
            monotone_constraints=constraints,
            n_estimators=220,
            n_jobs=1,
            objective="binary:logistic",
            random_state=random_state,
            subsample=1.0,
            tree_method="hist",
            verbosity=0,
        ),
        "lightgbm_monotonic": LGBMClassifier(
            bagging_seed=random_state,
            colsample_bytree=1.0,
            data_random_seed=random_state,
            deterministic=True,
            feature_fraction_seed=random_state,
            force_col_wise=True,
            learning_rate=0.05,
            monotone_constraints=list(constraints),
            monotone_constraints_method="advanced",
            n_estimators=220,
            n_jobs=1,
            objective="binary",
            random_state=random_state,
            subsample=1.0,
            verbose=-1,
        ),
    }

    for candidate_name, model in candidates.items():
        model.fit(X_train, y_train)
        joblib.dump(model, output_dir / f"{candidate_name}.pkl")

    return candidates


def build_candidate_report(
    *,
    candidate_name: str,
    model: Any,
    prepared: PreparedCompatibleData,
    governance_artifacts: Any,
    test_protected: pd.DataFrame,
) -> dict[str, Any]:
    named_model = NamedProcessedModel(
        model=model,
        feature_names=tuple(prepared.preprocessor.get_feature_names_out().tolist()),
    )
    validation_processed = build_processed_feature_frame(prepared, prepared.validation_mask)
    test_processed = build_processed_feature_frame(prepared, prepared.test_mask)
    validation_probabilities = np.asarray(named_model.predict_proba(validation_processed)[:, 1], dtype=float)
    test_probabilities = np.asarray(named_model.predict_proba(test_processed)[:, 1], dtype=float)
    probability_fn = lambda frame: named_model.predict_proba(  # noqa: E731
        pd.DataFrame(
            transform_features(prepared.preprocessor, frame),
            columns=prepared.preprocessor.get_feature_names_out().tolist(),
        )
    )[:, 1]

    sensitivity = build_sensitivity_for_probability_fn(
        artifacts=governance_artifacts,
        probability_fn=probability_fn,
        label=candidate_name,
        masked_features=prepared.masked_features,
        mask_replacements=prepared.mask_replacements,
    )
    acceptance_gates = evaluate_monotonic_acceptance_gates(sensitivity)
    metadata_gate = evaluate_metadata_stability_gate(
        artifacts=governance_artifacts,
        tabnet_model=named_model,
        max_allowed_delta=0.02,
    )
    counterfactual_audit = build_counterfactual_stability_audit(
        artifacts=governance_artifacts,
        prepared=prepared,
        probability_fn=probability_fn,
        sample_size=192,
        tolerance=0.01,
        features=MONOTONIC_AUDIT_FEATURES,
        step=0.12,
    )
    counterfactual_gate = evaluate_counterfactual_acceptance_gate(
        counterfactual_audit,
        max_violation_rate=0.02,
        max_worst_delta=0.05,
    )
    fairness_report = build_fairness_report(
        prepared.y_test,
        test_probabilities,
        test_protected,
        feature_frame=prepared.feature_frame.loc[prepared.test_mask].reset_index(drop=True),
    )
    fairness_gate = evaluate_fairness_gate(fairness_report)
    fairness_diagnostic = build_fairness_diagnostic(
        fairness_report=fairness_report,
        feature_frame=prepared.feature_frame.loc[prepared.test_mask].reset_index(drop=True),
        protected_frame=test_protected,
        model=model,
        processed_test_features=test_processed,
        active_feature_names=MONOTONIC_TREE_ACTIVE_FEATURES,
    )
    global_importance_report, selected_model_name = build_global_importance_report_for_candidate_models(
        {candidate_name: model},
        train_processed_features=build_processed_feature_frame(prepared, prepared.train_mask).to_numpy(dtype=float),
        test_processed_features=test_processed,
        model_stats=[
            evaluate_probability_model(
                y_true=prepared.y_test,
                probabilities=test_probabilities,
                model_name=candidate_name,
                split="test_months_11_12",
            )
        ],
        candidate_model_types={candidate_name: "classical_monotonic"},
        feature_names=ALL_MODEL_FEATURES,
    )

    return {
        "promotion_eligible": bool(
            acceptance_gates["passed"]
            and metadata_gate["passed"]
            and counterfactual_gate["passed"]
            and fairness_gate["passed"]
        ),
        "test_metrics": evaluate_probability_model(
            y_true=prepared.y_test,
            probabilities=test_probabilities,
            model_name=candidate_name,
            split="test_months_11_12",
        ),
        "validation_metrics": evaluate_probability_model(
            y_true=prepared.y_validation,
            probabilities=validation_probabilities,
            model_name=candidate_name,
            split="validation_months_9_10",
        ),
        "calibration_audit": build_calibration_audit(
            y_validation=prepared.y_validation,
            validation_probabilities=validation_probabilities,
            y_test=prepared.y_test,
            test_probabilities=test_probabilities,
        ),
        "acceptance_gates": acceptance_gates,
        "metadata_stability_gate": metadata_gate,
        "counterfactual_gate": counterfactual_gate,
        "fairness_gate": fairness_gate,
        "counterfactual_audit": counterfactual_audit,
        "fairness_diagnostic": fairness_diagnostic,
        "fairness_summary": {
            "overall_auc": fairness_report["overall_auc"],
            "worst_auc_gap": fairness_report["worst_auc_gap"],
            "flagged_groups": fairness_report["flagged_groups"],
            "individual_fairness_flagged_pair_share": fairness_report["individual_fairness_proxy"]["flagged_pair_share"],
            "verdict": fairness_report["verdict"],
        },
        "global_importance_source_model": selected_model_name,
        "top_global_importance_features": global_importance_report["items"][:10],
    }


def build_runtime_baseline_report(bundle: Any, prepared: PreparedCompatibleData) -> dict[str, Any]:
    test_processed = prepared.X_processed[prepared.test_mask.to_numpy()]
    if bundle.base_models is not None and bundle.stacking_config is not None:
        ensemble_bundle = EnsembleInferenceBundle(
            stacking_model=bundle.model,
            base_models=bundle.base_models,
            base_model_order=tuple(bundle.stacking_config["base_model_order"]),
            preprocessor=bundle.preprocessor,
            stacking_config=bundle.stacking_config,
        )
        probabilities = predict_ensemble_proba(ensemble_bundle, test_processed)[:, 1]
    else:
        probabilities = bundle.model.predict_proba(test_processed)[:, 1]
    return {
        "runtime_model_name": bundle.report.runtime_model_name,
        "runtime_model_type": bundle.report.runtime_model_type,
        "test_metrics": evaluate_probability_model(
            y_true=prepared.y_test,
            probabilities=np.asarray(probabilities, dtype=float),
            model_name=str(bundle.report.runtime_model_name or "runtime_model"),
            split="test_months_11_12",
        ),
    }


def build_tabnet_research_report(
    bundle: Any,
    *,
    prepared: PreparedCompatibleData,
    governance_artifacts: Any,
    test_protected: pd.DataFrame,
) -> dict[str, Any] | None:
    if bundle.base_models is None or "tabnet" not in bundle.base_models:
        return None
    tabnet_model = bundle.base_models["tabnet"]
    validation_processed = prepared.X_processed[prepared.validation_mask.to_numpy()]
    test_processed = prepared.X_processed[prepared.test_mask.to_numpy()]
    validation_probabilities = np.asarray(tabnet_model.predict_proba(validation_processed)[:, 1], dtype=float)
    test_probabilities = np.asarray(tabnet_model.predict_proba(test_processed)[:, 1], dtype=float)
    probability_fn = lambda frame: tabnet_model.predict_proba(  # noqa: E731
        transform_features(prepared.preprocessor, frame)
    )[:, 1]
    sensitivity = build_sensitivity_for_probability_fn(
        artifacts=governance_artifacts,
        probability_fn=probability_fn,
        label="tabnet_research",
        masked_features=prepared.masked_features,
        mask_replacements=prepared.mask_replacements,
    )
    counterfactual_audit = build_counterfactual_stability_audit(
        artifacts=governance_artifacts,
        prepared=prepared,
        probability_fn=probability_fn,
        sample_size=192,
        tolerance=0.01,
        features=MONOTONIC_AUDIT_FEATURES,
        step=0.12,
    )
    fairness_report = build_fairness_report(
        prepared.y_test,
        test_probabilities,
        test_protected,
        feature_frame=prepared.feature_frame.loc[prepared.test_mask].reset_index(drop=True),
    )
    return {
        "test_metrics": evaluate_probability_model(
            y_true=prepared.y_test,
            probabilities=test_probabilities,
            model_name="tabnet_research_baseline",
            split="test_months_11_12",
        ),
        "validation_metrics": evaluate_probability_model(
            y_true=prepared.y_validation,
            probabilities=validation_probabilities,
            model_name="tabnet_research_baseline",
            split="validation_months_9_10",
        ),
        "acceptance_gates": evaluate_monotonic_acceptance_gates(sensitivity),
        "counterfactual_gate": evaluate_counterfactual_acceptance_gate(
            counterfactual_audit,
            max_violation_rate=0.02,
            max_worst_delta=0.05,
        ),
        "counterfactual_audit": counterfactual_audit,
        "fairness_gate": evaluate_fairness_gate(fairness_report),
        "fairness_summary": {
            "overall_auc": fairness_report["overall_auc"],
            "worst_auc_gap": fairness_report["worst_auc_gap"],
            "flagged_groups": fairness_report["flagged_groups"],
            "individual_fairness_flagged_pair_share": fairness_report["individual_fairness_proxy"]["flagged_pair_share"],
        },
        "disagreement_audit": build_disagreement_audit(
            artifacts=governance_artifacts_to_bundle(bundle),
            tabnet_model=tabnet_model,
            prepared=prepared,
        ),
    }


def governance_artifacts_to_bundle(bundle: Any) -> Any:
    return SimpleNamespace(
        model=bundle.model,
        base_models=bundle.base_models,
        preprocessor=bundle.preprocessor,
        stacking_config=bundle.stacking_config,
        text_pca=bundle.text_pca,
    )


def evaluate_fairness_gate(fairness_report: dict[str, Any]) -> dict[str, Any]:
    flagged_groups = list(fairness_report.get("flagged_groups", []))
    worst_auc_gap = float(fairness_report.get("worst_auc_gap", 0.0))
    return {
        "passed": not flagged_groups and worst_auc_gap <= RED_AUC_GAP_THRESHOLD,
        "max_allowed_worst_auc_gap": float(RED_AUC_GAP_THRESHOLD),
        "worst_auc_gap": worst_auc_gap,
        "flagged_groups": flagged_groups,
        "verdict": fairness_report.get("verdict", ""),
    }


def build_fairness_diagnostic(
    *,
    fairness_report: dict[str, Any],
    feature_frame: pd.DataFrame,
    protected_frame: pd.DataFrame,
    model: Any,
    processed_test_features: pd.DataFrame,
    active_feature_names: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "failing_groups": fairness_report.get("flagged_groups", []),
        "group_metric_failures": fairness_report.get("groups", {}),
        "calibration_parity": fairness_report.get("calibration_parity", {}),
        "individual_fairness_proxy": fairness_report.get("individual_fairness_proxy", {}),
        "proxy_feature_risks": build_proxy_feature_risks(
            feature_frame,
            protected_frame,
            active_feature_names=active_feature_names,
        ),
        "subgroup_shap_comparison": build_subgroup_shap_comparison(
            model=model,
            processed_test_features=processed_test_features,
            protected_frame=protected_frame,
            flagged_groups=fairness_report.get("flagged_groups", []),
        ),
    }


def build_proxy_feature_risks(
    feature_frame: pd.DataFrame,
    protected_frame: pd.DataFrame,
    *,
    active_feature_names: tuple[str, ...],
    top_k: int = 5,
) -> dict[str, Any]:
    numeric_frame = feature_frame.loc[:, list(active_feature_names)].select_dtypes(include=["number"]).copy()
    diagnostics: dict[str, Any] = {}
    for protected_name in protected_frame.columns:
        attribute = protected_frame[protected_name].fillna("__MISSING__").astype(str)
        rows = []
        for group_value in sorted(attribute.unique().tolist()):
            mask = (attribute == group_value).to_numpy(dtype=bool)
            if mask.sum() < 30:
                continue
            group_means = numeric_frame.loc[mask].mean()
            overall_means = numeric_frame.mean()
            overall_stds = numeric_frame.std(ddof=0).replace(0.0, np.nan)
            standardized_gap = ((group_means - overall_means).abs() / overall_stds).fillna(0.0)
            top_features = standardized_gap.sort_values(ascending=False).head(top_k)
            rows.append(
                {
                    "group": group_value,
                    "top_shifted_features": [
                        {"feature": feature_name, "standardized_mean_gap": float(value)}
                        for feature_name, value in top_features.items()
                    ],
                }
            )
        diagnostics[protected_name] = rows
    return diagnostics


def build_subgroup_shap_comparison(
    *,
    model: Any,
    processed_test_features: pd.DataFrame,
    protected_frame: pd.DataFrame,
    flagged_groups: list[str] | None = None,
    target_groups: list[str] | None = None,
    sample_size: int = 1000,
    top_k: int = 8,
) -> dict[str, Any] | None:
    try:
        import shap
    except ImportError:  # pragma: no cover
        return None

    sample = processed_test_features.head(min(sample_size, len(processed_test_features))).copy()
    sample_protected = protected_frame.head(len(sample)).reset_index(drop=True)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(sample)
    if isinstance(shap_values, list):
        shap_matrix = np.asarray(shap_values[-1], dtype=float)
    else:
        shap_matrix = np.asarray(shap_values, dtype=float)
    overall_importance = np.mean(np.abs(shap_matrix), axis=0)
    rows = []
    groups_to_review = list(dict.fromkeys((flagged_groups or []) + (target_groups or [])))
    for flagged_group in groups_to_review:
        protected_name, group_value = flagged_group.split("=", 1)
        mask = (sample_protected[protected_name].fillna("__MISSING__").astype(str) == group_value).to_numpy(dtype=bool)
        if mask.sum() < 10:
            continue
        subgroup_importance = np.mean(np.abs(shap_matrix[mask]), axis=0)
        delta = subgroup_importance - overall_importance
        top_indices = np.argsort(-np.abs(delta))[:top_k]
        rows.append(
            {
                "group": flagged_group,
                "top_importance_deltas": [
                    {
                        "feature": str(sample.columns[index]),
                        "overall_mean_abs_shap": float(overall_importance[index]),
                        "subgroup_mean_abs_shap": float(subgroup_importance[index]),
                        "delta": float(delta[index]),
                    }
                    for index in top_indices
                ],
            }
        )
    return {"sample_size": int(len(sample)), "groups": rows}


def build_recommendation(candidate_reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    promotable = [
        candidate_name
        for candidate_name, payload in candidate_reports.items()
        if payload["promotion_eligible"]
    ]
    if promotable:
        return {
            "status": "candidate_ready_for_comparison",
            "recommended_candidates": promotable,
            "next_step": "Run full governance comparison against the current production ensemble.",
        }
    return {
        "status": "continue_candidate_iteration",
        "recommended_candidates": [],
        "next_step": (
            "Keep constrained trees as the primary production track, but continue "
            "iterating until monotonic and counterfactual gates pass."
        ),
    }


if __name__ == "__main__":
    main()
