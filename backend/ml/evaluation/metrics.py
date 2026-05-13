"""Reusable binary classification metrics for AlterScore offline evaluation."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.stats import ks_2samp
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_binary_classification_metrics(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    *,
    model_name: str,
    model_type: str,
    split: str,
) -> dict[str, Any]:
    """Compute the core ranking and calibration metrics for a binary classifier."""

    y_true_array = np.asarray(y_true, dtype=int)
    y_prob_array = np.asarray(y_prob, dtype=float)
    threshold = optimal_threshold(y_true_array, y_prob_array)
    y_pred_array = (y_prob_array >= threshold).astype(int)

    auc_roc = _safe_roc_auc_score(y_true_array, y_prob_array)
    defaulters = y_prob_array[y_true_array == 0]
    repayers = y_prob_array[y_true_array == 1]
    ks_statistic = _safe_ks_statistic(defaulters, repayers)

    return {
        "model_name": model_name,
        "model_type": model_type,
        "auc_roc": round(auc_roc, 4),
        "auc_pr": round(_safe_average_precision_score(y_true_array, y_prob_array), 4),
        "ks_statistic": round(ks_statistic, 4),
        "brier_score": round(_safe_brier_score_loss(y_true_array, y_prob_array), 4),
        "expected_calibration_error": round(
            expected_calibration_error(y_true_array, y_prob_array),
            4,
        ),
        "accuracy": round(accuracy_score(y_true_array, y_pred_array), 4),
        "precision": round(
            precision_score(y_true_array, y_pred_array, zero_division=0),
            4,
        ),
        "recall": round(recall_score(y_true_array, y_pred_array, zero_division=0), 4),
        "f1": round(f1_score(y_true_array, y_pred_array, zero_division=0), 4),
        "threshold": round(threshold, 4),
        "split": split,
    }


def expected_calibration_error(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    *,
    n_bins: int = 10,
) -> float:
    """Weighted average absolute gap between predicted and observed repay rates."""

    y_true_array = np.asarray(y_true, dtype=int)
    y_prob_array = np.asarray(y_prob, dtype=float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.digitize(y_prob_array, bins[1:-1], right=True)
    ece = 0.0

    for bin_id in range(n_bins):
        mask = bin_ids == bin_id
        if not np.any(mask):
            continue
        bin_confidence = float(y_prob_array[mask].mean())
        bin_accuracy = float(y_true_array[mask].mean())
        ece += float(mask.mean()) * abs(bin_accuracy - bin_confidence)

    return float(ece)


def optimal_threshold(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    *,
    threshold_min: float = 0.2,
    threshold_max: float = 0.8,
    threshold_count: int = 61,
) -> float:
    """Find the threshold that maximizes binary F1 on the supplied split."""

    y_true_array = np.asarray(y_true, dtype=int)
    y_prob_array = np.asarray(y_prob, dtype=float)
    if y_true_array.size == 0:
        return 0.5

    thresholds = np.linspace(threshold_min, threshold_max, threshold_count)
    f1_scores = [
        f1_score(y_true_array, y_prob_array >= threshold, zero_division=0)
        for threshold in thresholds
    ]
    return float(thresholds[int(np.argmax(f1_scores))])


def _safe_roc_auc_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2 or len(np.unique(y_prob)) < 2:
        return 0.5
    return float(roc_auc_score(y_true, y_prob))


def _safe_average_precision_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        return float(y_true.mean())
    return float(average_precision_score(y_true, y_prob))


def _safe_brier_score_loss(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    if y_true.size == 0:
        return 0.0
    return float(brier_score_loss(y_true, y_prob))


def _safe_ks_statistic(defaulters: np.ndarray, repayers: np.ndarray) -> float:
    if defaulters.size == 0 or repayers.size == 0:
        return 0.0
    ks_statistic, _ = ks_2samp(defaulters, repayers)
    return float(abs(ks_statistic))


__all__ = [
    "compute_binary_classification_metrics",
    "expected_calibration_error",
    "optimal_threshold",
]
