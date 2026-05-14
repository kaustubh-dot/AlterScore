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
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from backend.ml.inference.score_mapper import probability_to_score

CURVE_POINT_COUNT = 100
CALIBRATION_BIN_COUNT = 10
SCORE_RANGE_MIN = 300
SCORE_RANGE_MAX = 850
SCORE_HISTOGRAM_BUCKET_WIDTH = 50


def compute_binary_classification_metrics(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    *,
    model_name: str,
    model_type: str,
    split: str,
    threshold: float | None = None,
) -> dict[str, Any]:
    """Compute the core ranking and calibration metrics for a binary classifier."""

    y_true_array = np.asarray(y_true, dtype=int)
    y_prob_array = np.asarray(y_prob, dtype=float)
    resolved_threshold = _resolve_threshold(
        y_true_array,
        y_prob_array,
        threshold=threshold,
    )
    y_pred_array = (y_prob_array >= resolved_threshold).astype(int)

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
        "threshold": round(resolved_threshold, 4),
        "split": split,
    }


def build_split_evaluation_details(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    *,
    model_name: str,
    model_type: str,
    split: str,
    curve_point_count: int = CURVE_POINT_COUNT,
    calibration_bins: int = CALIBRATION_BIN_COUNT,
    threshold: float | None = None,
) -> dict[str, Any]:
    """Build curve and confusion payloads for one model on one split."""

    y_true_array = np.asarray(y_true, dtype=int)
    y_prob_array = np.asarray(y_prob, dtype=float)
    resolved_threshold = _resolve_threshold(
        y_true_array,
        y_prob_array,
        threshold=threshold,
    )

    return {
        "model_name": model_name,
        "model_type": model_type,
        "split": split,
        "roc_curve": compute_roc_points(
            y_true_array,
            y_prob_array,
            point_count=curve_point_count,
        ),
        "pr_curve": compute_pr_points(
            y_true_array,
            y_prob_array,
            point_count=curve_point_count,
        ),
        "calibration_curve": compute_calibration_points(
            y_true_array,
            y_prob_array,
            n_bins=calibration_bins,
        ),
        "confusion_matrix": compute_confusion_matrix(
            y_true_array,
            y_prob_array,
            threshold=resolved_threshold,
        ),
    }


def compute_roc_points(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    *,
    point_count: int = CURVE_POINT_COUNT,
) -> list[dict[str, float]]:
    """Return deterministic ROC curve points suitable for saved reports."""

    y_true_array = np.asarray(y_true, dtype=int)
    y_prob_array = np.asarray(y_prob, dtype=float)

    if len(np.unique(y_true_array)) < 2 or len(np.unique(y_prob_array)) < 2:
        return [
            {"fpr": 0.0, "tpr": 0.0},
            {"fpr": 1.0, "tpr": 1.0},
        ]

    fpr, tpr, _ = roc_curve(y_true_array, y_prob_array)
    sampled_indices = _sample_curve_indices(len(fpr), point_count)
    return [
        {
            "fpr": round(float(fpr[index]), 4),
            "tpr": round(float(tpr[index]), 4),
        }
        for index in sampled_indices
    ]


def compute_pr_points(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    *,
    point_count: int = CURVE_POINT_COUNT,
) -> list[dict[str, float]]:
    """Return deterministic precision-recall curve points for saved reports."""

    y_true_array = np.asarray(y_true, dtype=int)
    y_prob_array = np.asarray(y_prob, dtype=float)
    if y_true_array.size == 0:
        return []

    if len(np.unique(y_true_array)) < 2:
        base_precision = round(float(y_true_array.mean()), 4)
        return [
            {"recall": 0.0, "precision": base_precision},
            {"recall": 1.0, "precision": base_precision},
        ]

    precision, recall, _ = precision_recall_curve(y_true_array, y_prob_array)
    sampled_indices = _sample_curve_indices(len(precision), point_count)
    return [
        {
            "recall": round(float(recall[index]), 4),
            "precision": round(float(precision[index]), 4),
        }
        for index in sampled_indices
    ]


