"""Targeted TabNet dataset-repair and retraining experiment.

This script intentionally does not retrain the full stack and does not promote
any artifact into production. It trains a candidate TabNet against repaired
synthetic supervision, evaluates local monotonic behavior, and writes a
promotion-gate report for model governance review.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.artifact_loader import load_runtime_artifact_bundle
from backend.ml.data_generation.generator import DEFAULT_ROW_COUNT, generate_synthetic_dataset
from backend.ml.evaluation.metrics import (
    compute_binary_classification_metrics,
    expected_calibration_error,
)
from backend.ml.features.derived_features import DERIVED_FEATURES, compute_derived_features
from backend.ml.inference.ensemble_adapter import (
    EnsembleInferenceBundle,
    build_ensemble_meta_features,
)
from backend.ml.nlp.extractor import RAW_TEXT_RESPONSE_COLUMN
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES, TARGET
from backend.ml.preprocessing.pipeline import (
    apply_text_pca,
    align_text_features_from_raw_text,
    prepare_model_feature_frame,
    transform_features,
)
from backend.ml.training.neural import train_tabnet as tabnet_training


DATASET_PATH = ROOT / "data" / "raw" / "synthetic_dataset.csv"
DEFAULT_OUTPUT_DIR = ROOT / "runtime" / "research_archive" / "tabnet_repair" / "latest"
NEUTRAL_DEVICE_TYPE = "mobile"
NEUTRAL_TIME_OF_DAY = "afternoon"
TABNET_MODEL_NAME = "candidate_repaired_tabnet"


PositiveDirection = Literal["increasing", "decreasing"]


@dataclass(frozen=True)
class PreparedCompatibleData:
    preprocessor: Any
    feature_frame: pd.DataFrame
    X_processed: np.ndarray
    train_mask: pd.Series
    validation_mask: pd.Series
    test_mask: pd.Series
    y_train: np.ndarray
    y_validation: np.ndarray
    y_test: np.ndarray
    masked_features: tuple[str, ...]
    mask_replacements: dict[str, Any]


@dataclass(frozen=True)
class TrainedCandidate:
    model: Any
    artifact_path: Path
    validation_probabilities: np.ndarray
    test_probabilities: np.ndarray
    training_audit: dict[str, Any]


@dataclass(frozen=True)
class CriticalFeatureMonotonicPostProcessor:
    feature_directions: dict[str, PositiveDirection]
    calibrators: dict[str, IsotonicRegression]
    feature_weights: dict[str, float]

    def predict(self, feature_frame: pd.DataFrame) -> np.ndarray:
        outputs = []
        weights = []
        for feature_name, direction in self.feature_directions.items():
            calibrator = self.calibrators[feature_name]
            raw_values = feature_frame[feature_name].to_numpy(dtype=float)
            transformed_values = raw_values if direction == "increasing" else 1.0 - raw_values
            outputs.append(calibrator.predict(transformed_values))
            weights.append(self.feature_weights[feature_name])
        stacked = np.column_stack(outputs)
        weight_array = np.asarray(weights, dtype=float)
        return np.average(stacked, axis=1, weights=weight_array)


SENSITIVITY_FEATURES: dict[str, PositiveDirection] = {
    "resilience_score": "increasing",
    "future_orientation": "increasing",
    "numeracy_score": "increasing",
    "scroll_hesitation_score": "decreasing",
    "engagement_score": "increasing",
    "text_agency_score": "increasing",
    "text_sentiment_compound": "increasing",
    "conscientiousness_score": "increasing",
    "repayment_intention_score": "increasing",
    "psychological_credit_index": "increasing",
}

RAW_MONOTONIC_FEATURES: dict[str, PositiveDirection] = {
    "resilience_score": "increasing",
    "future_orientation": "increasing",
    "numeracy_score": "increasing",
    "scroll_hesitation_score": "decreasing",
}

BRITTLE_COMPOSITE_FEATURES: tuple[str, ...] = (
    "psychological_credit_index",
    "repayment_intention_score",
    "engagement_score",
    "behavioral_trust_score",
)


TRAINABLE_MONOTONIC_FEATURES: dict[str, PositiveDirection] = {
    feature_name: SENSITIVITY_FEATURES[feature_name]
    for feature_name in (
        *RAW_MONOTONIC_FEATURES.keys(),
        "text_agency_score",
        "text_sentiment_compound",
        "conscientiousness_score",
    )
}


def main() -> None:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    args = parse_args()
    masked_features = parse_feature_list(args.mask_features)
    curriculum_features = parse_feature_list(args.curriculum_features)
    postprocess_features = parse_feature_list(args.postprocess_features)
    targeted_counterfactual_step_grid = parse_float_list(args.targeted_counterfactual_step_grid)
    hard_pair_features = parse_feature_list(args.hard_pair_features)
    collateral_guard_features = parse_feature_list(args.collateral_guard_features)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    (output_dir / "plots").mkdir(parents=True, exist_ok=True)

    artifacts = load_runtime_artifact_bundle(strict=True)
    if artifacts.base_models is None or artifacts.stacking_config is None:
        raise RuntimeError("Runtime ensemble artifacts are required for compatibility checks.")

    current_dataset = pd.read_csv(DATASET_PATH)
    repaired_dataset = generate_synthetic_dataset(
        row_count=args.row_count,
        seed=args.seed,
    )
    repaired_dataset_path = output_dir / "synthetic_dataset_repaired.csv"
    repaired_dataset.to_csv(repaired_dataset_path, index=False)

    before_dataset_audit = build_dataset_audit(current_dataset, label="current_corrupted")
    after_dataset_audit = build_dataset_audit(repaired_dataset, label="repaired")

    current_prepared = prepare_production_compatible_data(
        current_dataset,
        preprocessor=artifacts.preprocessor,
        text_pca=artifacts.text_pca,
        neutralize_operational_metadata=True,
        masked_features=masked_features,
    )
    repaired_prepared = prepare_production_compatible_data(
        repaired_dataset,
        preprocessor=artifacts.preprocessor,
        text_pca=artifacts.text_pca,
        neutralize_operational_metadata=True,
        masked_features=masked_features,
    )

    candidate_artifact_path = output_dir / "artifacts" / "tabnet_repaired_prodpreproc.zip"
    if args.reuse_existing and candidate_artifact_path.is_file():
        candidate_model = tabnet_training.load_tabnet_model(candidate_artifact_path)
        manifest_path = candidate_artifact_path.with_suffix(".manifest.json")
        manifest_payload = (
            json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest_path.is_file()
            else {}
        )
        candidate_validation_probs = candidate_model.predict_proba(
            repaired_prepared.X_processed[repaired_prepared.validation_mask.to_numpy()]
        )[:, 1]
        candidate_test_probs = candidate_model.predict_proba(
            repaired_prepared.X_processed[repaired_prepared.test_mask.to_numpy()]
        )[:, 1]
        candidate = TrainedCandidate(
            model=candidate_model,
            artifact_path=candidate_artifact_path,
            validation_probabilities=np.asarray(candidate_validation_probs, dtype=float),
            test_probabilities=np.asarray(candidate_test_probs, dtype=float),
            training_audit=dict(manifest_payload.get("training_audit", {})),
        )
    else:
        candidate = train_candidate_tabnet(
            repaired_prepared,
            artifact_path=candidate_artifact_path,
            random_state=args.seed,
            max_epochs=args.max_epochs,
            patience=args.patience,
            n_d=args.n_d,
            n_a=args.n_a,
            n_steps=args.n_steps,
            gamma=args.gamma,
            n_independent=args.n_independent,
            n_shared=args.n_shared,
            momentum=args.momentum,
            mask_type=args.mask_type,
            curriculum_features=curriculum_features,
            counterfactual_augmentation_repeats=args.counterfactual_augmentation_repeats,
            counterfactual_step=args.counterfactual_step,
            targeted_counterfactual_step_grid=targeted_counterfactual_step_grid,
            targeted_strong_threshold=args.targeted_strong_threshold,
            targeted_low_hesitation_threshold=args.targeted_low_hesitation_threshold,
            hard_pair_features=hard_pair_features,
            hard_pair_sample_size=args.hard_pair_sample_size,
            hard_pair_max_per_feature=args.hard_pair_max_per_feature,
            hard_pair_repeats=args.hard_pair_repeats,
            hard_pair_violation_tolerance=args.hard_pair_violation_tolerance,
        )

    current_tabnet = artifacts.base_models["tabnet"]

    tabnet_metrics = {
        "old_tabnet_on_current_dataset": evaluate_probability_model(
            y_true=current_prepared.y_test,
            probabilities=current_tabnet.predict_proba(
                current_prepared.X_processed[current_prepared.test_mask.to_numpy()]
            )[:, 1],
            model_name="old_tabnet",
            split="current_dataset_test_months_11_12",
        ),
        "old_tabnet_on_repaired_dataset": evaluate_probability_model(
            y_true=repaired_prepared.y_test,
            probabilities=current_tabnet.predict_proba(
                repaired_prepared.X_processed[repaired_prepared.test_mask.to_numpy()]
            )[:, 1],
            model_name="old_tabnet",
            split="repaired_dataset_test_months_11_12",
        ),
        "new_tabnet_on_repaired_dataset": evaluate_probability_model(
            y_true=repaired_prepared.y_test,
            probabilities=candidate.test_probabilities,
            model_name=TABNET_MODEL_NAME,
            split="repaired_dataset_test_months_11_12",
        ),
    }

    calibration_audit = {
        "old_tabnet_on_repaired_dataset": build_calibration_audit(
            y_validation=repaired_prepared.y_validation,
            validation_probabilities=current_tabnet.predict_proba(
                repaired_prepared.X_processed[repaired_prepared.validation_mask.to_numpy()]
            )[:, 1],
            y_test=repaired_prepared.y_test,
            test_probabilities=current_tabnet.predict_proba(
                repaired_prepared.X_processed[repaired_prepared.test_mask.to_numpy()]
            )[:, 1],
        ),
        "new_tabnet_on_repaired_dataset": build_calibration_audit(
            y_validation=repaired_prepared.y_validation,
            validation_probabilities=candidate.validation_probabilities,
            y_test=repaired_prepared.y_test,
            test_probabilities=candidate.test_probabilities,
        ),
    }

    sensitivity = build_sensitivity_comparison(
        artifacts=artifacts,
        old_tabnet=current_tabnet,
        new_tabnet=candidate.model,
        new_masked_features=repaired_prepared.masked_features,
        new_mask_replacements=repaired_prepared.mask_replacements,
    )
    acceptance_gates = evaluate_monotonic_acceptance_gates(
        sensitivity,
        material_tolerance=args.material_tolerance,
        local_tolerance=args.local_tolerance,
    )
    metadata_gate = evaluate_metadata_stability_gate(
        artifacts=artifacts,
        tabnet_model=candidate.model,
        max_allowed_delta=args.metadata_delta_tolerance,
    )

    disagreement_audit = {
        "old_tabnet": build_disagreement_audit(
            artifacts=artifacts,
            tabnet_model=current_tabnet,
            prepared=repaired_prepared,
        ),
        "new_tabnet": build_disagreement_audit(
            artifacts=artifacts,
            tabnet_model=candidate.model,
            prepared=repaired_prepared,
        ),
    }
    counterfactual_audit = {
        "old_tabnet": build_counterfactual_stability_audit(
            artifacts=artifacts,
            prepared=repaired_prepared,
            probability_fn=lambda frame: current_tabnet.predict_proba(
                transform_features(artifacts.preprocessor, frame)
            )[:, 1],
            sample_size=args.counterfactual_audit_sample_size,
            tolerance=args.counterfactual_audit_tolerance,
            features=curriculum_features,
            step=args.counterfactual_step,
        ),
        "new_tabnet": build_counterfactual_stability_audit(
            artifacts=artifacts,
            prepared=repaired_prepared,
            probability_fn=lambda frame: candidate.model.predict_proba(
                transform_features(artifacts.preprocessor, frame)
            )[:, 1],
            sample_size=args.counterfactual_audit_sample_size,
            tolerance=args.counterfactual_audit_tolerance,
            features=curriculum_features,
            step=args.counterfactual_step,
        ),
    }
    collateral_guard_audit = build_counterfactual_stability_audit(
        artifacts=artifacts,
        prepared=repaired_prepared,
        probability_fn=lambda frame: candidate.model.predict_proba(
            transform_features(artifacts.preprocessor, frame)
        )[:, 1],
        sample_size=args.counterfactual_audit_sample_size,
        tolerance=args.counterfactual_audit_tolerance,
        features=collateral_guard_features,
        step=args.counterfactual_step,
    )
    counterfactual_gate = evaluate_counterfactual_acceptance_gate(
        counterfactual_audit["new_tabnet"],
        max_violation_rate=args.counterfactual_max_violation_rate,
        max_worst_delta=args.counterfactual_max_worst_delta,
    )
    collateral_guard_gate = evaluate_counterfactual_acceptance_gate(
        collateral_guard_audit,
        max_violation_rate=args.counterfactual_max_violation_rate,
        max_worst_delta=args.counterfactual_max_worst_delta,
    )
    promotion_eligible = bool(
        acceptance_gates["passed"]
        and metadata_gate["passed"]
        and counterfactual_gate["passed"]
        and collateral_guard_gate["passed"]
    )
    monotonic_postprocess = fit_critical_feature_monotonic_postprocessor(
        feature_frame=repaired_prepared.feature_frame.loc[
            repaired_prepared.validation_mask
        ].reset_index(drop=True),
        y_true=repaired_prepared.y_validation,
        feature_names=postprocess_features,
    )
    postprocessed_probabilities = monotonic_postprocess.predict(
        repaired_prepared.feature_frame.loc[repaired_prepared.test_mask].reset_index(drop=True)
    )
    monotonic_postprocess_report = {
        "feature_weights": monotonic_postprocess.feature_weights,
        "test_metrics": evaluate_probability_model(
            y_true=repaired_prepared.y_test,
            probabilities=postprocessed_probabilities,
            model_name="critical_feature_monotonic_postprocessor",
            split="repaired_dataset_test_months_11_12",
        ),
        "test_gate": evaluate_monotonic_acceptance_gates(
            build_sensitivity_for_probability_fn(
                artifacts=artifacts,
                probability_fn=lambda frame: monotonic_postprocess.predict(frame),
                label="monotonic_postprocessor",
                masked_features=repaired_prepared.masked_features,
                mask_replacements=repaired_prepared.mask_replacements,
            ),
            material_tolerance=args.material_tolerance,
            local_tolerance=args.local_tolerance,
        ),
    }

    ensemble_compatibility = build_ensemble_compatibility_report(
        artifacts=artifacts,
        repaired_prepared=repaired_prepared,
        old_tabnet=current_tabnet,
        new_tabnet=candidate.model,
        evaluate_reentry=promotion_eligible or args.force_ensemble_compatibility,
    )

    sensitivity_csv_path = output_dir / "sensitivity_sweeps.csv"
    flatten_sensitivity_to_frame(sensitivity).to_csv(sensitivity_csv_path, index=False)
    plot_paths = write_sensitivity_plots(
        sensitivity,
        output_dir=output_dir / "plots",
    )

    report = {
        "experiment": {
            "name": "targeted_tabnet_dataset_repair_experiment",
            "seed": args.seed,
            "row_count": args.row_count,
            "max_epochs": args.max_epochs,
            "patience": args.patience,
            "tabnet_hyperparameters": {
                "n_d": args.n_d,
                "n_a": args.n_a,
                "n_steps": args.n_steps,
                "gamma": args.gamma,
                "n_independent": args.n_independent,
                "n_shared": args.n_shared,
                "momentum": args.momentum,
                "mask_type": args.mask_type,
            },
            "runtime_disagreement_mitigation_remains_enabled": _tabnet_guard_enabled(
                artifacts.stacking_config
            ),
            "candidate_artifact_path": str(candidate.artifact_path),
            "repaired_dataset_path": str(repaired_dataset_path),
            "sensitivity_csv_path": str(sensitivity_csv_path),
            "plot_paths": [str(path) for path in plot_paths],
            "uses_production_preprocessor": True,
            "uses_production_text_pca": True,
            "operational_metadata_training_policy": (
                f"device_type and time_of_day are neutralized to "
                f"{NEUTRAL_DEVICE_TYPE!r}/{NEUTRAL_TIME_OF_DAY!r} before "
                "preprocessing and TabNet training."
            ),
            "masked_features": list(masked_features),
            "curriculum_features": list(curriculum_features),
            "counterfactual_augmentation_repeats": args.counterfactual_augmentation_repeats,
            "counterfactual_step": args.counterfactual_step,
            "targeted_counterfactual_step_grid": list(targeted_counterfactual_step_grid),
            "targeted_strong_threshold": args.targeted_strong_threshold,
            "targeted_low_hesitation_threshold": args.targeted_low_hesitation_threshold,
            "hard_pair_features": list(hard_pair_features),
            "hard_pair_sample_size": args.hard_pair_sample_size,
            "hard_pair_max_per_feature": args.hard_pair_max_per_feature,
            "hard_pair_repeats": args.hard_pair_repeats,
            "hard_pair_violation_tolerance": args.hard_pair_violation_tolerance,
            "collateral_guard_features": list(collateral_guard_features),
            "postprocess_features": list(postprocess_features),
        },
        "dataset_audit": {
            "before": before_dataset_audit,
            "after": after_dataset_audit,
        },
        "tabnet_metrics": tabnet_metrics,
        "training_audit": candidate.training_audit,
        "calibration_audit": calibration_audit,
        "sensitivity": sensitivity,
        "acceptance_gates": acceptance_gates,
        "metadata_stability_gate": metadata_gate,
        "counterfactual_gate": counterfactual_gate,
        "collateral_guard_gate": collateral_guard_gate,
        "promotion_eligible": promotion_eligible,
        "disagreement_audit": disagreement_audit,
        "counterfactual_audit": counterfactual_audit,
        "collateral_guard_audit": collateral_guard_audit,
        "monotonic_postprocess_report": monotonic_postprocess_report,
        "ensemble_compatibility": ensemble_compatibility,
        "root_cause_summary": [
            "The previous synthetic supervision encoded high scroll_hesitation_score as positive engagement.",
            "The synthetic label logit directly rewarded device_type == desktop.",
            "TabNet learned localized high-AUC shortcuts from those corrupted labels, so aggregate AUC did not expose monotonic failures.",
            "The candidate is trained with repaired labels, TabNet-only feature masking, and counterfactual curriculum augmentation, then blocked from promotion unless raw TabNet sensitivity passes monotonic gates.",
        ],
    }

    report_path = output_dir / "tabnet_repair_experiment_report.json"
    report_path.write_text(json.dumps(to_jsonable(report), indent=2), encoding="utf-8")
    summary = {
        "report_path": str(report_path),
        "promotion_eligible": promotion_eligible,
        "acceptance_gates_passed": acceptance_gates["passed"],
        "metadata_stability_gate_passed": metadata_gate["passed"],
        "counterfactual_gate_passed": counterfactual_gate["passed"],
        "collateral_guard_gate_passed": collateral_guard_gate["passed"],
        "failed_monotonic_gates": [
            result for result in acceptance_gates["results"] if not result["passed"]
        ],
        "tabnet_test_metrics": {
            "old_tabnet_on_repaired_dataset": tabnet_metrics[
                "old_tabnet_on_repaired_dataset"
            ],
            "new_tabnet_on_repaired_dataset": tabnet_metrics[
                "new_tabnet_on_repaired_dataset"
            ],
        },
        "counterfactual_audit_new_tabnet": counterfactual_audit["new_tabnet"],
        "plot_paths": [str(path) for path in plot_paths],
    }
    if args.print_full_report:
        print(json.dumps(to_jsonable({"report_path": str(report_path), **report}), indent=2))
    else:
        print(json.dumps(to_jsonable(summary), indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row-count", type=int, default=DEFAULT_ROW_COUNT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-epochs", type=int, default=30)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--n-d", type=int, default=tabnet_training._TABNET_N_D)
    parser.add_argument("--n-a", type=int, default=tabnet_training._TABNET_N_A)
    parser.add_argument("--n-steps", type=int, default=tabnet_training._TABNET_N_STEPS)
    parser.add_argument("--gamma", type=float, default=tabnet_training._TABNET_GAMMA)
    parser.add_argument(
        "--n-independent",
        type=int,
        default=tabnet_training._TABNET_N_INDEPENDENT,
    )
    parser.add_argument("--n-shared", type=int, default=tabnet_training._TABNET_N_SHARED)
    parser.add_argument("--momentum", type=float, default=tabnet_training._TABNET_MOMENTUM)
    parser.add_argument("--mask-type", default=tabnet_training._TABNET_MASK_TYPE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--reuse-existing", action="store_true")
    parser.add_argument("--force-ensemble-compatibility", action="store_true")
    parser.add_argument("--print-full-report", action="store_true")
    parser.add_argument("--material-tolerance", type=float, default=0.02)
    parser.add_argument("--local-tolerance", type=float, default=0.05)
    parser.add_argument("--metadata-delta-tolerance", type=float, default=0.02)
    parser.add_argument(
        "--mask-features",
        default="psychological_credit_index,repayment_intention_score,engagement_score,behavioral_trust_score",
        help="Comma-separated raw model features to neutralize for TabNet-only experiments.",
    )
    parser.add_argument(
        "--curriculum-features",
        default="resilience_score,future_orientation,numeracy_score,scroll_hesitation_score",
        help="Comma-separated raw features used for monotonic counterfactual curriculum augmentation.",
    )
    parser.add_argument("--counterfactual-augmentation-repeats", type=int, default=1)
    parser.add_argument("--counterfactual-step", type=float, default=0.12)
    parser.add_argument(
        "--targeted-counterfactual-step-grid",
        default="0.04,0.08,0.12,0.16",
        help="Comma-separated additional favorable step sizes for hard monotonic slices.",
    )
    parser.add_argument("--targeted-strong-threshold", type=float, default=0.7)
    parser.add_argument("--targeted-low-hesitation-threshold", type=float, default=0.3)
    parser.add_argument("--counterfactual-audit-sample-size", type=int, default=256)
    parser.add_argument("--counterfactual-audit-tolerance", type=float, default=0.01)
    parser.add_argument("--counterfactual-max-violation-rate", type=float, default=0.02)
    parser.add_argument("--counterfactual-max-worst-delta", type=float, default=0.05)
    parser.add_argument(
        "--collateral-guard-features",
        default="text_agency_score",
        help="Comma-separated non-core features to audit for collateral monotonic regressions.",
    )
    parser.add_argument(
        "--hard-pair-features",
        default="resilience_score,future_orientation",
        help="Comma-separated features used for adaptive hard-pair mining after the first-pass TabNet fit.",
    )
    parser.add_argument("--hard-pair-sample-size", type=int, default=1024)
    parser.add_argument("--hard-pair-max-per-feature", type=int, default=256)
    parser.add_argument("--hard-pair-repeats", type=int, default=2)
    parser.add_argument("--hard-pair-violation-tolerance", type=float, default=0.01)
    parser.add_argument(
        "--postprocess-features",
        default="resilience_score,future_orientation,numeracy_score,scroll_hesitation_score,engagement_score",
        help="Comma-separated features for the monotonic post-processing diagnostic.",
    )
    return parser.parse_args()


def parse_feature_list(raw_value: str) -> tuple[str, ...]:
    return tuple(
        feature_name.strip()
        for feature_name in raw_value.split(",")
        if feature_name.strip()
    )


def parse_float_list(raw_value: str) -> tuple[float, ...]:
    return tuple(
        float(token.strip())
        for token in raw_value.split(",")
        if token.strip()
    )


def build_dataset_audit(dataset: pd.DataFrame, *, label: str) -> dict[str, Any]:
    repayment = dataset[TARGET].astype(int)
    numeric_features = [
        "scroll_hesitation_score",
        "engagement_score",
        "numeracy_score",
        "future_orientation",
        "resilience_score",
        "text_agency_score",
        "text_sentiment_compound",
        "repayment_intention_score",
        "psychological_credit_index",
        "cognitive_load_index",
        "impulsivity_index",
    ]
    label_correlations = {
        feature_name: safe_corr(dataset[feature_name], repayment)
        for feature_name in numeric_features
        if feature_name in dataset.columns
    }
    label_correlations["device_type"] = categorical_label_correlations(
        dataset,
        "device_type",
    )
    label_correlations["time_of_day"] = categorical_label_correlations(
        dataset,
        "time_of_day",
    )

    return {
        "label": label,
        "row_count": int(len(dataset)),
        "repayment_label_distribution": {
            "repayment_rate": float(repayment.mean()),
            "default_rate": float(1.0 - repayment.mean()),
            "positive_count": int(repayment.sum()),
            "negative_count": int(len(repayment) - repayment.sum()),
        },
        "engagement_score_distribution": describe_series(dataset["engagement_score"]),
        "metadata_influence": {
            "repayment_rate_by_device_type": group_mean(dataset, "device_type", TARGET),
            "repayment_rate_by_time_of_day": group_mean(dataset, "time_of_day", TARGET),
            "device_type_mix": group_share(dataset, "device_type"),
            "time_of_day_mix": group_share(dataset, "time_of_day"),
        },
        "strong_profile_distributions": build_strong_profile_summary(dataset),
        "feature_label_correlations": label_correlations,
        "monotonic_label_sanity": build_label_monotonic_sanity(dataset),
        "operational_metadata_notes": [
            "No protected attributes are model features.",
            "device_type and time_of_day remain categorical telemetry in the raw schema for payload compatibility.",
            "The repaired TabNet experiment neutralizes device_type/time_of_day before training so the candidate cannot learn direct metadata weights.",
        ],
    }


def train_candidate_tabnet(
    prepared: PreparedCompatibleData,
    *,
    artifact_path: Path,
    random_state: int,
    max_epochs: int,
    patience: int,
    n_d: int,
    n_a: int,
    n_steps: int,
    gamma: float,
    n_independent: int,
    n_shared: int,
    momentum: float,
    mask_type: str,
    curriculum_features: tuple[str, ...],
    counterfactual_augmentation_repeats: int,
    counterfactual_step: float,
    targeted_counterfactual_step_grid: tuple[float, ...],
    targeted_strong_threshold: float,
    targeted_low_hesitation_threshold: float,
    hard_pair_features: tuple[str, ...],
    hard_pair_sample_size: int,
    hard_pair_max_per_feature: int,
    hard_pair_repeats: int,
    hard_pair_violation_tolerance: float,
) -> TrainedCandidate:
    np.random.seed(random_state)
    tabnet_training._set_pytorch_seed(random_state)
    model = build_candidate_tabnet_model(
        random_state=random_state,
        n_d=n_d,
        n_a=n_a,
        n_steps=n_steps,
        gamma=gamma,
        n_independent=n_independent,
        n_shared=n_shared,
        momentum=momentum,
        mask_type=mask_type,
    )

    train_mask = prepared.train_mask.to_numpy()
    validation_mask = prepared.validation_mask.to_numpy()
    test_mask = prepared.test_mask.to_numpy()
    train_feature_frame = prepared.feature_frame.loc[prepared.train_mask].reset_index(drop=True)
    training_feature_frame, training_labels, training_audit = build_monotonic_curriculum_training_set(
        train_feature_frame=train_feature_frame,
        y_train=prepared.y_train,
        curriculum_features=curriculum_features,
        repeats=counterfactual_augmentation_repeats,
        step=counterfactual_step,
        masked_features=prepared.masked_features,
        mask_replacements=prepared.mask_replacements,
        targeted_counterfactual_step_grid=targeted_counterfactual_step_grid,
        targeted_strong_threshold=targeted_strong_threshold,
        targeted_low_hesitation_threshold=targeted_low_hesitation_threshold,
    )
    first_pass_model = build_candidate_tabnet_model(
        random_state=random_state,
        n_d=n_d,
        n_a=n_a,
        n_steps=n_steps,
        gamma=gamma,
        n_independent=n_independent,
        n_shared=n_shared,
        momentum=momentum,
        mask_type=mask_type,
    )
    X_train_processed = transform_features(prepared.preprocessor, training_feature_frame)
    first_pass_model.fit(
        X_train=X_train_processed,
        y_train=training_labels,
        eval_set=[(prepared.X_processed[validation_mask], prepared.y_validation)],
        eval_name=["validation"],
        eval_metric=["auc"],
        max_epochs=max_epochs,
        patience=patience,
        batch_size=tabnet_training._TABNET_BATCH_SIZE,
        virtual_batch_size=tabnet_training._TABNET_VIRTUAL_BATCH_SIZE,
        num_workers=0,
        drop_last=False,
    )
    mined_frame, mined_labels, hard_pair_audit = mine_hard_pair_training_rows(
        base_train_feature_frame=train_feature_frame,
        y_train=prepared.y_train,
        masked_features=prepared.masked_features,
        mask_replacements=prepared.mask_replacements,
        preprocessor=prepared.preprocessor,
        model=first_pass_model,
        hard_pair_features=hard_pair_features,
        step_grid=targeted_counterfactual_step_grid
        if targeted_counterfactual_step_grid
        else (counterfactual_step,),
        sample_size=hard_pair_sample_size,
        max_per_feature=hard_pair_max_per_feature,
        repeats=hard_pair_repeats,
        violation_tolerance=hard_pair_violation_tolerance,
    )
    final_training_feature_frame = training_feature_frame
    final_training_labels = training_labels
    if not mined_frame.empty:
        final_training_feature_frame = pd.concat(
            [training_feature_frame, mined_frame],
            ignore_index=True,
        )
        final_training_labels = np.concatenate([training_labels, mined_labels])
    model = build_candidate_tabnet_model(
        random_state=random_state,
        n_d=n_d,
        n_a=n_a,
        n_steps=n_steps,
        gamma=gamma,
        n_independent=n_independent,
        n_shared=n_shared,
        momentum=momentum,
        mask_type=mask_type,
    )
    X_train_processed = transform_features(prepared.preprocessor, final_training_feature_frame)
    model.fit(
        X_train=X_train_processed,
        y_train=final_training_labels,
        eval_set=[(prepared.X_processed[validation_mask], prepared.y_validation)],
        eval_name=["validation"],
        eval_metric=["auc"],
        max_epochs=max_epochs,
        patience=patience,
        batch_size=tabnet_training._TABNET_BATCH_SIZE,
        virtual_batch_size=tabnet_training._TABNET_VIRTUAL_BATCH_SIZE,
        num_workers=0,
        drop_last=False,
    )
    training_audit["hard_pair_mining"] = hard_pair_audit

    tabnet_training._save_tabnet_model(model, artifact_path)
    validation_probabilities = np.asarray(
        model.predict_proba(prepared.X_processed[validation_mask])[:, 1],
        dtype=float,
    )
    test_probabilities = np.asarray(
        model.predict_proba(prepared.X_processed[test_mask])[:, 1],
        dtype=float,
    )
    manifest_path = artifact_path.with_suffix(".manifest.json")
    manifest_path.write_text(
        json.dumps(
            {
                "model_name": TABNET_MODEL_NAME,
                "training_policy": "repaired_labels_production_preprocessor_metadata_neutralized",
                "random_state": random_state,
                "max_epochs": max_epochs,
                "patience": patience,
                "hyperparameters": {
                    "n_d": n_d,
                    "n_a": n_a,
                    "n_steps": n_steps,
                    "gamma": gamma,
                    "n_independent": n_independent,
                    "n_shared": n_shared,
                    "momentum": momentum,
                    "mask_type": mask_type,
                },
                "neutralized_operational_metadata": {
                    "device_type": NEUTRAL_DEVICE_TYPE,
                    "time_of_day": NEUTRAL_TIME_OF_DAY,
                },
                "masked_features": list(prepared.masked_features),
                "training_audit": training_audit,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return TrainedCandidate(
        model=model,
        artifact_path=artifact_path,
        validation_probabilities=validation_probabilities,
        test_probabilities=test_probabilities,
        training_audit=training_audit,
    )


def build_candidate_tabnet_model(
    *,
    random_state: int,
    n_d: int,
    n_a: int,
    n_steps: int,
    gamma: float,
    n_independent: int,
    n_shared: int,
    momentum: float,
    mask_type: str,
) -> Any:
    from pytorch_tabnet.tab_model import TabNetClassifier  # type: ignore[import]

    return TabNetClassifier(
        n_d=n_d,
        n_a=n_a,
        n_steps=n_steps,
        gamma=gamma,
        n_independent=n_independent,
        n_shared=n_shared,
        momentum=momentum,
        epsilon=tabnet_training._TABNET_EPSILON,
        mask_type=mask_type,
        seed=random_state,
        verbose=0,
    )


def prepare_production_compatible_data(
    dataset: pd.DataFrame,
    *,
    preprocessor: Any,
    text_pca: Any,
    neutralize_operational_metadata: bool,
    masked_features: tuple[str, ...],
) -> PreparedCompatibleData:
    aligned_dataset, raw_embeddings = align_text_features_from_raw_text(dataset)
    feature_source_columns = [
        column_name for column_name in aligned_dataset.columns if column_name in ALL_MODEL_FEATURES
    ]
    feature_frame = prepare_model_feature_frame(
        aligned_dataset.loc[:, feature_source_columns].copy()
    )
    feature_frame = apply_text_pca(feature_frame, raw_embeddings, text_pca)
    if neutralize_operational_metadata:
        feature_frame = neutralize_operational_metadata_features(feature_frame)

    train_mask = dataset["cohort_month"].isin(tuple(range(1, 9)))
    validation_mask = dataset["cohort_month"].isin((9, 10))
    test_mask = dataset["cohort_month"].isin((11, 12))
    feature_frame, mask_replacements = apply_tabnet_feature_masking(
        feature_frame,
        train_mask=train_mask,
        masked_features=masked_features,
    )

    X_processed = transform_features(preprocessor, feature_frame)
    return PreparedCompatibleData(
        preprocessor=preprocessor,
        feature_frame=feature_frame,
        X_processed=X_processed,
        train_mask=train_mask,
        validation_mask=validation_mask,
        test_mask=test_mask,
        y_train=dataset.loc[train_mask, TARGET].to_numpy(dtype=int),
        y_validation=dataset.loc[validation_mask, TARGET].to_numpy(dtype=int),
        y_test=dataset.loc[test_mask, TARGET].to_numpy(dtype=int),
        masked_features=masked_features,
        mask_replacements=mask_replacements,
    )


def neutralize_operational_metadata_features(feature_frame: pd.DataFrame) -> pd.DataFrame:
    updated = feature_frame.copy()
    updated.loc[:, "device_type"] = NEUTRAL_DEVICE_TYPE
    updated.loc[:, "time_of_day"] = NEUTRAL_TIME_OF_DAY
    return updated


def apply_tabnet_feature_masking(
    feature_frame: pd.DataFrame,
    *,
    train_mask: pd.Series,
    masked_features: tuple[str, ...],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    updated = feature_frame.copy()
    replacements: dict[str, Any] = {}
    if not masked_features:
        return updated, replacements

    train_frame = updated.loc[train_mask].reset_index(drop=True)
    for feature_name in masked_features:
        if feature_name not in updated.columns:
            raise ValueError(f"Masked feature {feature_name!r} is not present in the feature frame.")
        train_series = train_frame[feature_name]
        if pd.api.types.is_numeric_dtype(train_series):
            replacement = float(train_series.median())
        else:
            mode = train_series.mode(dropna=True)
            replacement = str(mode.iloc[0]) if not mode.empty else ""
        updated.loc[:, feature_name] = replacement
        replacements[feature_name] = replacement
    return updated, replacements


def build_monotonic_curriculum_training_set(
    *,
    train_feature_frame: pd.DataFrame,
    y_train: np.ndarray,
    curriculum_features: tuple[str, ...],
    repeats: int,
    step: float,
    masked_features: tuple[str, ...],
    mask_replacements: dict[str, Any],
    targeted_counterfactual_step_grid: tuple[float, ...],
    targeted_strong_threshold: float,
    targeted_low_hesitation_threshold: float,
) -> tuple[pd.DataFrame, np.ndarray, dict[str, Any]]:
    base_frame = train_feature_frame.reset_index(drop=True).copy()
    labels = np.asarray(y_train, dtype=int)
    if repeats <= 0 or not curriculum_features:
        return base_frame, labels, {
            "base_rows": int(len(base_frame)),
            "curriculum_rows_added": 0,
            "repeats": int(repeats),
            "step": float(step),
            "curriculum_features": list(curriculum_features),
            "targeted_rows_added": 0,
            "targeted_counterfactual_step_grid": list(targeted_counterfactual_step_grid),
            "targeted_strong_threshold": float(targeted_strong_threshold),
            "targeted_low_hesitation_threshold": float(targeted_low_hesitation_threshold),
        }

    augmented_rows: list[dict[str, Any]] = []
    augmented_labels: list[int] = []
    favorable_count = 0
    adverse_count = 0
    targeted_rows_added = 0
    for _ in range(repeats):
        for row_index, (_, row) in enumerate(base_frame.iterrows()):
            label = int(labels[row_index])
            for feature_name in curriculum_features:
                direction = TRAINABLE_MONOTONIC_FEATURES[feature_name]
                variant = apply_counterfactual_feature_shift(
                    row=row.to_dict(),
                    feature_name=feature_name,
                    direction=direction,
                    favorable=bool(label == 1),
                    step=step,
                )
                if variant is None:
                    continue
                for masked_feature in masked_features:
                    if masked_feature in variant:
                        variant[masked_feature] = mask_replacements[masked_feature]
                augmented_rows.append(variant)
                augmented_labels.append(label)
                if label == 1:
                    favorable_count += 1
                else:
                    adverse_count += 1
                if label == 1 and should_add_targeted_monotonic_pairs(
                    row=row,
                    feature_name=feature_name,
                    strong_threshold=targeted_strong_threshold,
                    low_hesitation_threshold=targeted_low_hesitation_threshold,
                ):
                    for targeted_step in targeted_counterfactual_step_grid:
                        targeted_variant = apply_counterfactual_feature_shift(
                            row=row.to_dict(),
                            feature_name=feature_name,
                            direction=direction,
                            favorable=True,
                            step=targeted_step,
                        )
                        if targeted_variant is None:
                            continue
                        for masked_feature in masked_features:
                            if masked_feature in targeted_variant:
                                targeted_variant[masked_feature] = mask_replacements[masked_feature]
                        augmented_rows.append(targeted_variant)
                        augmented_labels.append(label)
                        favorable_count += 1
                        targeted_rows_added += 1

    if not augmented_rows:
        return base_frame, labels, {
            "base_rows": int(len(base_frame)),
            "curriculum_rows_added": 0,
            "repeats": int(repeats),
            "step": float(step),
            "curriculum_features": list(curriculum_features),
            "targeted_rows_added": 0,
            "targeted_counterfactual_step_grid": list(targeted_counterfactual_step_grid),
            "targeted_strong_threshold": float(targeted_strong_threshold),
            "targeted_low_hesitation_threshold": float(targeted_low_hesitation_threshold),
        }

    augmented_frame = pd.DataFrame(augmented_rows, columns=ALL_MODEL_FEATURES)
    combined_frame = pd.concat([base_frame, augmented_frame], ignore_index=True)
    combined_labels = np.concatenate([labels, np.asarray(augmented_labels, dtype=int)])
    return combined_frame, combined_labels, {
        "base_rows": int(len(base_frame)),
        "curriculum_rows_added": int(len(augmented_frame)),
        "repeats": int(repeats),
        "step": float(step),
        "curriculum_features": list(curriculum_features),
        "favorable_label_rows_added": int(favorable_count),
        "adverse_label_rows_added": int(adverse_count),
        "targeted_rows_added": int(targeted_rows_added),
        "targeted_counterfactual_step_grid": list(targeted_counterfactual_step_grid),
        "targeted_strong_threshold": float(targeted_strong_threshold),
        "targeted_low_hesitation_threshold": float(targeted_low_hesitation_threshold),
    }


def apply_counterfactual_feature_shift(
    *,
    row: dict[str, Any],
    feature_name: str,
    direction: PositiveDirection,
    favorable: bool,
    step: float,
) -> dict[str, Any] | None:
    value = float(row[feature_name])
    signed_step = step if favorable else -step
    if direction == "decreasing":
        signed_step *= -1.0
    shifted_value = float(np.clip(value + signed_step, 0.0, 1.0))
    if abs(shifted_value - value) < 1e-9:
        return None

    updated_row = dict(row)
    updated_row[feature_name] = shifted_value
    updated_frame = recompute_derived_columns(pd.DataFrame([updated_row], columns=ALL_MODEL_FEATURES))
    return updated_frame.iloc[0].to_dict()


def should_add_targeted_monotonic_pairs(
    *,
    row: pd.Series,
    feature_name: str,
    strong_threshold: float,
    low_hesitation_threshold: float,
) -> bool:
    value = float(row[feature_name])
    if feature_name == "scroll_hesitation_score":
        return value <= low_hesitation_threshold
    return value >= strong_threshold


def mine_hard_pair_training_rows(
    *,
    base_train_feature_frame: pd.DataFrame,
    y_train: np.ndarray,
    masked_features: tuple[str, ...],
    mask_replacements: dict[str, Any],
    preprocessor: Any,
    model: Any,
    hard_pair_features: tuple[str, ...],
    step_grid: tuple[float, ...],
    sample_size: int,
    max_per_feature: int,
    repeats: int,
    violation_tolerance: float,
) -> tuple[pd.DataFrame, np.ndarray, dict[str, Any]]:
    if sample_size <= 0 or max_per_feature <= 0 or repeats <= 0 or not hard_pair_features:
        return pd.DataFrame(columns=ALL_MODEL_FEATURES), np.asarray([], dtype=int), {
            "enabled": False,
            "rows_added": 0,
            "feature_results": {},
        }

    train_frame = base_train_feature_frame.reset_index(drop=True).copy()
    labels = np.asarray(y_train, dtype=int)
    positive_indices = np.flatnonzero(labels == 1)
    if len(positive_indices) == 0:
        return pd.DataFrame(columns=ALL_MODEL_FEATURES), np.asarray([], dtype=int), {
            "enabled": False,
            "rows_added": 0,
            "feature_results": {},
        }

    mined_rows: list[dict[str, Any]] = []
    mined_labels: list[int] = []
    feature_results: dict[str, Any] = {}
    for feature_name in hard_pair_features:
        if feature_name not in TRAINABLE_MONOTONIC_FEATURES:
            continue
        candidate_indices = select_hard_pair_candidate_indices(
            train_frame=train_frame,
            positive_indices=positive_indices,
            feature_name=feature_name,
            sample_size=sample_size,
        )
        if len(candidate_indices) == 0:
            feature_results[feature_name] = {
                "candidate_count": 0,
                "selected_violation_count": 0,
            }
            continue

        base_subset = train_frame.iloc[candidate_indices].reset_index(drop=True)
        base_probabilities = np.asarray(
            model.predict_proba(transform_features(preprocessor, base_subset))[:, 1],
            dtype=float,
        )
        variant_records: list[dict[str, Any]] = []
        variant_source_positions: list[int] = []
        for local_position, (_, row) in enumerate(base_subset.iterrows()):
            for step in step_grid:
                variant = apply_counterfactual_feature_shift(
                    row=row.to_dict(),
                    feature_name=feature_name,
                    direction=TRAINABLE_MONOTONIC_FEATURES[feature_name],
                    favorable=True,
                    step=step,
                )
                if variant is None:
                    continue
                for masked_feature in masked_features:
                    if masked_feature in variant:
                        variant[masked_feature] = mask_replacements[masked_feature]
                variant_records.append(variant)
                variant_source_positions.append(local_position)

        if not variant_records:
            feature_results[feature_name] = {
                "candidate_count": int(len(candidate_indices)),
                "selected_violation_count": 0,
            }
            continue

        variant_frame = pd.DataFrame(variant_records, columns=ALL_MODEL_FEATURES)
        variant_probabilities = np.asarray(
            model.predict_proba(transform_features(preprocessor, variant_frame))[:, 1],
            dtype=float,
        )
        deltas = variant_probabilities - base_probabilities[np.asarray(variant_source_positions, dtype=int)]
        violating_positions = np.flatnonzero(deltas < -violation_tolerance)
        if len(violating_positions) > 0:
            ordered_positions = violating_positions[np.argsort(deltas[violating_positions])]
            selected_positions = ordered_positions[:max_per_feature]
        else:
            selected_positions = np.asarray([], dtype=int)

        for position in selected_positions:
            for _ in range(repeats):
                mined_rows.append(variant_records[int(position)])
                mined_labels.append(1)

        feature_results[feature_name] = {
            "candidate_count": int(len(candidate_indices)),
            "generated_variant_count": int(len(variant_records)),
            "violation_count": int(len(violating_positions)),
            "selected_violation_count": int(len(selected_positions)),
            "worst_delta": None
            if len(violating_positions) == 0
            else float(np.min(deltas[violating_positions])),
            "mean_selected_delta": None
            if len(selected_positions) == 0
            else float(np.mean(deltas[selected_positions])),
        }

    if not mined_rows:
        return pd.DataFrame(columns=ALL_MODEL_FEATURES), np.asarray([], dtype=int), {
            "enabled": True,
            "rows_added": 0,
            "feature_results": feature_results,
            "step_grid": list(step_grid),
            "sample_size": int(sample_size),
            "max_per_feature": int(max_per_feature),
            "repeats": int(repeats),
            "violation_tolerance": float(violation_tolerance),
        }

    return (
        pd.DataFrame(mined_rows, columns=ALL_MODEL_FEATURES),
        np.asarray(mined_labels, dtype=int),
        {
            "enabled": True,
            "rows_added": int(len(mined_rows)),
            "feature_results": feature_results,
            "step_grid": list(step_grid),
            "sample_size": int(sample_size),
            "max_per_feature": int(max_per_feature),
            "repeats": int(repeats),
            "violation_tolerance": float(violation_tolerance),
        },
    )


def select_hard_pair_candidate_indices(
    *,
    train_frame: pd.DataFrame,
    positive_indices: np.ndarray,
    feature_name: str,
    sample_size: int,
) -> np.ndarray:
    candidate_frame = train_frame.iloc[positive_indices]
    values = candidate_frame[feature_name].to_numpy(dtype=float)
    if feature_name == "scroll_hesitation_score":
        order = np.argsort(values)
    else:
        order = np.argsort(-values)
    limited = order[: min(sample_size, len(order))]
    return positive_indices[limited]


def build_sensitivity_comparison(
    *,
    artifacts: Any,
    old_tabnet: Any,
    new_tabnet: Any,
    new_masked_features: tuple[str, ...],
    new_mask_replacements: dict[str, Any],
) -> dict[str, Any]:
    anchor = build_strong_anchor_feature_frame(artifacts)
    grid = np.linspace(0.0, 1.0, 11)

    sweeps: dict[str, Any] = {}
    for feature_name, direction in SENSITIVITY_FEATURES.items():
        sweeps[feature_name] = {
            "expected_direction": direction,
            "old_tabnet": sweep_tabnet_feature(
                artifacts=artifacts,
                tabnet_model=old_tabnet,
                anchor_feature_frame=anchor,
                feature_name=feature_name,
                values=grid,
            ),
            "new_tabnet": sweep_tabnet_feature(
                artifacts=artifacts,
                tabnet_model=new_tabnet,
                anchor_feature_frame=anchor,
                feature_name=feature_name,
                values=grid,
                masked_features=new_masked_features,
                mask_replacements=new_mask_replacements,
            ),
        }

    return {
        "anchor_profile": {
            feature_name: to_python_scalar(anchor.iloc[0][feature_name])
            for feature_name in [
                "numeracy_score",
                "future_orientation",
                "resilience_score",
                "scroll_hesitation_score",
                "engagement_score",
                "text_agency_score",
                "text_sentiment_compound",
            ]
        },
        "feature_sweeps": sweeps,
    }


def build_sensitivity_for_probability_fn(
    *,
    artifacts: Any,
    probability_fn: Any,
    label: str,
    masked_features: tuple[str, ...],
    mask_replacements: dict[str, Any],
) -> dict[str, Any]:
    anchor = build_strong_anchor_feature_frame(artifacts)
    grid = np.linspace(0.0, 1.0, 11)
    sweeps: dict[str, Any] = {}
    for feature_name, direction in SENSITIVITY_FEATURES.items():
        sweeps[feature_name] = {
            "expected_direction": direction,
            label: sweep_probability_fn_feature(
                artifacts=artifacts,
                probability_fn=probability_fn,
                anchor_feature_frame=anchor,
                feature_name=feature_name,
                values=grid,
                masked_features=masked_features,
                mask_replacements=mask_replacements,
            ),
            "old_tabnet": sweep_probability_fn_feature(
                artifacts=artifacts,
                probability_fn=probability_fn,
                anchor_feature_frame=anchor,
                feature_name=feature_name,
                values=grid,
                masked_features=masked_features,
                mask_replacements=mask_replacements,
            ),
            "new_tabnet": sweep_probability_fn_feature(
                artifacts=artifacts,
                probability_fn=probability_fn,
                anchor_feature_frame=anchor,
                feature_name=feature_name,
                values=grid,
                masked_features=masked_features,
                mask_replacements=mask_replacements,
            ),
        }
    return {"anchor_profile": {}, "feature_sweeps": sweeps}


def build_strong_anchor_feature_frame(artifacts: Any) -> pd.DataFrame:
    anchor = pd.DataFrame(
        [
            {
                "numeracy_score": 0.86,
                "CRT_score": 0.82,
                "financial_literacy_score": 0.84,
                "future_orientation": 0.88,
                "delay_discounting_rate": 0.86,
                "risk_attitude": 0.48,
                "risk_consistency_flag": 0,
                "loss_aversion_score": 0.38,
                "locus_of_control": 0.82,
                "conscientiousness_score": 0.84,
                "social_capital_score": 0.78,
                "honesty_score": 0.86,
                "resilience_score": 0.87,
                "reciprocity_norm": 0.78,
                "avg_response_time_ms": 3600.0,
                "answer_change_rate": 0.04,
                "session_duration_sec": 420.0,
                "dropout_count": 0,
                "scroll_hesitation_score": 0.12,
                "risk_response_speed_ratio": 0.70,
                "typing_speed_wpm": 48.0,
                "text_sentiment_compound": 0.72,
                "text_agency_score": 0.88,
                "text_problem_solving_flag": 1,
                "text_semantic_dim1": 0.0,
                "text_semantic_dim2": 0.0,
                "psychological_credit_index": 0.79,
                "cognitive_consistency_index": 0.78,
                "repayment_intention_score": 0.58,
                "impulsivity_index": 0.41,
                "cognitive_load_index": 0.93,
                "engagement_score": 0.0,
                "behavioral_trust_score": 0.0,
                "device_type": NEUTRAL_DEVICE_TYPE,
                "time_of_day": NEUTRAL_TIME_OF_DAY,
            }
        ],
        columns=ALL_MODEL_FEATURES,
    )
    anchor = recompute_derived_columns(anchor)

    # Keep the semantic dimensions in a realistic range using the production PCA
    # projection from a strong narrative rather than arbitrary manual values.
    narrative_dataset = pd.DataFrame(
        [
            {
                **anchor.iloc[0].to_dict(),
                TARGET: 1,
                "gender": "female",
                "age_group": "26-35",
                "region": "semi-urban",
                "education_level": "secondary",
                "cohort_month": 12,
                "application_date": "2025-12-15",
                RAW_TEXT_RESPONSE_COLUMN: (
                    "When income dropped, I reviewed expenses, negotiated a payment plan, "
                    "found extra work, protected savings, and stayed transparent with lenders."
                ),
            }
        ]
    )
    aligned, raw_embeddings = align_text_features_from_raw_text(narrative_dataset)
    text_frame = prepare_model_feature_frame(aligned.loc[:, ALL_MODEL_FEATURES].copy())
    text_frame = apply_text_pca(text_frame, raw_embeddings, artifacts.text_pca)
    anchor.loc[:, "text_semantic_dim1"] = text_frame["text_semantic_dim1"].iloc[0]
    anchor.loc[:, "text_semantic_dim2"] = text_frame["text_semantic_dim2"].iloc[0]
    return neutralize_operational_metadata_features(anchor)


def sweep_tabnet_feature(
    *,
    artifacts: Any,
    tabnet_model: Any,
    anchor_feature_frame: pd.DataFrame,
    feature_name: str,
    values: np.ndarray,
    masked_features: tuple[str, ...] = (),
    mask_replacements: dict[str, Any] | None = None,
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for value in values:
        feature_frame = anchor_feature_frame.copy()
        feature_frame.loc[:, feature_name] = float(value)
        if feature_name in {
            "scroll_hesitation_score",
            "answer_change_rate",
            "dropout_count",
            "risk_response_speed_ratio",
            "risk_attitude",
            "CRT_score",
            "avg_response_time_ms",
        }:
            feature_frame = recompute_derived_columns(feature_frame)
        feature_frame = neutralize_operational_metadata_features(feature_frame)
        if masked_features:
            for masked_feature in masked_features:
                feature_frame.loc[:, masked_feature] = (mask_replacements or {})[masked_feature]
        processed = transform_features(artifacts.preprocessor, feature_frame)
        probability = float(tabnet_model.predict_proba(processed)[:, 1][0])
        rows.append({"value": float(value), "probability": probability})
    return rows


def sweep_probability_fn_feature(
    *,
    artifacts: Any,
    probability_fn: Any,
    anchor_feature_frame: pd.DataFrame,
    feature_name: str,
    values: np.ndarray,
    masked_features: tuple[str, ...] = (),
    mask_replacements: dict[str, Any] | None = None,
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for value in values:
        feature_frame = anchor_feature_frame.copy()
        feature_frame.loc[:, feature_name] = float(value)
        if feature_name in {
            "scroll_hesitation_score",
            "answer_change_rate",
            "dropout_count",
            "risk_response_speed_ratio",
            "risk_attitude",
            "CRT_score",
            "avg_response_time_ms",
        }:
            feature_frame = recompute_derived_columns(feature_frame)
        feature_frame = neutralize_operational_metadata_features(feature_frame)
        if masked_features:
            for masked_feature in masked_features:
                feature_frame.loc[:, masked_feature] = (mask_replacements or {})[masked_feature]
        rows.append(
            {
                "value": float(value),
                "probability": float(np.asarray(probability_fn(feature_frame), dtype=float)[0]),
            }
        )
    return rows


def fit_critical_feature_monotonic_postprocessor(
    *,
    feature_frame: pd.DataFrame,
    y_true: np.ndarray,
    feature_names: tuple[str, ...],
) -> CriticalFeatureMonotonicPostProcessor:
    directions = {
        feature_name: SENSITIVITY_FEATURES[feature_name]
        for feature_name in feature_names
    }
    calibrators: dict[str, IsotonicRegression] = {}
    weights: dict[str, float] = {}
    y_array = np.asarray(y_true, dtype=int)
    for feature_name, direction in directions.items():
        raw_values = feature_frame[feature_name].to_numpy(dtype=float)
        transformed_values = raw_values if direction == "increasing" else 1.0 - raw_values
        calibrator = IsotonicRegression(out_of_bounds="clip", increasing=True)
        calibrator.fit(transformed_values, y_array)
        component_predictions = calibrator.predict(transformed_values)
        calibrators[feature_name] = calibrator
        weights[feature_name] = max(safe_auc(y_array, component_predictions) - 0.5, 0.01)

    weight_sum = sum(weights.values())
    normalized_weights = {
        feature_name: float(weight / weight_sum)
        for feature_name, weight in weights.items()
    }
    return CriticalFeatureMonotonicPostProcessor(
        feature_directions=directions,
        calibrators=calibrators,
        feature_weights=normalized_weights,
    )


def recompute_derived_columns(feature_frame: pd.DataFrame) -> pd.DataFrame:
    updated = feature_frame.copy()
    derived = compute_derived_features(updated.iloc[0].to_dict())
    for feature_name in DERIVED_FEATURES:
        updated.loc[:, feature_name] = float(derived[feature_name])
    return updated.loc[:, ALL_MODEL_FEATURES]


def evaluate_monotonic_acceptance_gates(
    sensitivity: dict[str, Any],
    *,
    material_tolerance: float = 0.02,
    local_tolerance: float = 0.05,
) -> dict[str, Any]:
    gate_results = []
    for feature_name, payload in sensitivity["feature_sweeps"].items():
        direction: PositiveDirection = payload["expected_direction"]
        points = payload["new_tabnet"]
        probabilities = np.asarray([point["probability"] for point in points], dtype=float)
        endpoint_delta = float(probabilities[-1] - probabilities[0])
        diffs = np.diff(probabilities)
        if direction == "increasing":
            endpoint_passed = endpoint_delta >= -material_tolerance
            local_passed = bool(np.min(diffs) >= -local_tolerance)
            worst_local_violation = float(np.min(diffs))
        else:
            endpoint_passed = endpoint_delta <= material_tolerance
            local_passed = bool(np.max(diffs) <= local_tolerance)
            worst_local_violation = float(np.max(diffs))

        gate_results.append(
            {
                "feature": feature_name,
                "expected_direction": direction,
                "endpoint_delta": endpoint_delta,
                "worst_local_step": worst_local_violation,
                "endpoint_passed": bool(endpoint_passed),
                "local_passed": bool(local_passed),
                "passed": bool(endpoint_passed and local_passed),
            }
        )

    return {
        "passed": all(result["passed"] for result in gate_results),
        "material_tolerance": material_tolerance,
        "local_tolerance": local_tolerance,
        "results": gate_results,
    }


def evaluate_metadata_stability_gate(
    *,
    artifacts: Any,
    tabnet_model: Any,
    max_allowed_delta: float,
) -> dict[str, Any]:
    anchor = build_strong_anchor_feature_frame(artifacts)
    variant_probabilities: dict[str, float] = {}
    for device_type in ["mobile", "desktop", "tablet"]:
        for time_of_day in ["morning", "afternoon", "evening", "night"]:
            variant = anchor.copy()
            variant.loc[:, "device_type"] = device_type
            variant.loc[:, "time_of_day"] = time_of_day
            variant = neutralize_operational_metadata_features(variant)
            processed = transform_features(artifacts.preprocessor, variant)
            variant_probabilities[f"{device_type}_{time_of_day}"] = float(
                tabnet_model.predict_proba(processed)[:, 1][0]
            )
    values = list(variant_probabilities.values())
    delta = float(max(values) - min(values))
    return {
        "passed": delta <= max_allowed_delta,
        "max_allowed_delta": max_allowed_delta,
        "max_observed_delta": delta,
        "variant_probabilities": variant_probabilities,
        "note": "Variants are neutralized before preprocessing to match the runtime metadata policy.",
    }


def build_counterfactual_stability_audit(
    *,
    artifacts: Any,
    prepared: PreparedCompatibleData,
    probability_fn: Any,
    sample_size: int,
    tolerance: float,
    features: tuple[str, ...],
    step: float,
) -> dict[str, Any]:
    test_frame = prepared.feature_frame.loc[prepared.test_mask].reset_index(drop=True)
    if test_frame.empty:
        return {"sample_count": 0, "feature_results": {}}

    sampled_frame = test_frame.iloc[: min(sample_size, len(test_frame))].reset_index(drop=True)
    base_probabilities = np.asarray(probability_fn(sampled_frame), dtype=float)
    feature_results: dict[str, Any] = {}
    for feature_name in features:
        direction = SENSITIVITY_FEATURES[feature_name]
        counterfactual_rows = []
        realized_changes = []
        for _, row in sampled_frame.iterrows():
            variant = apply_counterfactual_feature_shift(
                row=row.to_dict(),
                feature_name=feature_name,
                direction=direction,
                favorable=True,
                step=step,
            )
            if variant is None:
                counterfactual_rows.append(row.to_dict())
                realized_changes.append(0.0)
                continue
            for masked_feature in prepared.masked_features:
                variant[masked_feature] = prepared.mask_replacements[masked_feature]
            counterfactual_rows.append(variant)
            realized_changes.append(float(variant[feature_name]) - float(row[feature_name]))

        counterfactual_frame = pd.DataFrame(counterfactual_rows, columns=ALL_MODEL_FEATURES)
        counterfactual_probabilities = np.asarray(probability_fn(counterfactual_frame), dtype=float)
        deltas = counterfactual_probabilities - base_probabilities
        feature_results[feature_name] = {
            "expected_direction": direction,
            "sample_count": int(len(sampled_frame)),
            "mean_delta": float(deltas.mean()),
            "p05_delta": float(np.percentile(deltas, 5)),
            "worst_delta": float(deltas.min()),
            "violation_rate": float(np.mean(deltas < -tolerance)),
            "violation_count": int(np.sum(deltas < -tolerance)),
            "average_realized_feature_shift": float(np.mean(realized_changes)),
        }

    return {
        "sample_count": int(len(sampled_frame)),
        "tolerance": float(tolerance),
        "step": float(step),
        "feature_results": feature_results,
    }


def evaluate_counterfactual_acceptance_gate(
    audit: dict[str, Any],
    *,
    max_violation_rate: float,
    max_worst_delta: float,
) -> dict[str, Any]:
    results = []
    for feature_name, feature_result in audit.get("feature_results", {}).items():
        violation_rate = float(feature_result["violation_rate"])
        worst_delta = float(feature_result["worst_delta"])
        results.append(
            {
                "feature": feature_name,
                "violation_rate": violation_rate,
                "worst_delta": worst_delta,
                "passed": bool(
                    violation_rate <= max_violation_rate
                    and worst_delta >= -max_worst_delta
                ),
            }
        )
    return {
        "passed": all(result["passed"] for result in results),
        "max_violation_rate": float(max_violation_rate),
        "max_worst_delta": float(max_worst_delta),
        "results": results,
    }


def build_disagreement_audit(
    *,
    artifacts: Any,
    tabnet_model: Any,
    prepared: PreparedCompatibleData,
) -> dict[str, Any]:
    base_models = dict(artifacts.base_models)
    base_models["tabnet"] = tabnet_model
    bundle = EnsembleInferenceBundle(
        stacking_model=artifacts.model,
        base_models=base_models,
        base_model_order=tuple(artifacts.stacking_config["base_model_order"]),
        preprocessor=artifacts.preprocessor,
        stacking_config=artifacts.stacking_config,
    )
    meta_features = build_ensemble_meta_features(
        bundle,
        prepared.X_processed[prepared.test_mask.to_numpy()],
    )
    debug = meta_features.mitigation_debug
    peer_mean = np.asarray(debug["peer_mean_probability"], dtype=float)
    raw_tabnet = np.asarray(debug["raw_tabnet_probability"], dtype=float)
    disagreement = np.asarray(debug["disagreement_magnitude"], dtype=float)
    trigger_mask = np.asarray(debug["trigger_mask"], dtype=bool)
    return {
        "trigger_rate": float(trigger_mask.mean()),
        "trigger_count": int(trigger_mask.sum()),
        "mean_peer_probability": float(peer_mean.mean()),
        "mean_tabnet_probability": float(raw_tabnet.mean()),
        "mean_disagreement": float(disagreement.mean()),
        "p95_positive_disagreement": float(np.percentile(disagreement, 95)),
        "p99_positive_disagreement": float(np.percentile(disagreement, 99)),
    }


def build_ensemble_compatibility_report(
    *,
    artifacts: Any,
    repaired_prepared: PreparedCompatibleData,
    old_tabnet: Any,
    new_tabnet: Any,
    evaluate_reentry: bool,
) -> dict[str, Any]:
    X_test = repaired_prepared.X_processed[repaired_prepared.test_mask.to_numpy()]
    y_test = repaired_prepared.y_test
    if not evaluate_reentry:
        return {
            "evaluated": False,
            "reason": "candidate_failed_promotion_gates",
        }

    old_bundle = build_bundle_with_tabnet(artifacts, old_tabnet)
    new_bundle = build_bundle_with_tabnet(artifacts, new_tabnet)
    old_meta = build_ensemble_meta_features(old_bundle, X_test)
    new_meta = build_ensemble_meta_features(new_bundle, X_test)

    reports = {
        "current_runtime_old_tabnet_with_guard": evaluate_probability_model(
            y_true=y_test,
            probabilities=artifacts.model.predict_proba(
                old_meta.adjusted_meta_features_matrix
            )[:, 1],
            model_name="current_runtime_old_tabnet_with_guard",
            split="repaired_dataset_test_months_11_12",
        ),
        "repaired_tabnet_with_guard": evaluate_probability_model(
            y_true=y_test,
            probabilities=artifacts.model.predict_proba(
                new_meta.adjusted_meta_features_matrix
            )[:, 1],
            model_name="repaired_tabnet_with_guard",
            split="repaired_dataset_test_months_11_12",
        ),
    }

    raw_new = new_meta.raw_meta_features_matrix
    base_model_order = tuple(artifacts.stacking_config["base_model_order"])
    tabnet_index = base_model_order.index("tabnet")
    peer_indices = [index for index, name in enumerate(base_model_order) if name != "tabnet"]
    peer_mean = raw_new[:, peer_indices].mean(axis=1)

    without_tabnet = raw_new.copy()
    without_tabnet[:, tabnet_index] = peer_mean
    reports["without_tabnet_peer_mean_substitution"] = evaluate_probability_model(
        y_true=y_test,
        probabilities=artifacts.model.predict_proba(without_tabnet)[:, 1],
        model_name="without_tabnet_peer_mean_substitution",
        split="repaired_dataset_test_months_11_12",
    )

    reduced_tabnet = raw_new.copy()
    reduced_tabnet[:, tabnet_index] = 0.50 * raw_new[:, tabnet_index] + 0.50 * peer_mean
    reports["repaired_tabnet_50pct_peer_blend"] = evaluate_probability_model(
        y_true=y_test,
        probabilities=artifacts.model.predict_proba(reduced_tabnet)[:, 1],
        model_name="repaired_tabnet_50pct_peer_blend",
        split="repaired_dataset_test_months_11_12",
    )
    return {"evaluated": True, "variants": reports}


def build_bundle_with_tabnet(artifacts: Any, tabnet_model: Any) -> EnsembleInferenceBundle:
    base_models = dict(artifacts.base_models)
    base_models["tabnet"] = tabnet_model
    return EnsembleInferenceBundle(
        stacking_model=artifacts.model,
        base_models=base_models,
        base_model_order=tuple(artifacts.stacking_config["base_model_order"]),
        preprocessor=artifacts.preprocessor,
        stacking_config=artifacts.stacking_config,
    )


def evaluate_probability_model(
    *,
    y_true: np.ndarray,
    probabilities: np.ndarray,
    model_name: str,
    split: str,
) -> dict[str, Any]:
    probabilities = np.asarray(probabilities, dtype=float)
    metrics = compute_binary_classification_metrics(
        y_true,
        probabilities,
        model_name=model_name,
        model_type="tabnet" if "tabnet" in model_name else "ensemble_variant",
        split=split,
    )
    return {
        **metrics,
        "probability_summary": {
            "mean": float(probabilities.mean()),
            "std": float(probabilities.std()),
            "min": float(probabilities.min()),
            "p05": float(np.percentile(probabilities, 5)),
            "p50": float(np.percentile(probabilities, 50)),
            "p95": float(np.percentile(probabilities, 95)),
            "max": float(probabilities.max()),
        },
    }


def build_calibration_audit(
    *,
    y_validation: np.ndarray,
    validation_probabilities: np.ndarray,
    y_test: np.ndarray,
    test_probabilities: np.ndarray,
) -> dict[str, Any]:
    validation_probabilities = np.asarray(validation_probabilities, dtype=float)
    test_probabilities = np.asarray(test_probabilities, dtype=float)

    isotonic = IsotonicRegression(out_of_bounds="clip")
    isotonic.fit(validation_probabilities, y_validation)
    validation_isotonic = isotonic.predict(validation_probabilities)
    test_isotonic = isotonic.predict(test_probabilities)

    platt = LogisticRegression(max_iter=1000, solver="lbfgs")
    platt.fit(validation_probabilities.reshape(-1, 1), y_validation)
    validation_platt = platt.predict_proba(validation_probabilities.reshape(-1, 1))[:, 1]
    test_platt = platt.predict_proba(test_probabilities.reshape(-1, 1))[:, 1]

    return {
        "validation": {
            "raw": calibration_metrics(y_validation, validation_probabilities),
            "isotonic": calibration_metrics(y_validation, validation_isotonic),
            "platt": calibration_metrics(y_validation, validation_platt),
        },
        "test": {
            "raw": calibration_metrics(y_test, test_probabilities),
            "isotonic": calibration_metrics(y_test, test_isotonic),
            "platt": calibration_metrics(y_test, test_platt),
        },
    }


def calibration_metrics(y_true: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    return {
        "auc_roc": safe_auc(y_true, probabilities),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "expected_calibration_error": float(expected_calibration_error(y_true, probabilities)),
    }


def build_label_monotonic_sanity(dataset: pd.DataFrame) -> dict[str, Any]:
    checks: dict[str, PositiveDirection] = {
        "scroll_hesitation_score": "decreasing",
        "engagement_score": "increasing",
        "numeracy_score": "increasing",
        "future_orientation": "increasing",
        "resilience_score": "increasing",
        "text_agency_score": "increasing",
        "repayment_intention_score": "increasing",
        "psychological_credit_index": "increasing",
    }
    output = {}
    for feature_name, direction in checks.items():
        output[feature_name] = binned_label_direction(
            dataset,
            feature_name=feature_name,
            expected_direction=direction,
        )
    return output


def binned_label_direction(
    dataset: pd.DataFrame,
    *,
    feature_name: str,
    expected_direction: PositiveDirection,
) -> dict[str, Any]:
    quantiles = pd.qcut(dataset[feature_name], q=5, duplicates="drop")
    grouped = dataset.groupby(quantiles, observed=False)[TARGET].mean()
    rates = [float(value) for value in grouped.to_numpy(dtype=float)]
    endpoint_delta = rates[-1] - rates[0]
    passed = endpoint_delta >= 0 if expected_direction == "increasing" else endpoint_delta <= 0
    return {
        "expected_direction": expected_direction,
        "bin_repayment_rates": rates,
        "endpoint_delta": float(endpoint_delta),
        "passed": bool(passed),
    }


def build_strong_profile_summary(dataset: pd.DataFrame) -> dict[str, Any]:
    masks = {
        "strong_profiles": (
            (dataset["numeracy_score"] >= 0.8)
            & (dataset["future_orientation"] >= 0.8)
            & (dataset["resilience_score"] >= 0.8)
        ),
        "resilience_heavy": dataset["resilience_score"] >= 0.8,
        "numeracy_heavy": dataset["numeracy_score"] >= 0.8,
        "future_heavy": dataset["future_orientation"] >= 0.8,
    }
    output = {}
    for name, mask in masks.items():
        subset = dataset.loc[mask]
        output[name] = {
            "count": int(mask.sum()),
            "repayment_rate": None if subset.empty else float(subset[TARGET].mean()),
            "scroll_hesitation_mean": None
            if subset.empty
            else float(subset["scroll_hesitation_score"].mean()),
            "engagement_mean": None
            if subset.empty
            else float(subset["engagement_score"].mean()),
            "device_mix": {} if subset.empty else group_share(subset, "device_type"),
            "time_mix": {} if subset.empty else group_share(subset, "time_of_day"),
        }
    return output


def flatten_sensitivity_to_frame(sensitivity: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for feature_name, payload in sensitivity["feature_sweeps"].items():
        for model_name in ["old_tabnet", "new_tabnet"]:
            for point in payload[model_name]:
                rows.append(
                    {
                        "feature": feature_name,
                        "expected_direction": payload["expected_direction"],
                        "model": model_name,
                        "value": point["value"],
                        "probability": point["probability"],
                    }
                )
    return pd.DataFrame(rows)


def write_sensitivity_plots(
    sensitivity: dict[str, Any],
    *,
    output_dir: Path,
) -> list[Path]:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return write_sensitivity_svg_plots(sensitivity, output_dir=output_dir)

    paths: list[Path] = []
    for feature_name, payload in sensitivity["feature_sweeps"].items():
        fig, ax = plt.subplots(figsize=(7, 4))
        for model_name, color in [("old_tabnet", "#b64242"), ("new_tabnet", "#2d6f51")]:
            points = payload[model_name]
            ax.plot(
                [point["value"] for point in points],
                [point["probability"] for point in points],
                marker="o",
                label=model_name,
                color=color,
            )
        ax.set_title(f"TabNet sensitivity: {feature_name}")
        ax.set_xlabel(feature_name)
        ax.set_ylabel("Repayment probability")
        ax.set_ylim(0.0, 1.0)
        ax.legend(loc="best")
        ax.grid(alpha=0.25)
        path = output_dir / f"{feature_name}_sensitivity.png"
        fig.tight_layout()
        fig.savefig(path, dpi=140)
        plt.close(fig)
        paths.append(path)
    return paths


def write_sensitivity_svg_plots(
    sensitivity: dict[str, Any],
    *,
    output_dir: Path,
) -> list[Path]:
    paths: list[Path] = []
    for feature_name, payload in sensitivity["feature_sweeps"].items():
        path = output_dir / f"{feature_name}_sensitivity.svg"
        path.write_text(
            build_sensitivity_svg(
                feature_name=feature_name,
                old_points=payload["old_tabnet"],
                new_points=payload["new_tabnet"],
            ),
            encoding="utf-8",
        )
        paths.append(path)
    return paths


def build_sensitivity_svg(
    *,
    feature_name: str,
    old_points: list[dict[str, float]],
    new_points: list[dict[str, float]],
) -> str:
    width = 720
    height = 420
    left = 64
    right = 24
    top = 42
    bottom = 62
    plot_width = width - left - right
    plot_height = height - top - bottom

    def project(point: dict[str, float]) -> tuple[float, float]:
        x = left + float(point["value"]) * plot_width
        y = top + (1.0 - float(point["probability"])) * plot_height
        return x, y

    def polyline(points: list[dict[str, float]]) -> str:
        return " ".join(
            f"{x:.2f},{y:.2f}" for x, y in (project(point) for point in points)
        )

    old_circles = "\n".join(
        f'<circle cx="{project(point)[0]:.2f}" cy="{project(point)[1]:.2f}" '
        'r="3.5" fill="#b64242" />'
        for point in old_points
    )
    new_circles = "\n".join(
        f'<circle cx="{project(point)[0]:.2f}" cy="{project(point)[1]:.2f}" '
        'r="3.5" fill="#2d6f51" />'
        for point in new_points
    )
    horizontal_grid = "\n".join(
        f'<line x1="{left}" y1="{top + i * plot_height / 4:.2f}" '
        f'x2="{left + plot_width}" y2="{top + i * plot_height / 4:.2f}" '
        'stroke="#d9d9d9" stroke-width="1" />'
        for i in range(5)
    )
    y_labels = "\n".join(
        f'<text x="{left - 12}" y="{top + i * plot_height / 4 + 5:.2f}" '
        'font-family="Arial" font-size="12" text-anchor="end" fill="#444">'
        f"{1.0 - i * 0.25:.2f}</text>"
        for i in range(5)
    )
    x_labels = "\n".join(
        f'<text x="{left + i * plot_width / 5:.2f}" y="{height - 28}" '
        'font-family="Arial" font-size="12" text-anchor="middle" fill="#444">'
        f"{i / 5:.1f}</text>"
        for i in range(6)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff" />
  <text x="{left}" y="26" font-family="Arial" font-size="18" font-weight="700" fill="#222">TabNet sensitivity: {feature_name}</text>
  {horizontal_grid}
  <line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#222" stroke-width="1.2" />
  <line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#222" stroke-width="1.2" />
  {y_labels}
  {x_labels}
  <polyline points="{polyline(old_points)}" fill="none" stroke="#b64242" stroke-width="2.5" />
  <polyline points="{polyline(new_points)}" fill="none" stroke="#2d6f51" stroke-width="2.5" />
  {old_circles}
  {new_circles}
  <rect x="{width - 190}" y="52" width="156" height="54" fill="#ffffff" stroke="#cccccc" />
  <line x1="{width - 176}" y1="72" x2="{width - 142}" y2="72" stroke="#b64242" stroke-width="3" />
  <text x="{width - 132}" y="76" font-family="Arial" font-size="12" fill="#222">old_tabnet</text>
  <line x1="{width - 176}" y1="92" x2="{width - 142}" y2="92" stroke="#2d6f51" stroke-width="3" />
  <text x="{width - 132}" y="96" font-family="Arial" font-size="12" fill="#222">new_tabnet</text>
  <text x="{left + plot_width / 2:.2f}" y="{height - 8}" font-family="Arial" font-size="12" text-anchor="middle" fill="#444">{feature_name}</text>
  <text x="18" y="{top + plot_height / 2:.2f}" font-family="Arial" font-size="12" text-anchor="middle" fill="#444" transform="rotate(-90 18 {top + plot_height / 2:.2f})">Repayment probability</text>
</svg>
"""


