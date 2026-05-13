"""Offline fairness report generation helpers for AlterScore."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from backend.app.core.paths import MODEL_REPORTS_DIR
from backend.ml.evaluation.metrics import select_best_test_auc_model
from backend.ml.inference.score_mapper import probability_to_score
from backend.ml.preprocessing.feature_registry import PROTECTED_FEATURES

DEFAULT_FAIRNESS_REPORT_PATH: Final[Path] = MODEL_REPORTS_DIR / "fairness_report.json"
APPROVAL_SCORE_THRESHOLD: Final[int] = 550
MIN_GROUP_SAMPLES: Final[int] = 30
YELLOW_AUC_GAP_THRESHOLD: Final[float] = 0.04
RED_AUC_GAP_THRESHOLD: Final[float] = 0.07


def build_fairness_report(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    protected_frame: pd.DataFrame,
    *,
    approval_score_threshold: int = APPROVAL_SCORE_THRESHOLD,
    min_group_samples: int = MIN_GROUP_SAMPLES,
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
    }

    worst_auc_gap = 0.0
    flagged_groups: list[str] = []

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
                continue

            subgroup_true = y_true_array[mask]
            if len(np.unique(subgroup_true)) < 2:
                continue

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
    report["verdict"] = _build_verdict(flagged_groups)
    return report


def build_fairness_report_for_candidate_probabilities(
    y_true: np.ndarray | list[int],
    protected_frame: pd.DataFrame,
    candidate_probabilities: dict[str, np.ndarray],
    *,
    model_stats: list[dict[str, Any]],
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
            approval_score_threshold=approval_score_threshold,
            min_group_samples=min_group_samples,
        ),
        selected_model_name,
    )


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


def _build_verdict(flagged_groups: list[str]) -> str:
    if not flagged_groups:
        return (
            "Model shows acceptable fairness across all tested demographic groups. "
            "No subgroup shows AUC deviation >4% from the overall model."
        )
    return (
        "Model requires attention for: "
        f"{', '.join(flagged_groups)}. "
        "These groups show AUC deviation beyond threshold. "
        "Recommend targeted feature collection or separate calibration."
    )


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


__all__ = [
    "APPROVAL_SCORE_THRESHOLD",
    "DEFAULT_FAIRNESS_REPORT_PATH",
    "MIN_GROUP_SAMPLES",
    "RED_AUC_GAP_THRESHOLD",
    "YELLOW_AUC_GAP_THRESHOLD",
    "build_fairness_report",
    "build_fairness_report_for_candidate_probabilities",
    "save_fairness_report",
]
