"""Offline fairness report generation helpers for AlterScore."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from backend.app.core.paths import MODEL_REPORTS_DIR
from backend.ml.evaluation.metrics import (
    CALIBRATION_BIN_COUNT,
    compute_calibration_points,
    expected_calibration_error,
    select_best_test_auc_model,
)
from backend.ml.inference.score_mapper import probability_to_score
from backend.ml.preprocessing.feature_registry import PROTECTED_FEATURES

DEFAULT_FAIRNESS_REPORT_PATH: Final[Path] = MODEL_REPORTS_DIR / "fairness_report.json"
APPROVAL_SCORE_THRESHOLD: Final[int] = 550
MIN_GROUP_SAMPLES: Final[int] = 30
YELLOW_AUC_GAP_THRESHOLD: Final[float] = 0.08
RED_AUC_GAP_THRESHOLD: Final[float] = 0.075
CALIBRATION_PARITY_BIN_COUNT: Final[int] = CALIBRATION_BIN_COUNT
INDIVIDUAL_FAIRNESS_SIMILARITY_THRESHOLD: Final[float] = 0.90
INDIVIDUAL_FAIRNESS_SCORE_GAP_THRESHOLD: Final[int] = 50
INDIVIDUAL_FAIRNESS_MAX_ROWS: Final[int] = 2_000
INDIVIDUAL_FAIRNESS_WORST_PAIR_COUNT: Final[int] = 10
PSYCHOMETRIC_SIMILARITY_FEATURES: Final[tuple[str, ...]] = (
    "numeracy_score",
    "CRT_score",
    "financial_literacy_score",
    "future_orientation",
    "delay_discounting_rate",
    "risk_attitude",
    "risk_consistency_flag",
    "loss_aversion_score",
    "locus_of_control",
    "conscientiousness_score",
    "social_capital_score",
    "honesty_score",
    "resilience_score",
    "reciprocity_norm",
)


def build_fairness_report(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    protected_frame: pd.DataFrame,
    *,
    feature_frame: pd.DataFrame | None = None,
    approval_score_threshold: int = APPROVAL_SCORE_THRESHOLD,
    min_group_samples: int = MIN_GROUP_SAMPLES,
    calibration_bins: int = CALIBRATION_PARITY_BIN_COUNT,
    similarity_threshold: float = INDIVIDUAL_FAIRNESS_SIMILARITY_THRESHOLD,
    score_gap_threshold: int = INDIVIDUAL_FAIRNESS_SCORE_GAP_THRESHOLD,
) -> dict[str, Any]:
    """Build the documented subgroup fairness payload for one held-out split."""

    y_true_array = np.asarray(y_true, dtype=int)
    y_prob_array = np.asarray(y_prob, dtype=float)
    if len(y_true_array) != len(y_prob_array):
        raise ValueError("y_true and y_prob must contain the same number of rows.")
    if len(protected_frame) != len(y_true_array):
        raise ValueError(
            "protected_frame row count must match the supplied targets and probabilities."
        )
    if ((y_prob_array < 0.0) | (y_prob_array > 1.0)).any():
        raise ValueError("Fairness report probabilities must stay within the [0, 1] range.")

    overall_auc = _safe_roc_auc_score(y_true_array, y_prob_array)
    scores = np.asarray(
        [probability_to_score(probability) for probability in y_prob_array],
        dtype=int,
    )
    approved = scores >= int(approval_score_threshold)

    report = {
        "overall_auc": round(overall_auc, 4),
        "overall_approval_rate": round(float(approved.mean()), 4),
        "overall_default_rate": round(float(1.0 - y_true_array.mean()), 4),
        "worst_auc_gap": 0.0,
        "flagged_groups": [],
        "verdict": "",
        "groups": {},
        "calibration_parity": build_calibration_parity_report(
            y_true_array,
            y_prob_array,
            protected_frame,
            min_group_samples=min_group_samples,
            n_bins=calibration_bins,
        ),
        "individual_fairness_proxy": build_individual_fairness_proxy(
            scores,
            protected_frame,
            feature_frame=feature_frame,
            similarity_threshold=similarity_threshold,
            score_gap_threshold=score_gap_threshold,
        ),
    }

    worst_auc_gap = 0.0
    flagged_groups: list[str] = []
    evaluated_group_count = 0
    skipped_group_count = 0

    for attribute_name in PROTECTED_FEATURES:
        if attribute_name not in protected_frame.columns:
            raise ValueError(
                f"Protected fairness column '{attribute_name}' is missing from the dataset."
            )

        attribute_values = protected_frame[attribute_name].fillna("__MISSING__").astype(str)
        attribute_payload: dict[str, Any] = {}

        for group_value in sorted(attribute_values.unique().tolist()):
            mask = (attribute_values == group_value).to_numpy(dtype=bool)
            n_samples = int(mask.sum())
            if n_samples < min_group_samples:
                skipped_group_count += 1
                continue

            subgroup_true = y_true_array[mask]
            if len(np.unique(subgroup_true)) < 2:
                skipped_group_count += 1
                continue

            evaluated_group_count += 1
            subgroup_prob = y_prob_array[mask]
            subgroup_scores = scores[mask]
            subgroup_approved = approved[mask]

            auc = _safe_roc_auc_score(subgroup_true, subgroup_prob)
            auc_gap = abs(auc - overall_auc)
            worst_auc_gap = max(worst_auc_gap, auc_gap)
            flag = _determine_group_flag(auc_gap)
            if flag != "green":
                flagged_groups.append(f"{attribute_name}={group_value}")

            attribute_payload[group_value] = {
                "n_samples": n_samples,
                "auc": round(auc, 4),
                "auc_gap_from_overall": round(auc_gap, 4),
                "approval_rate": round(float(subgroup_approved.mean()), 4),
                "fpr": round(_false_positive_rate(subgroup_true, subgroup_approved), 4),
                "fnr": round(_false_negative_rate(subgroup_true, subgroup_approved), 4),
                "mean_score": round(float(subgroup_scores.mean()), 1),
                "flag": flag,
            }

        report["groups"][attribute_name] = attribute_payload

    report["worst_auc_gap"] = round(worst_auc_gap, 4)
    report["flagged_groups"] = flagged_groups
    report["verdict"] = _build_verdict(
        flagged_groups,
        evaluated_group_count=evaluated_group_count,
        skipped_group_count=skipped_group_count,
    )
    return report


def build_fairness_report_for_candidate_probabilities(
    y_true: np.ndarray | list[int],
    protected_frame: pd.DataFrame,
    candidate_probabilities: dict[str, np.ndarray],
    *,
    model_stats: list[dict[str, Any]],
    feature_frame: pd.DataFrame | None = None,
    approval_score_threshold: int = APPROVAL_SCORE_THRESHOLD,
    min_group_samples: int = MIN_GROUP_SAMPLES,
) -> tuple[dict[str, Any], str]:
    """Select the current best candidate model and build its fairness report."""

    if not candidate_probabilities:
        raise ValueError("At least one candidate probability series is required.")

    selected_model_name = select_best_test_auc_model(
        model_stats,
        candidate_model_names=set(candidate_probabilities),
    )
    if selected_model_name is None or selected_model_name not in candidate_probabilities:
        selected_model_name = sorted(candidate_probabilities)[0]

    return (
        build_fairness_report(
            y_true,
            candidate_probabilities[selected_model_name],
            protected_frame,
            feature_frame=feature_frame,
            approval_score_threshold=approval_score_threshold,
            min_group_samples=min_group_samples,
        ),
        selected_model_name,
    )


def build_calibration_parity_report(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    protected_frame: pd.DataFrame,
    *,
    min_group_samples: int = MIN_GROUP_SAMPLES,
    n_bins: int = CALIBRATION_PARITY_BIN_COUNT,
) -> dict[str, Any]:
    """Build per-protected-group calibration curves and ECE gaps."""

    y_true_array = np.asarray(y_true, dtype=int)
    y_prob_array = np.asarray(y_prob, dtype=float)
    _validate_fairness_inputs(y_true_array, y_prob_array, protected_frame)

    overall_ece = expected_calibration_error(y_true_array, y_prob_array, n_bins=n_bins)
    groups: dict[str, dict[str, Any]] = {}
    max_ece_gap = 0.0
    evaluated_group_count = 0
    skipped_group_count = 0

    for attribute_name in PROTECTED_FEATURES:
        attribute_values = protected_frame[attribute_name].fillna("__MISSING__").astype(str)
        attribute_payload: dict[str, Any] = {}

        for group_value in sorted(attribute_values.unique().tolist()):
            mask = (attribute_values == group_value).to_numpy(dtype=bool)
            n_samples = int(mask.sum())
            if n_samples < min_group_samples or len(np.unique(y_true_array[mask])) < 2:
                skipped_group_count += 1
                continue

            subgroup_true = y_true_array[mask]
            subgroup_prob = y_prob_array[mask]
            group_ece = expected_calibration_error(
                subgroup_true,
                subgroup_prob,
                n_bins=n_bins,
            )
            ece_gap = abs(group_ece - overall_ece)
            max_ece_gap = max(max_ece_gap, ece_gap)
            evaluated_group_count += 1

            attribute_payload[group_value] = {
                "n_samples": n_samples,
                "expected_calibration_error": round(group_ece, 4),
                "ece_gap_from_overall": round(ece_gap, 4),
                "mean_predicted_probability": round(float(subgroup_prob.mean()), 4),
                "observed_repayment_rate": round(float(subgroup_true.mean()), 4),
                "points": compute_calibration_points(
                    subgroup_true,
                    subgroup_prob,
                    n_bins=n_bins,
                ),
            }

        groups[attribute_name] = attribute_payload

    return {
        "n_bins": int(n_bins),
        "overall_expected_calibration_error": round(overall_ece, 4),
        "max_ece_gap": round(max_ece_gap, 4),
        "evaluated_group_count": evaluated_group_count,
        "skipped_group_count": skipped_group_count,
        "groups": groups,
    }


def build_individual_fairness_proxy(
    scores: np.ndarray | list[int],
    protected_frame: pd.DataFrame,
    *,
    feature_frame: pd.DataFrame | None,
    similarity_threshold: float = INDIVIDUAL_FAIRNESS_SIMILARITY_THRESHOLD,
    score_gap_threshold: int = INDIVIDUAL_FAIRNESS_SCORE_GAP_THRESHOLD,
    max_rows: int = INDIVIDUAL_FAIRNESS_MAX_ROWS,
    worst_pair_count: int = INDIVIDUAL_FAIRNESS_WORST_PAIR_COUNT,
) -> dict[str, Any]:
    """Compare scores for demographically different, psychometrically similar pairs."""

    score_array = np.asarray(scores, dtype=int)
    if len(protected_frame) != len(score_array):
        raise ValueError("protected_frame row count must match the supplied scores.")

    base_payload = {
        "similarity_feature_set": list(PSYCHOMETRIC_SIMILARITY_FEATURES),
        "similarity_threshold": round(float(similarity_threshold), 4),
        "score_gap_threshold": int(score_gap_threshold),
        "evaluated_applicants": 0,
        "evaluated_pairs": 0,
        "flagged_pair_count": 0,
        "flagged_pair_share": 0.0,
        "max_score_gap": 0,
        "mean_score_gap": 0.0,
        "p95_score_gap": 0.0,
        "worst_pairs": [],
        "verdict": "",
    }
    if feature_frame is None:
        return {
            **base_payload,
            "verdict": (
                "Individual fairness proxy was not computed because the offline "
                "psychometric feature frame was not supplied."
            ),
        }

    _validate_similarity_feature_frame(feature_frame, expected_rows=len(score_array))
    for attribute_name in PROTECTED_FEATURES:
        if attribute_name not in protected_frame.columns:
            raise ValueError(
                f"Protected fairness column '{attribute_name}' is missing from the dataset."
            )

    sampled_positions = _sample_positions(len(score_array), max_rows=max_rows)
    if sampled_positions.size < 2:
        return {
            **base_payload,
            "evaluated_applicants": int(sampled_positions.size),
            "verdict": "Individual fairness proxy is inconclusive because fewer than two applicants were available.",
        }

    feature_values = feature_frame.iloc[sampled_positions].loc[
        :,
        list(PSYCHOMETRIC_SIMILARITY_FEATURES),
    ]
    feature_matrix = np.nan_to_num(feature_values.to_numpy(dtype=float), nan=0.0)
    row_norms = np.linalg.norm(feature_matrix, axis=1)
    nonzero_mask = row_norms > 0.0
    if int(nonzero_mask.sum()) < 2:
        return {
            **base_payload,
            "evaluated_applicants": int(nonzero_mask.sum()),
            "verdict": "Individual fairness proxy is inconclusive because psychometric vectors were empty.",
        }

    feature_matrix = feature_matrix[nonzero_mask]
    normalized_features = feature_matrix / row_norms[nonzero_mask, None]
    score_subset = score_array[sampled_positions][nonzero_mask]
    protected_subset = protected_frame.iloc[sampled_positions].reset_index(drop=True)
    protected_subset = protected_subset.loc[nonzero_mask, PROTECTED_FEATURES].reset_index(
        drop=True
    )

    similarities = normalized_features @ normalized_features.T
    upper_triangle = np.triu(np.ones_like(similarities, dtype=bool), k=1)
    similar_pairs = (similarities >= float(similarity_threshold)) & upper_triangle
    demographic_difference = _build_demographic_difference_matrix(protected_subset)
    candidate_pairs = similar_pairs & demographic_difference
    evaluated_pairs = int(candidate_pairs.sum())
    evaluated_applicants = int(len(score_subset))

    if evaluated_pairs == 0:
        return {
            **base_payload,
            "evaluated_applicants": evaluated_applicants,
            "verdict": (
                "Individual fairness proxy found no demographically different pairs "
                "above the psychometric similarity threshold."
            ),
        }

    score_gaps = np.abs(score_subset[:, None] - score_subset[None, :]).astype(int)
    candidate_score_gaps = score_gaps[candidate_pairs]
    flagged_pairs = candidate_pairs & (score_gaps > int(score_gap_threshold))
    flagged_pair_count = int(flagged_pairs.sum())

    return {
        **base_payload,
        "evaluated_applicants": evaluated_applicants,
        "evaluated_pairs": evaluated_pairs,
        "flagged_pair_count": flagged_pair_count,
        "flagged_pair_share": round(float(flagged_pair_count / evaluated_pairs), 4),
        "max_score_gap": int(candidate_score_gaps.max()),
        "mean_score_gap": round(float(candidate_score_gaps.mean()), 2),
        "p95_score_gap": round(float(np.percentile(candidate_score_gaps, 95)), 2),
        "worst_pairs": _build_worst_individual_fairness_pairs(
            score_subset,
            protected_subset,
            similarities,
            score_gaps,
            candidate_pairs,
            worst_pair_count=worst_pair_count,
        ),
        "verdict": _build_individual_fairness_verdict(
            flagged_pair_count,
            evaluated_pairs=evaluated_pairs,
            score_gap_threshold=score_gap_threshold,
        ),
    }


def save_fairness_report(
    report: dict[str, Any],
    path: str | Path,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def _determine_group_flag(auc_gap: float) -> str:
    if auc_gap > RED_AUC_GAP_THRESHOLD:
        return "red"
    if auc_gap > YELLOW_AUC_GAP_THRESHOLD:
        return "yellow"
    return "green"


def _build_verdict(
    flagged_groups: list[str],
    *,
    evaluated_group_count: int,
    skipped_group_count: int,
) -> str:
    if evaluated_group_count == 0:
        return (
            "Fairness audit is inconclusive because no subgroup met the minimum "
            "sample and class-coverage requirements."
        )
    if not flagged_groups:
        if skipped_group_count:
            return (
                "Model shows acceptable fairness across evaluated demographic groups, "
                "but some subgroups were skipped due to limited support."
            )
        return (
            "Model shows acceptable fairness across all tested demographic groups. "
            "No subgroup shows AUC deviation >4% from the overall model."
        )
    verdict = (
        "Model requires attention for: "
        f"{', '.join(flagged_groups)}. "
        "These groups show AUC deviation beyond threshold. "
        "Recommend targeted feature collection or separate calibration."
    )
    if skipped_group_count:
        verdict += " Some additional subgroups were skipped due to limited support."
    return verdict


def _safe_roc_auc_score(
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> float:
    if len(np.unique(y_true)) < 2 or len(np.unique(y_prob)) < 2:
        return 0.5
    return float(roc_auc_score(y_true, y_prob))


def _false_positive_rate(
    y_true: np.ndarray,
    approved: np.ndarray,
) -> float:
    negatives = y_true == 0
    negative_total = int(negatives.sum())
    if negative_total == 0:
        return 0.0
    return float(np.sum(approved & negatives) / negative_total)


def _false_negative_rate(
    y_true: np.ndarray,
    approved: np.ndarray,
) -> float:
    positives = y_true == 1
    positive_total = int(positives.sum())
    if positive_total == 0:
        return 0.0
    return float(np.sum((~approved) & positives) / positive_total)


def _validate_fairness_inputs(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    protected_frame: pd.DataFrame,
) -> None:
    if len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must contain the same number of rows.")
    if len(protected_frame) != len(y_true):
        raise ValueError(
            "protected_frame row count must match the supplied targets and probabilities."
        )
    if ((y_prob < 0.0) | (y_prob > 1.0)).any():
        raise ValueError("Fairness report probabilities must stay within the [0, 1] range.")
    for attribute_name in PROTECTED_FEATURES:
        if attribute_name not in protected_frame.columns:
            raise ValueError(
                f"Protected fairness column '{attribute_name}' is missing from the dataset."
            )


def _validate_similarity_feature_frame(
    feature_frame: pd.DataFrame,
    *,
    expected_rows: int,
) -> None:
    if len(feature_frame) != expected_rows:
        raise ValueError(
            "feature_frame row count must match the supplied scores for individual fairness."
        )
    protected_overlap = sorted(set(feature_frame.columns) & set(PROTECTED_FEATURES))
    if protected_overlap:
        raise ValueError(
            "Individual fairness similarity features must not include protected "
            f"attributes: {protected_overlap}."
        )
    missing_features = [
        feature_name
        for feature_name in PSYCHOMETRIC_SIMILARITY_FEATURES
        if feature_name not in feature_frame.columns
    ]
    if missing_features:
        raise ValueError(
            "feature_frame is missing psychometric similarity features: "
            f"{missing_features}."
        )


def _sample_positions(row_count: int, *, max_rows: int) -> np.ndarray:
    if row_count <= max_rows:
        return np.arange(row_count, dtype=int)
    return np.linspace(0, row_count - 1, max_rows, dtype=int)


def _build_demographic_difference_matrix(protected_frame: pd.DataFrame) -> np.ndarray:
    protected_values = protected_frame.loc[:, PROTECTED_FEATURES].fillna("__MISSING__")
    protected_array = protected_values.astype(str).to_numpy()
    row_count = protected_array.shape[0]
    demographic_difference = np.zeros((row_count, row_count), dtype=bool)
    for column_index in range(protected_array.shape[1]):
        demographic_difference |= (
            protected_array[:, column_index, None]
            != protected_array[None, :, column_index]
        )
    return demographic_difference


def _build_worst_individual_fairness_pairs(
    scores: np.ndarray,
    protected_frame: pd.DataFrame,
    similarities: np.ndarray,
    score_gaps: np.ndarray,
    candidate_pairs: np.ndarray,
    *,
    worst_pair_count: int,
) -> list[dict[str, Any]]:
    pair_positions = np.argwhere(candidate_pairs)
    if pair_positions.size == 0:
        return []

    ordered_indices = np.argsort(
        -score_gaps[pair_positions[:, 0], pair_positions[:, 1]]
    )[:worst_pair_count]
    worst_pairs: list[dict[str, Any]] = []
    for pair_position in pair_positions[ordered_indices]:
        row_a = int(pair_position[0])
        row_b = int(pair_position[1])
        differing_attributes = [
            attribute_name
            for attribute_name in PROTECTED_FEATURES
            if str(protected_frame.iloc[row_a][attribute_name])
            != str(protected_frame.iloc[row_b][attribute_name])
        ]
        worst_pairs.append(
            {
                "row_position_a": row_a,
                "row_position_b": row_b,
                "score_a": int(scores[row_a]),
                "score_b": int(scores[row_b]),
                "score_gap": int(score_gaps[row_a, row_b]),
                "cosine_similarity": round(float(similarities[row_a, row_b]), 4),
                "differing_attributes": differing_attributes,
            }
        )
    return worst_pairs


def _build_individual_fairness_verdict(
    flagged_pair_count: int,
    *,
    evaluated_pairs: int,
    score_gap_threshold: int,
) -> str:
    if flagged_pair_count == 0:
        return (
            "Individual fairness proxy found no demographically different, "
            "psychometrically similar pairs with score gaps above the configured threshold."
        )
    return (
        "Individual fairness proxy found "
        f"{flagged_pair_count} of {evaluated_pairs} demographically different, "
        "psychometrically similar pairs with score gaps above "
        f"{score_gap_threshold} points. Review feature collection and calibration before promotion."
    )


__all__ = [
    "APPROVAL_SCORE_THRESHOLD",
    "DEFAULT_FAIRNESS_REPORT_PATH",
    "MIN_GROUP_SAMPLES",
    "CALIBRATION_PARITY_BIN_COUNT",
    "INDIVIDUAL_FAIRNESS_SCORE_GAP_THRESHOLD",
    "INDIVIDUAL_FAIRNESS_SIMILARITY_THRESHOLD",
    "PSYCHOMETRIC_SIMILARITY_FEATURES",
    "RED_AUC_GAP_THRESHOLD",
    "YELLOW_AUC_GAP_THRESHOLD",
    "build_calibration_parity_report",
    "build_fairness_report",
    "build_fairness_report_for_candidate_probabilities",
    "build_individual_fairness_proxy",
    "save_fairness_report",
]