def group_mean(dataset: pd.DataFrame, group_column: str, value_column: str) -> dict[str, float]:
    return {
        str(key): float(value)
        for key, value in dataset.groupby(group_column, observed=False)[value_column]
        .mean()
        .sort_index()
        .items()
    }


def group_share(dataset: pd.DataFrame, column: str) -> dict[str, float]:
    return {
        str(key): float(value)
        for key, value in dataset[column].value_counts(normalize=True).sort_index().items()
    }


def categorical_label_correlations(dataset: pd.DataFrame, column: str) -> dict[str, float]:
    dummy_frame = pd.get_dummies(dataset[column], prefix=column)
    return {
        column_name: safe_corr(dummy_frame[column_name], dataset[TARGET])
        for column_name in dummy_frame.columns
    }


def describe_series(series: pd.Series) -> dict[str, float]:
    values = series.to_numpy(dtype=float)
    return {
        "mean": float(values.mean()),
        "std": float(values.std()),
        "min": float(values.min()),
        "p05": float(np.percentile(values, 5)),
        "p25": float(np.percentile(values, 25)),
        "p50": float(np.percentile(values, 50)),
        "p75": float(np.percentile(values, 75)),
        "p95": float(np.percentile(values, 95)),
        "max": float(values.max()),
    }


def safe_corr(left: pd.Series | np.ndarray, right: pd.Series | np.ndarray) -> float:
    left_array = np.asarray(left, dtype=float)
    right_array = np.asarray(right, dtype=float)
    if left_array.std() == 0.0 or right_array.std() == 0.0:
        return 0.0
    return float(np.corrcoef(left_array, right_array)[0, 1])


def safe_auc(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        return 0.5
    return float(roc_auc_score(y_true, probabilities))


def _tabnet_guard_enabled(stacking_config: dict[str, Any]) -> bool:
    payload = stacking_config.get("tabnet_mitigation")
    return bool(isinstance(payload, dict) and payload.get("enabled", False))


def to_python_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


if __name__ == "__main__":
    main()