def compute_calibration_points(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    *,
    n_bins: int = CALIBRATION_BIN_COUNT,
) -> list[dict[str, float | int]]:
    """Return occupied equal-width calibration bins."""

    y_true_array = np.asarray(y_true, dtype=int)
    y_prob_array = np.asarray(y_prob, dtype=float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.digitize(y_prob_array, bins[1:-1], right=True)
    points: list[dict[str, float | int]] = []

    for bin_id in range(n_bins):
        mask = bin_ids == bin_id
        if not np.any(mask):
            continue
        points.append(
            {
                "mean_predicted": round(float(y_prob_array[mask].mean()), 4),
                "fraction_positive": round(float(y_true_array[mask].mean()), 4),
                "count": int(mask.sum()),
            }
        )

    return points


def compute_confusion_matrix(
    y_true: np.ndarray | list[int],
    y_prob: np.ndarray | list[float],
    *,
    threshold: float | None = None,
) -> dict[str, float | int]:
    """Return thresholded confusion counts and derived rates."""

    y_true_array = np.asarray(y_true, dtype=int)
    y_prob_array = np.asarray(y_prob, dtype=float)
    resolved_threshold = _resolve_threshold(
        y_true_array,
        y_prob_array,
        threshold=threshold,
    )
    y_pred_array = (y_prob_array >= resolved_threshold).astype(int)

    true_positive = int(np.sum((y_true_array == 1) & (y_pred_array == 1)))
    false_positive = int(np.sum((y_true_array == 0) & (y_pred_array == 1)))
    false_negative = int(np.sum((y_true_array == 1) & (y_pred_array == 0)))
    true_negative = int(np.sum((y_true_array == 0) & (y_pred_array == 0)))

    positive_total = true_positive + false_negative
    negative_total = false_positive + true_negative

    return {
        "threshold": round(resolved_threshold, 4),
        "tp": true_positive,
        "fp": false_positive,
        "fn": false_negative,
        "tn": true_negative,
        "tpr": round(
            float(true_positive / positive_total) if positive_total else 0.0,
            4,
        ),
        "fpr": round(
            float(false_positive / negative_total) if negative_total else 0.0,
            4,
        ),
        "fnr": round(
            float(false_negative / positive_total) if positive_total else 0.0,
            4,
        ),
    }


def build_population_percentiles_payload(
    y_prob: np.ndarray | list[float],
    *,
    model_name: str,
    bucket_width: int = SCORE_HISTOGRAM_BUCKET_WIDTH,
) -> dict[str, Any]:
    """Build percentile lookup and histogram payloads from scored population probabilities."""

    probability_array = np.asarray(y_prob, dtype=float)
    scores = np.asarray(
        [probability_to_score(probability) for probability in probability_array],
        dtype=int,
    )
    if scores.size == 0:
        raise ValueError("Population percentile payload requires at least one scored row.")

    score_grid = np.arange(SCORE_RANGE_MIN, SCORE_RANGE_MAX + 1, dtype=int)
    sorted_scores = np.sort(scores)
    percentile_counts = np.searchsorted(sorted_scores, score_grid, side="right")
    percentiles = np.rint((percentile_counts / float(scores.size)) * 100.0).astype(int)
    histogram = _build_score_histogram(scores, bucket_width=bucket_width)

    return {
        "model_name": model_name,
        "row_count": int(scores.size),
        "summary": {
            "min_score": int(scores.min()),
            "max_score": int(scores.max()),
            "mean_score": round(float(scores.mean()), 2),
            "median_score": round(float(np.median(scores)), 2),
        },
        "score_histogram": histogram,
        "scores": score_grid.astype(int).tolist(),
        "percentiles": percentiles.astype(int).tolist(),
        "score_to_percentile": {
            str(score): int(percentile)
            for score, percentile in zip(score_grid.tolist(), percentiles.tolist(), strict=True)
        },
    }


def build_population_percentiles_report(
    model_payloads: dict[str, dict[str, Any]],
    *,
    default_model_name: str,
) -> dict[str, Any]:
    """Wrap one or more model-specific percentile tables into one saved artifact."""

    if default_model_name not in model_payloads:
        raise ValueError(
            "default_model_name must exist in the provided population percentile payloads."
        )

    default_payload = dict(model_payloads[default_model_name])
    return {
        "default_model_name": default_model_name,
        "available_models": sorted(model_payloads),
        "models": {model_name: dict(payload) for model_name, payload in model_payloads.items()},
        **default_payload,
    }


def merge_population_percentiles_reports(
    existing_payload: dict[str, Any] | None,
    updated_model_payloads: dict[str, dict[str, Any]],
    *,
    default_model_name: str,
) -> dict[str, Any]:
    """Merge updated model percentile payloads into an existing saved report."""

    merged_model_payloads: dict[str, dict[str, Any]] = {}
    if isinstance(existing_payload, dict):
        existing_models = existing_payload.get("models")
        if isinstance(existing_models, dict):
            for model_name, payload in existing_models.items():
                if isinstance(model_name, str) and isinstance(payload, dict):
                    merged_model_payloads[model_name] = dict(payload)

    for model_name, payload in updated_model_payloads.items():
        merged_model_payloads[model_name] = dict(payload)

    return build_population_percentiles_report(
        merged_model_payloads,
        default_model_name=default_model_name,
    )


def merge_evaluation_details(
    existing_details: dict[str, Any] | None,
    updated_details: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Merge split/model evaluation payloads without dropping older entries."""

    merged_details: dict[str, dict[str, Any]] = {}

    if isinstance(existing_details, dict):
        for split_name, split_payload in existing_details.items():
            if not isinstance(split_name, str) or not isinstance(split_payload, dict):
                continue
            merged_details[split_name] = {
                model_name: dict(model_payload)
                for model_name, model_payload in split_payload.items()
                if isinstance(model_name, str) and isinstance(model_payload, dict)
            }

    for split_name, split_payload in updated_details.items():
        existing_split_payload = merged_details.setdefault(split_name, {})
        for model_name, model_payload in split_payload.items():
            existing_split_payload[model_name] = dict(model_payload)

    return merged_details


def select_best_test_auc_model(
    model_stats: list[dict[str, Any]],
    candidate_model_names: set[str] | None = None,
) -> str | None:
    """Select the highest-AUC test-split model from saved metric rows."""

    best_model_name: str | None = None
    best_auc = float("-inf")

    for item in model_stats:
        if item.get("split") != "test_months_11_12":
            continue
        model_name = item.get("model_name")
        if not isinstance(model_name, str):
            continue
        if candidate_model_names is not None and model_name not in candidate_model_names:
            continue
        try:
            auc_roc = float(item["auc_roc"])
        except (KeyError, TypeError, ValueError):
            continue
        if auc_roc > best_auc:
            best_auc = auc_roc
            best_model_name = model_name

    return best_model_name


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


def _resolve_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    *,
    threshold: float | None,
) -> float:
    if threshold is None:
        return optimal_threshold(y_true, y_prob)
    return float(threshold)


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


def _sample_curve_indices(point_total: int, max_points: int) -> np.ndarray:
    if point_total <= max_points:
        return np.arange(point_total, dtype=int)

    sampled = np.linspace(0, point_total - 1, max_points, dtype=int)
    return np.unique(sampled)


def _build_score_histogram(
    scores: np.ndarray,
    *,
    bucket_width: int,
) -> list[dict[str, float | int | str]]:
    buckets: list[dict[str, float | int | str]] = []
    row_count = float(len(scores))
    for bucket_min in range(SCORE_RANGE_MIN, SCORE_RANGE_MAX + 1, bucket_width):
        bucket_max = min(bucket_min + bucket_width - 1, SCORE_RANGE_MAX)
        if bucket_max >= SCORE_RANGE_MAX:
            mask = (scores >= bucket_min) & (scores <= bucket_max)
        else:
            mask = (scores >= bucket_min) & (scores <= bucket_max)
        count = int(mask.sum())
        buckets.append(
            {
                "label": f"{bucket_min}-{bucket_max}",
                "score_min": bucket_min,
                "score_max": bucket_max,
                "count": count,
                "share": round(float(count / row_count), 6),
            }
        )
    return buckets


__all__ = [
    "CALIBRATION_BIN_COUNT",
    "CURVE_POINT_COUNT",
    "SCORE_HISTOGRAM_BUCKET_WIDTH",
    "build_population_percentiles_report",
    "build_population_percentiles_payload",
    "build_split_evaluation_details",
    "compute_binary_classification_metrics",
    "compute_calibration_points",
    "compute_confusion_matrix",
    "compute_pr_points",
    "compute_roc_points",
    "expected_calibration_error",
    "optimal_threshold",
    "merge_evaluation_details",
    "merge_population_percentiles_reports",
    "select_best_test_auc_model",
]
