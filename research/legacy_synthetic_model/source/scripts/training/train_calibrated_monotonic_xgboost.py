"""Train and publish the calibrated monotonic XGBoost runtime bundle.

This entrypoint is intentionally self-contained: it can rebuild the checked-in
monotonic runtime model, reports, explainers, and production manifest from the
deterministic synthetic generator without relying on an external candidate
folder under runtime/.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Final
import warnings

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.core.constants import (
    SCORE_BASE,
    SCORE_LOG_ODDS_FACTOR,
    SCORE_PDO,
    SCORE_ANCHOR_SCORE,
    SCORE_ANCHOR_ODDS,
)
from backend.app.core.paths import (
    MODEL_ARTIFACTS_DIR,
    MODEL_EXPLAINERS_DIR,
    MODEL_PREPROCESSORS_DIR,
    MODEL_REGISTRY_DIR,
    MODEL_REPORTS_DIR,
)
from backend.app.services.scoring import (
    GOVERNED_PROBABILITY_MAX,
    GOVERNED_PROBABILITY_MIN,
    _calculate_governance_multiplier,
)
from backend.ml.data_generation.generator import (
    DEFAULT_ROW_COUNT,
    DEFAULT_SEED,
    generate_synthetic_dataset,
)
from backend.ml.data_generation.validators import validate_synthetic_dataset
from backend.ml.evaluation.drift import build_psi_report_from_prepared_data
from backend.ml.evaluation.fairness import build_fairness_report, save_fairness_report
from backend.ml.evaluation.metrics import (
    build_population_percentiles_payload,
    build_population_percentiles_report,
    build_split_evaluation_details,
    compute_binary_classification_metrics,
    optimal_threshold,
)
from backend.ml.explainability.dice_explainer import (
    build_default_persisted_dice_explainer,
    save_persisted_dice_explainer,
)
from backend.ml.explainability.global_importance import (
    build_global_importance_report_for_candidate_models,
    save_global_importance_report,
)
from backend.ml.explainability.shap_explainer import PersistedShapExplainer
from backend.ml.preprocessing.feature_registry import ALL_MODEL_FEATURES
from backend.ml.preprocessing.pipeline import (
    fit_preprocessor,
    prepare_temporal_data,
    transform_features,
)
from backend.ml.registry.production_manifest import compute_file_sha256
from backend.ml.registry.promotion_gates import (
    PROMOTION_COMPATIBLE_GATE_STATUSES,
    build_promotion_gate_summary_from_manifest,
    evaluate_promotion_gates,
    load_promotion_gate_policy,
)
from backend.ml.training.classical.monotonic_constraints import (
    MONOTONIC_TREE_FEATURE_WEIGHT_MAP,
    MONOTONIC_TREE_MASKED_FEATURES,
    apply_monotonic_tree_feature_masking,
    build_feature_weight_vector,
    build_monotonic_constraint_vector,
    neutralize_operational_metadata_for_training,
)

MODEL_NAME: Final[str] = "xgboost_monotonic"
MODEL_TYPE: Final[str] = "classical_monotonic"
VALIDATION_SPLIT: Final[str] = "validation_months_9_10"
TEST_SPLIT: Final[str] = "test_months_11_12"
DEFAULT_SCORE_BASE: Final[float] = SCORE_BASE
DEFAULT_SCORE_LOG_ODDS_FACTOR: Final[float] = SCORE_LOG_ODDS_FACTOR
DEFAULT_MODEL_VERSION: Final[str] = "0.9.0"
DEFAULT_MANIFEST_VERSION: Final[str] = "xgboost_monotonic_answer_only_v6"
DEFAULT_CODE_REF: Final[str] = "codex/scoring-production-hardening"


@dataclass(frozen=True)
class CalibratedMonotonicTrainingResult:
    run_id: str
    manifest_path: Path
    gate_status: str
    promotion_status: str
    test_auc_roc: float
    test_expected_calibration_error: float
    worst_auc_gap: float
    individual_fairness_flagged_pair_share: float
    individual_fairness_max_score_gap: int
    score_mapping: dict[str, Any]


def train_calibrated_monotonic_xgboost(
    *,
    row_count: int = DEFAULT_ROW_COUNT,
    seed: int = DEFAULT_SEED,
    device: str = "cuda",
    allow_cpu_fallback: bool = False,
    score_base: float = DEFAULT_SCORE_BASE,
    score_log_odds_factor: float = DEFAULT_SCORE_LOG_ODDS_FACTOR,
    code_ref: str = DEFAULT_CODE_REF,
    model_version: str = DEFAULT_MODEL_VERSION,
    manifest_version: str = DEFAULT_MANIFEST_VERSION,
) -> CalibratedMonotonicTrainingResult:
    """Regenerate the calibrated monotonic runtime bundle and manifest."""

    _assert_xgboost_device_available(device, allow_cpu_fallback=allow_cpu_fallback)
    from xgboost import XGBClassifier

    np.random.seed(seed)
    warnings.filterwarnings("ignore", category=FutureWarning)

    dataset = generate_synthetic_dataset(row_count=row_count, seed=seed)
    validate_synthetic_dataset(dataset, expected_row_count=row_count)

    prepared = prepare_temporal_data(dataset)
    policy_frame = neutralize_operational_metadata_for_training(prepared.feature_frame)
    policy_frame, mask_replacements = apply_monotonic_tree_feature_masking(
        policy_frame,
        train_mask=dataset["cohort_month"].isin(range(1, 9)),
        masked_features=MONOTONIC_TREE_MASKED_FEATURES,
    )

    preprocessor_path = MODEL_PREPROCESSORS_DIR / "preprocessor_monotonic.pkl"
    preprocessor = fit_preprocessor(
        policy_frame.loc[prepared.train.indices],
        artifact_path=preprocessor_path,
    )
    processed_features = transform_features(preprocessor, policy_frame)
    transformed_feature_names = preprocessor.get_feature_names_out().tolist()
    monotonic_constraints = build_monotonic_constraint_vector(transformed_feature_names)
    constraint_counts = _count_constraints(monotonic_constraints)
    feature_weights = build_feature_weight_vector(transformed_feature_names)

    train_mask = prepared.feature_frame.index.isin(prepared.train.indices)
    validation_mask = prepared.feature_frame.index.isin(prepared.validation.indices)
    test_mask = prepared.feature_frame.index.isin(prepared.test.indices)
    X_train = processed_features[train_mask]
    X_validation = processed_features[validation_mask]
    X_test = processed_features[test_mask]
    y_train = prepared.train.y.to_numpy(dtype=int)
    y_validation = prepared.validation.y.to_numpy(dtype=int)
    y_test = prepared.test.y.to_numpy(dtype=int)

    xgboost_params = _build_xgboost_params(
        device=device,
        monotonic_constraints=monotonic_constraints,
        seed=seed,
    )
    raw_model = XGBClassifier(**xgboost_params)
    raw_model.fit(
        X_train,
        y_train,
        eval_set=[(X_validation, y_validation)],
        verbose=False,
        feature_weights=np.asarray(feature_weights, dtype=float),
    )
    calibrated_model = CalibratedClassifierCV(
        estimator=raw_model,
        method="isotonic",
        cv="prefit",
    )
    calibrated_model.fit(X_validation, y_validation)

    train_probs = _predict_positive_probabilities(calibrated_model, X_train)
    validation_probs = _predict_positive_probabilities(
        calibrated_model,
        X_validation,
    )
    test_probs = _predict_positive_probabilities(calibrated_model, X_test)
    population_probs = _predict_positive_probabilities(
        calibrated_model,
        processed_features,
    )

    score_mapping = _build_score_mapping(score_base, score_log_odds_factor)
    validation_threshold = optimal_threshold(y_validation, validation_probs)
    model_stats = [
        compute_binary_classification_metrics(
            y_validation,
            validation_probs,
            model_name=MODEL_NAME,
            model_type=MODEL_TYPE,
            split=VALIDATION_SPLIT,
            threshold=validation_threshold,
        ),
        compute_binary_classification_metrics(
            y_test,
            test_probs,
            model_name=MODEL_NAME,
            model_type=MODEL_TYPE,
            split=TEST_SPLIT,
            threshold=validation_threshold,
        ),
    ]
    evaluation_details = {
        VALIDATION_SPLIT: {
            MODEL_NAME: build_split_evaluation_details(
                y_validation,
                validation_probs,
                model_name=MODEL_NAME,
                model_type=MODEL_TYPE,
                split=VALIDATION_SPLIT,
                threshold=validation_threshold,
            )
        },
        TEST_SPLIT: {
            MODEL_NAME: build_split_evaluation_details(
                y_test,
                test_probs,
                model_name=MODEL_NAME,
                model_type=MODEL_TYPE,
                split=TEST_SPLIT,
                threshold=validation_threshold,
            )
        },
    }
    baseline_metrics = _load_baseline_metrics()
    run_id = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S_xgboost_monotonic_calibrated"
    )
    metrics_payload = {
        "run_id": run_id,
        "split_row_counts": {
            "train": int(len(y_train)),
            "validation": int(len(y_validation)),
            "test": int(len(y_test)),
        },
        "model_stats": model_stats,
        "baselines": baseline_metrics,
        "evaluation_details": evaluation_details,
        "training_summary": {
            "calibration": "isotonic",
            "training_device": device,
            "parallel_workers": -1,
            "monotonic_constraint_counts": constraint_counts,
            "masked_features": sorted(mask_replacements),
            "feature_weights": dict(sorted(MONOTONIC_TREE_FEATURE_WEIGHT_MAP.items())),
        },
    }
    metrics_path = MODEL_REPORTS_DIR / "metrics_monotonic.json"
    _save_json(metrics_payload, metrics_path)

    baseline_metrics_path = MODEL_REPORTS_DIR / "baseline_metrics_monotonic.json"
    _save_json(baseline_metrics, baseline_metrics_path)

    policy_test_frame = policy_frame.loc[test_mask].reset_index(drop=True)
    post_governance_test_probs = _apply_post_model_governance(
        test_probs,
        policy_test_frame,
    )
    fairness_report = build_fairness_report(
        y_test,
        test_probs,
        prepared.test.protected.reset_index(drop=True),
        feature_frame=policy_test_frame,
        post_governance_probabilities=post_governance_test_probs,
        score_mapping_config=score_mapping,
    )
    fairness_path = MODEL_REPORTS_DIR / "fairness_report_monotonic.json"
    save_fairness_report(fairness_report, fairness_path)

    psi_report = build_psi_report_from_prepared_data(prepared)
    psi_path = MODEL_REPORTS_DIR / "psi_report_monotonic.json"
    _save_json(psi_report, psi_path)

    global_importance_report, _ = build_global_importance_report_for_candidate_models(
        {MODEL_NAME: raw_model},
        train_processed_features=X_train,
        test_processed_features=X_test,
        model_stats=model_stats,
        candidate_model_types={MODEL_NAME: MODEL_TYPE},
        feature_names=ALL_MODEL_FEATURES,
    )
    global_importance_path = MODEL_REPORTS_DIR / "global_importance_monotonic.json"
    save_global_importance_report(global_importance_report, global_importance_path)

    population_payload = build_population_percentiles_report(
        {
            MODEL_NAME: build_population_percentiles_payload(
                population_probs,
                model_name=MODEL_NAME,
                score_mapping_config=score_mapping,
            )
        },
        default_model_name=MODEL_NAME,
    )
    population_path = MODEL_REPORTS_DIR / "population_percentiles_monotonic.json"
    _save_json(population_payload, population_path)

    shap_path = MODEL_EXPLAINERS_DIR / "shap_explainer_monotonic.pkl"
    shap_explainer = _fit_surrogate_shap_explainer(
        X_train=X_train,
        train_probs=train_probs,
    )
    _save_joblib(shap_explainer, shap_path)

    dice_path = MODEL_EXPLAINERS_DIR / "dice_explainer_monotonic.pkl"
    save_persisted_dice_explainer(
        build_default_persisted_dice_explainer(model_name=MODEL_NAME),
        dice_path,
    )

    _prepare_xgboost_for_serving(raw_model)
    _prepare_xgboost_for_serving(calibrated_model)
    model_path = MODEL_ARTIFACTS_DIR / "xgboost_monotonic.pkl"
    _save_joblib(calibrated_model, model_path)

    artifact_spec = {
        "runtime_model": (model_path, "models/artifacts/xgboost_monotonic.pkl"),
        "preprocessor": (
            preprocessor_path,
            "models/preprocessors/preprocessor_monotonic.pkl",
        ),
        "shap_explainer": (shap_path, "models/explainers/shap_explainer_monotonic.pkl"),
        "dice_explainer": (dice_path, "models/explainers/dice_explainer_monotonic.pkl"),
        "metrics": (metrics_path, "models/reports/metrics_monotonic.json"),
        "baseline_metrics": (
            baseline_metrics_path,
            "models/reports/baseline_metrics_monotonic.json",
        ),
        "fairness_report": (
            fairness_path,
            "models/reports/fairness_report_monotonic.json",
        ),
        "psi_report": (psi_path, "models/reports/psi_report_monotonic.json"),
        "global_importance": (
            global_importance_path,
            "models/reports/global_importance_monotonic.json",
        ),
        "population_percentiles": (
            population_path,
            "models/reports/population_percentiles_monotonic.json",
        ),
    }
    artifacts_block = _build_artifacts_block(artifact_spec)
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    test_metrics = _find_test_metrics(model_stats)

    manifest = {
        "manifest_schema_version": "1.0.0",
        "manifest_version": manifest_version,
        "model_version": model_version,
        "run_id": run_id,
        "created_at": created_at,
        "code_ref": code_ref,
        "data_version": "synthetic_v3.1.0_answer_only",
        "feature_registry_version": "0.2.0",
        "runtime_model_name": MODEL_NAME,
        "runtime_model_type": MODEL_TYPE,
        "target": "repayment_label",
        "split": {
            "train": "cohort_month 1-8",
            "validation": "cohort_month 9-10",
            "test": "cohort_month 11-12",
        },
        "artifacts": artifacts_block,
        "metrics_summary": {
            "test_split": TEST_SPLIT,
            "test_auc_roc": test_metrics["auc_roc"],
            "expected_calibration_error": test_metrics["expected_calibration_error"],
            "calibration": "isotonic",
        },
        "fairness_summary": {
            "overall_auc": fairness_report["overall_auc"],
            "worst_auc_gap": fairness_report["worst_auc_gap"],
            "post_governance_available": True,
            "post_governance_overall_auc": fairness_report["post_governance_impact"][
                "overall_auc_after_governance"
            ],
            "individual_fairness_flagged_pair_share": fairness_report[
                "individual_fairness_proxy"
            ]["flagged_pair_share"],
            "individual_fairness_max_score_gap": fairness_report[
                "individual_fairness_proxy"
            ]["max_score_gap"],
            "verdict": fairness_report["verdict"],
        },
        "drift_summary": {
            "max_psi": psi_report["max_psi"],
            "verdict": psi_report["verdict"],
        },
        "score_mapping": score_mapping,
        "training_summary": {
            "row_count": int(row_count),
            "seed": int(seed),
            "training_device": device,
            "parallel_workers": -1,
            "calibration": "isotonic",
            "xgboost_params": _jsonable_xgboost_params(xgboost_params),
            "monotonic_constraint_counts": constraint_counts,
            "masked_features": sorted(mask_replacements),
            "feature_weights": dict(sorted(MONOTONIC_TREE_FEATURE_WEIGHT_MAP.items())),
        },
        "promotion_status": "candidate",
        "promotion_notes": (
            "Calibrated monotonic XGBoost bundle regenerated from the deterministic "
            "synthetic v2 generator. The runtime model uses isotonic calibration, "
            "manifest-backed score mapping, active monotonic constraints, and "
            "promotion-gate-aligned reports."
        ),
    }
    gate_summary = evaluate_promotion_gates(
        manifest=manifest,
        metrics_payload=metrics_payload,
        fairness_report=fairness_report,
        psi_report=psi_report,
        population_percentiles=population_payload,
        policy=load_promotion_gate_policy(),
    )
    promotion_status = (
        "promoted"
        if gate_summary is not None
        and gate_summary["status"] in PROMOTION_COMPATIBLE_GATE_STATUSES
        else "review_required"
    )
    manifest["promotion_status"] = promotion_status
    final_gate_summary = evaluate_promotion_gates(
        manifest=manifest,
        metrics_payload=metrics_payload,
        fairness_report=fairness_report,
        psi_report=psi_report,
        population_percentiles=population_payload,
        policy=load_promotion_gate_policy(),
    )
    manifest["promotion_gate_summary"] = final_gate_summary

    manifest_path = MODEL_REGISTRY_DIR / "production_manifest.json"
    _save_json(manifest, manifest_path)
    final_manifest_summary = build_promotion_gate_summary_from_manifest(
        manifest_path,
        repo_root=REPO_ROOT,
    )

    return CalibratedMonotonicTrainingResult(
        run_id=run_id,
        manifest_path=manifest_path,
        gate_status=str(final_manifest_summary["status"]),
        promotion_status=promotion_status,
        test_auc_roc=float(test_metrics["auc_roc"]),
        test_expected_calibration_error=float(
            test_metrics["expected_calibration_error"]
        ),
        worst_auc_gap=float(fairness_report["worst_auc_gap"]),
        individual_fairness_flagged_pair_share=float(
            fairness_report["individual_fairness_proxy"]["flagged_pair_share"]
        ),
        individual_fairness_max_score_gap=int(
            fairness_report["individual_fairness_proxy"]["max_score_gap"]
        ),
        score_mapping=score_mapping,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train the calibrated monotonic XGBoost AlterScore bundle.",
    )
    parser.add_argument("--row-count", type=int, default=DEFAULT_ROW_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument(
        "--allow-cpu-fallback",
        action="store_true",
        help="Allow training on CPU when the requested CUDA build is unavailable.",
    )
    parser.add_argument(
        "--score-base",
        type=float,
        default=DEFAULT_SCORE_BASE,
        help="Base credit score assigned to an even-odds repayment probability.",
    )
    parser.add_argument(
        "--score-log-odds-factor",
        type=float,
        default=DEFAULT_SCORE_LOG_ODDS_FACTOR,
        help="Log-odds score slope used by the manifest-backed score mapper.",
    )
    parser.add_argument("--code-ref", default=DEFAULT_CODE_REF)
    parser.add_argument("--model-version", default=DEFAULT_MODEL_VERSION)
    parser.add_argument("--manifest-version", default=DEFAULT_MANIFEST_VERSION)
    parser.add_argument(
        "--require-clean-pass",
        action="store_true",
        help="Return non-zero unless promotion gates pass without warnings.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(list(argv) if argv is not None else None)
    result = train_calibrated_monotonic_xgboost(
        row_count=args.row_count,
        seed=args.seed,
        device=args.device,
        allow_cpu_fallback=args.allow_cpu_fallback,
        score_base=args.score_base,
        score_log_odds_factor=args.score_log_odds_factor,
        code_ref=args.code_ref,
        model_version=args.model_version,
        manifest_version=args.manifest_version,
    )
    payload = asdict(result)
    payload["manifest_path"] = str(result.manifest_path)
    print(json.dumps(payload, indent=2, sort_keys=True))

    if args.require_clean_pass and result.gate_status != "passed":
        return 1
    if result.promotion_status != "promoted":
        return 1
    return 0


def _assert_xgboost_device_available(
    device: str,
    *,
    allow_cpu_fallback: bool,
) -> None:
    if device == "cpu":
        return
    try:
        import xgboost as xgb
    except ImportError as exc:
        raise RuntimeError("xgboost is required for monotonic training.") from exc

    build_info = xgb.build_info()
    if bool(build_info.get("USE_CUDA")):
        return
    if allow_cpu_fallback:
        return
    raise RuntimeError(
        "Requested CUDA training, but the installed xgboost build does not expose CUDA."
    )


def _build_xgboost_params(
    *,
    device: str,
    monotonic_constraints: tuple[int, ...],
    seed: int,
) -> dict[str, Any]:
    return {
        "n_estimators": 320,
        "learning_rate": 0.035,
        "max_depth": 2,
        "min_child_weight": 12,
        "reg_lambda": 3.0,
        "gamma": 0.05,
        "subsample": 0.88,
        "colsample_bytree": 0.9,
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "random_state": seed,
        "n_jobs": -1,
        "tree_method": "hist",
        "device": device,
        "monotone_constraints": monotonic_constraints,
        "verbosity": 0,
    }


def _build_score_mapping(
    score_base: float,
    score_log_odds_factor: float,
) -> dict[str, Any]:
    return {
        "method": "log_odds",
        "score_base": float(score_base),
        "log_odds_factor": float(score_log_odds_factor),
        "probability_clip_min": GOVERNED_PROBABILITY_MIN,
        "probability_clip_max": GOVERNED_PROBABILITY_MAX,
        "score_min": 300,
        "score_max": 850,
        "calibration": "isotonic",
        "policy": {
            "pdo": float(SCORE_PDO),
            "anchor_score": float(SCORE_ANCHOR_SCORE),
            "anchor_odds": float(SCORE_ANCHOR_ODDS),
            "note": "base and log_odds_factor are derived from pdo/anchor — do not hand-edit",
        },
    }


def _predict_positive_probabilities(model: Any, X: np.ndarray) -> np.ndarray:
    probabilities = np.asarray(model.predict_proba(X)[:, 1], dtype=float)
    if np.isnan(probabilities).any():
        raise ValueError("Calibrated monotonic model produced NaN probabilities.")
    if ((probabilities < 0.0) | (probabilities > 1.0)).any():
        raise ValueError(
            "Calibrated monotonic model produced probabilities outside [0, 1]."
        )
    return probabilities


def _apply_post_model_governance(
    probabilities: np.ndarray,
    feature_frame: Any,
) -> np.ndarray:
    adjusted_probabilities: list[float] = []
    for probability, feature_row in zip(
        np.asarray(probabilities, dtype=float),
        feature_frame.to_dict(orient="records"),
        strict=True,
    ):
        multiplier, _ = _calculate_governance_multiplier(feature_row)
        adjusted_probabilities.append(
            float(
                np.clip(
                    probability * multiplier,
                    GOVERNED_PROBABILITY_MIN,
                    GOVERNED_PROBABILITY_MAX,
                )
            )
        )
    return np.asarray(adjusted_probabilities, dtype=float)


def _fit_surrogate_shap_explainer(
    *,
    X_train: np.ndarray,
    train_probs: np.ndarray,
) -> PersistedShapExplainer:
    surrogate_labels = (np.asarray(train_probs, dtype=float) >= 0.5).astype(int)
    surrogate_model = LogisticRegression(max_iter=1_000, random_state=42)
    surrogate_model.fit(X_train, surrogate_labels)
    coefficients = np.asarray(surrogate_model.coef_, dtype=float)
    if coefficients.ndim == 2:
        coefficients = coefficients[-1]
    explainer = PersistedShapExplainer(
        model_name=MODEL_NAME,
        algorithm="exact_linear_shap",
        feature_names=tuple(ALL_MODEL_FEATURES),
        background_mean=np.asarray(np.mean(X_train, axis=0), dtype=float),
        background_size=int(X_train.shape[0]),
        coefficients=np.asarray(coefficients, dtype=float),
    )
    explainer.validate(expected_feature_names=ALL_MODEL_FEATURES)
    return explainer


def _prepare_xgboost_for_serving(model: Any) -> None:
    candidates = [model, getattr(model, "estimator", None)]
    for calibrated_classifier in getattr(model, "calibrated_classifiers_", []) or []:
        candidates.append(getattr(calibrated_classifier, "estimator", None))

    for candidate in candidates:
        if candidate is None:
            continue
        if hasattr(candidate, "get_xgb_params") and hasattr(candidate, "set_params"):
            candidate.set_params(device="cpu")


def _load_baseline_metrics() -> list[dict[str, Any]]:
    baseline_path = MODEL_REPORTS_DIR / "baseline_metrics.json"
    if not baseline_path.is_file():
        return []
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("baseline_metrics.json must contain a JSON list.")
    normalized_metrics: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, Mapping):
            continue
        normalized = dict(item)
        if normalized.get("model_name") == "simulated_loan_officer":
            normalized["model_name"] = "synthetic_heuristic"
        if "lift_vs_loan_officer" in normalized:
            normalized["lift_vs_synthetic_heuristic"] = normalized.pop(
                "lift_vs_loan_officer"
            )
        normalized_metrics.append(normalized)
    return normalized_metrics


def _build_artifacts_block(
    artifact_spec: Mapping[str, tuple[Path, str]],
) -> dict[str, dict[str, str]]:
    artifacts_block: dict[str, dict[str, str]] = {}
    for artifact_key, (file_path, relative_path) in artifact_spec.items():
        if not file_path.is_file():
            raise FileNotFoundError(f"Required artifact is missing: {file_path}")
        artifacts_block[artifact_key] = {
            "path": relative_path,
            "sha256": compute_file_sha256(file_path),
        }
    return artifacts_block


def _find_test_metrics(model_stats: list[dict[str, Any]]) -> dict[str, Any]:
    for item in model_stats:
        if item["model_name"] == MODEL_NAME and item["split"] == TEST_SPLIT:
            return item
    raise ValueError("Missing monotonic test metrics.")


def _count_constraints(constraints: tuple[int, ...]) -> dict[str, int]:
    return {
        "positive": int(sum(value == 1 for value in constraints)),
        "negative": int(sum(value == -1 for value in constraints)),
        "zero": int(sum(value == 0 for value in constraints)),
    }


def _jsonable_xgboost_params(params: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: (list(value) if isinstance(value, tuple) else value)
        for key, value in params.items()
    }


def _save_json(payload: Any, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _save_joblib(artifact: object, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output_path)


if __name__ == "__main__":
    raise SystemExit(main())
